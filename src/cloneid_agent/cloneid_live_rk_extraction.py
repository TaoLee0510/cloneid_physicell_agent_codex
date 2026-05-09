"""Read-only CLONEID extraction for the SNU-668 r/K density-history benchmark."""

from __future__ import annotations

from datetime import datetime
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from .db import repository_root
from .rk_downsampling import FLASK_AREA_CM2


LIVE_RK_EXTRACTION_SCRIPT = "cloneid_rk_benchmark_records.R"


def live_rk_extraction_script_path() -> Path:
    return repository_root() / "scripts" / LIVE_RK_EXTRACTION_SCRIPT


def parse_cloneid_root_ids(value: str | list[str] | tuple[str, ...] | None) -> list[str]:
    """Parse one or more CLONEID event roots from CLI/config input."""

    if value is None:
        return []
    if isinstance(value, str):
        raw_items = re.split(r"[,;\s]+", value)
    else:
        raw_items = []
        for item in value:
            raw_items.extend(re.split(r"[,;\s]+", str(item)))
    return [item.strip() for item in raw_items if item.strip() and item.strip() != "auto"]


def export_live_rk_payload(
    *,
    root_ids: list[str],
    output_path: str | Path,
    max_depth: int = 80,
) -> Path:
    """Call the approved cloneid R interface and write raw extracted records."""

    if not root_ids:
        raise ValueError("At least one CLONEID root id is required for live r/K extraction")
    script = live_rk_extraction_script_path()
    if not script.exists():
        raise FileNotFoundError(f"Live r/K extraction script not found: {script}")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "Rscript",
        str(script),
        "--mode",
        "live",
        "--output",
        str(output),
        "--max-depth",
        str(max_depth),
    ]
    for root_id in root_ids:
        cmd.extend(["--root-id", root_id])
    result = subprocess.run(
        cmd,
        cwd=repository_root(),
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        stdout = result.stdout.strip()
        details = stderr or stdout or f"exit code {result.returncode}"
        raise RuntimeError(f"Live CLONEID r/K extraction failed: {details}")
    return output


def load_live_cloneid_rk_record(
    *,
    root_ids: list[str],
    output_dir: str | Path,
    max_depth: int = 80,
) -> dict[str, Any]:
    """Extract live CLONEID records and convert them to benchmark-native shape."""

    raw_path = export_live_rk_payload(
        root_ids=root_ids,
        output_path=Path(output_dir) / "live_cloneid_rk_extraction_raw.json",
        max_depth=max_depth,
    )
    payload = json.loads(raw_path.read_text())
    record = convert_live_rk_payload_to_full_record(payload, requested_root_ids=root_ids)
    record["raw_live_extraction_path"] = str(raw_path)
    return record


def convert_live_rk_payload_to_full_record(
    payload: dict[str, Any],
    *,
    requested_root_ids: list[str],
) -> dict[str, Any]:
    """Convert raw CLONEID rows into the existing benchmark full-record schema."""

    passaging_rows = payload.get("passaging", [])
    if not passaging_rows:
        raise ValueError("Live CLONEID extraction returned no Passaging rows")

    flask_by_id = _flask_by_id(payload.get("flask", []))
    root_ids = requested_root_ids or [str(item) for item in payload.get("root_ids", [])]
    branch_by_root = {root_id: _infer_branch_label(root_id) for root_id in root_ids}
    replicate_by_root = {root_id: _infer_replicate_id(root_id) for root_id in root_ids}
    parent_by_id = {
        str(_value(row, "id", "event_id")): _clean_optional(_value(row, "passaged_from_id1", "parent_event_id"))
        for row in passaging_rows
    }
    root_by_event = {
        str(_value(row, "id", "event_id")): _trace_root(str(_value(row, "id", "event_id")), parent_by_id, set(root_ids))
        for row in passaging_rows
    }
    events = []
    warnings: list[str] = []
    for row in passaging_rows:
        event_id = str(_value(row, "id", "event_id"))
        root_id = root_by_event.get(event_id) or _nearest_root_from_text(event_id, root_ids) or event_id
        branch_label = branch_by_root.get(root_id) or _infer_branch_label(event_id)
        replicate_id = replicate_by_root.get(root_id) or _infer_replicate_id(event_id)
        raw_event_type = _value(row, "event", "event_type")
        event_type = _normalize_event_type(raw_event_type, event_id)
        flask_id = _clean_optional(_value(row, "flask", "flask_id"))
        flask_area_cm2 = _flask_area_cm2(flask_by_id.get(str(flask_id)))
        area = _to_float(_value(row, "areaOccupied_um2"), default=None)
        confluence = _confluence_from_row(row, flask_area_cm2=flask_area_cm2)
        cell_count = _to_int(_value(row, "cellCount"), default=None)
        corrected_count = _to_int(_value(row, "correctedCount"), default=cell_count)
        if corrected_count is None:
            corrected_count = 0
            warnings.append(f"{event_id} has no cellCount/correctedCount; count set to 0 for schema compatibility")
        if cell_count is None:
            cell_count = corrected_count
        if area is None:
            warnings.append(f"{event_id} has no areaOccupied_um2; confluence-dependent fitting may be unavailable")
        event = {
            "event_id": event_id,
            "id": event_id,
            "parent_event_id": _clean_optional(_value(row, "passaged_from_id1", "parent_event_id")),
            "passaged_from_id1": _clean_optional(_value(row, "passaged_from_id1", "parent_event_id")),
            "passaged_from_id2": _clean_optional(_value(row, "passaged_from_id2")),
            "event_type": event_type,
            "event": event_type,
            "date_time": _normalize_datetime(_value(row, "date", "date_time")),
            "date": _normalize_datetime(_value(row, "date", "date_time")),
            "cell_line": _clean_optional(_value(row, "cellLine", "cell_line")) or "SNU-668",
            "cellLine": _clean_optional(_value(row, "cellLine", "cell_line")) or "SNU-668",
            "root_id": root_id,
            "branch_label": branch_label,
            "replicate_id": replicate_id,
            "passage_number": _to_int(_value(row, "passage", "passage_number"), default=_infer_passage(event_id)),
            "passage": _to_int(_value(row, "passage", "passage_number"), default=_infer_passage(event_id)),
            "selection_regime": _selection_regime(branch_label, row),
            "media": _clean_optional(_value(row, "media")) or "",
            "flask_id": flask_id or "",
            "flask": flask_id or "",
            "flask_area_cm2": flask_area_cm2,
            "cellCount": cell_count,
            "correctedCount": corrected_count,
            "areaOccupied_um2": area,
            "cellSize_um2": _to_float(_value(row, "cellSize_um2"), default=None),
            "confluence_proxy": confluence,
            "image_uri": _image_uri_from_qupath(event_id, payload.get("qupath", [])),
            "field_position": "",
            "magnification": "",
            "segmentation_version": "live_cloneid_record",
            "image_QC_flag": "not_reported",
            "notes": _clean_optional(_value(row, "comment")) or "Live read-only CLONEID extraction.",
        }
        events.append(event)

    events.sort(key=lambda item: (item["date_time"], item["event_id"]))
    perspective_records = [_convert_perspective(row) for row in payload.get("perspective", [])]
    identity_records = [_convert_identity(row) for row in payload.get("identity", [])]
    return {
        "source": "live_read_only_cloneid",
        "cell_line": "SNU-668",
        "root_id": ",".join(root_ids),
        "root_ids": root_ids,
        "dataset_regime": "snu668_full_history",
        "dataset_id": "snu668_r2_K3_A9_live",
        "data_status": "live_read_only_cloneid_extraction",
        "live_access_status": "live_read_only_cloneid_extraction_succeeded",
        "connection_method": payload.get("connection_method", "cloneid::connect2DB()"),
        "traversal_policy": payload.get(
            "traversal_policy",
            "descendants through Passaging.passaged_from_id1 only",
        ),
        "passaging_records": events,
        "perspective_records": perspective_records,
        "identity_records": identity_records,
        "qupath_records": payload.get("qupath", []),
        "extraction_warnings": warnings,
        "usage_rules": [
            "Transfer/passaging events are not biological growth episodes.",
            "Endpoint Perspective is validation/support only, not fitting.",
            "Identity is inferred secondary support only.",
            "Live extraction is read-only and uses SELECT queries through cloneid::connect2DB().",
        ],
    }


def _value(row: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in row:
            return row[key]
    return None


def _clean_optional(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    if text.lower() in {"na", "nan", "null", "none", ""}:
        return None
    return text


def _to_float(value: Any, default: float | None = None) -> float | None:
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int | None = None) -> int | None:
    number = _to_float(value, None)
    if number is None:
        return default
    return int(round(number))


def _normalize_datetime(value: Any) -> str:
    if value in (None, ""):
        return "1970-01-01 00:00:00"
    text = str(value).replace("T", " ").replace("Z", "")
    text = re.sub(r"\.\d+", "", text)
    for fmt, width in (("%Y-%m-%d %H:%M:%S", 19), ("%Y-%m-%d %H:%M", 16), ("%Y-%m-%d", 10)):
        try:
            return datetime.strptime(text[:width], fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return text


def _normalize_event_type(value: Any, event_id: str) -> str:
    text = f"{value or ''} {event_id}".lower()
    if "harvest" in text:
        return "harvest"
    if "seed" in text:
        return "seeding"
    if "transfer" in text or "passage" in text:
        return "transfer"
    return str(value or "unknown")


def _infer_branch_label(text: str) -> str:
    match = re.search(r"(?:^|[_-])([rRkK])\d*(?:[_-])", text)
    if match:
        value = match.group(1)
        return "K" if value.upper() == "K" else "r"
    if "_K" in text or "-K" in text:
        return "K"
    if "_r" in text or "-r" in text:
        return "r"
    return "unknown"


def _infer_replicate_id(text: str) -> str:
    match = re.search(r"(?:^|[_-])([rRkK]\d+)(?:[_-])", text)
    if match:
        return match.group(1)
    return _infer_branch_label(text)


def _infer_passage(text: str) -> int:
    match = re.search(r"(?:^|[_-])A(\d+)(?:[_-])", text)
    if match:
        return int(match.group(1))
    match = re.search(r"(?:^|[_-])P(\d+)(?:[_-])", text)
    if match:
        return int(match.group(1))
    return 0


def _trace_root(event_id: str, parent_by_id: dict[str, str | None], root_ids: set[str]) -> str | None:
    current: str | None = event_id
    seen: set[str] = set()
    while current and current not in seen:
        if current in root_ids:
            return current
        seen.add(current)
        current = parent_by_id.get(current)
    return None


def _nearest_root_from_text(event_id: str, root_ids: list[str]) -> str | None:
    branch = _infer_branch_label(event_id)
    for root_id in root_ids:
        if _infer_branch_label(root_id) == branch:
            return root_id
    return root_ids[0] if root_ids else None


def _selection_regime(branch_label: str, row: dict[str, Any]) -> str:
    growth_type = _clean_optional(_value(row, "growthType"))
    if growth_type:
        return growth_type
    if branch_label == "K":
        return "K-selection high-density transfer"
    if branch_label == "r":
        return "r-selection low-density transfer"
    return "selection regime not reported"


def _flask_by_id(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row.get("id")): row for row in rows if row.get("id") is not None}


def _flask_area_cm2(row: dict[str, Any] | None) -> float | None:
    if not row:
        return None
    for key in ("dishSurfaceArea_cm2", "surfaceArea_cm2", "flask_area_cm2"):
        value = _to_float(row.get(key), None)
        if value:
            return value
    return None


def _confluence_from_row(row: dict[str, Any], *, flask_area_cm2: float | None) -> float | None:
    existing = _to_float(row.get("confluence_proxy"), None)
    if existing is not None:
        return round(existing, 6)
    area = _to_float(row.get("areaOccupied_um2"), None)
    if area is None or flask_area_cm2 is None:
        return None
    return round(area / (flask_area_cm2 * 100_000_000.0), 6)


def _image_uri_from_qupath(event_id: str, qupath_rows: list[dict[str, Any]]) -> str:
    for row in qupath_rows:
        if str(row.get("id")) == event_id or str(row.get("passaged_from_id1")) == event_id:
            for key in ("image_uri", "imageURI", "file", "path"):
                if row.get(key):
                    return str(row[key])
            return f"cloneid-qupath://{event_id}"
    return ""


def _convert_perspective(row: dict[str, Any]) -> dict[str, Any]:
    clone_id = _clean_optional(row.get("cloneID")) or _clean_optional(row.get("Perspective_id")) or ""
    origin = _clean_optional(row.get("origin"))
    return {
        "Perspective_id": clone_id,
        "cloneID": clone_id,
        "assay_event_id": origin or "",
        "upstream_event_id": origin or "",
        "branch_label": _infer_branch_label(origin or clone_id),
        "whichPerspective": _clean_optional(row.get("whichPerspective")) or "",
        "clone_or_state_weights": {"size": _to_float(row.get("size"), 0.0)},
        "feature_matrix_pointer": _clean_optional(row.get("profile_loci")) or "",
        "raw_data_pointer": "",
        "sampleSource": _clean_optional(row.get("sampleSource")) or "",
        "rootID": _clean_optional(row.get("rootID")) or "",
        "state": _clean_optional(row.get("state")) or "",
        "alias": _clean_optional(row.get("alias")) or "",
        "QC_flag": "not_reported",
    }


def _convert_identity(row: dict[str, Any]) -> dict[str, Any]:
    payload = dict(row)
    payload.setdefault("usage", "secondary inferred support only")
    payload.setdefault("branch_label", _infer_branch_label(str(row.get("sampleSource") or row.get("cloneID") or "")))
    return payload
