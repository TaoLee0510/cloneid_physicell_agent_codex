"""Event-history covariates for the CLONEID-LTE r/K benchmark."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any

from .rk_downsampling import build_mock_cloneid_full_record
from .run_io import write_json, write_markdown


def build_dry_run_snu668_fixture() -> dict[str, Any]:
    """Return the deterministic 5.5 SNU-668 fixture with explicit mock status."""

    fixture = build_mock_cloneid_full_record("auto")
    fixture["dataset_regime"] = "CLONEID_full_native_record"
    fixture["dataset_id"] = "snu668_rk_density_history_mock_fixture"
    fixture["data_status"] = "deterministic_mock_schema_fixture_not_observed_cloneid_data"
    return fixture


def _parse_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _record_id(record: dict[str, Any]) -> Any:
    return record.get("event_id") or record.get("id")


def _record_parent(record: dict[str, Any]) -> Any:
    return record.get("parent_event_id") or record.get("passaged_from_id1")


def _record_date(record: dict[str, Any]) -> Any:
    return record.get("date_time") or record.get("date")


def _record_event_type(record: dict[str, Any]) -> Any:
    return record.get("event_type") or record.get("event")


def build_history_covariates(dataset: dict[str, Any]) -> dict[str, Any]:
    """Build cumulative density/confluence history covariates from events."""

    records = sorted(
        dataset.get("passaging_records", []),
        key=lambda item: (_parse_datetime(_record_date(item)) or datetime.min, str(_record_id(item))),
    )
    by_id = {_record_id(record): record for record in records}
    max_area = max([float(record.get("areaOccupied_um2") or 0.0) for record in records] or [0.0])
    max_count = max(
        [float(record.get("correctedCount") or record.get("cellCount") or 0.0) for record in records] or [0.0]
    )
    cumulative_confluence = 0.0
    cumulative_area = 0.0
    cumulative_count = 0.0
    rows: list[dict[str, Any]] = []
    for order, record in enumerate(records):
        parent = by_id.get(_record_parent(record))
        date = _parse_datetime(_record_date(record))
        parent_date = _parse_datetime(_record_date(parent)) if parent else None
        duration_hours = None
        if date and parent_date:
            duration_hours = round((date - parent_date).total_seconds() / 3600.0, 3)

        area = float(record.get("areaOccupied_um2") or 0.0)
        count = float(record.get("correctedCount") or record.get("cellCount") or 0.0)
        confluence = record.get("confluence_proxy")
        if confluence is None and record.get("flask_area_cm2"):
            confluence = area / (float(record["flask_area_cm2"]) * 100_000_000.0)
        density_proxy = round(float(confluence), 6) if confluence is not None else None
        area_relative = round(area / max_area, 6) if max_area else None
        count_relative = round(count / max_count, 6) if max_count else None
        transfer_reset = bool(
            parent
            and _record_event_type(parent) == "harvest"
            and _record_event_type(record) == "seeding"
        )
        row = {
            "event_id": _record_id(record),
            "parent_event_id": _record_parent(record),
            "event_order_index": order,
            "timestamp": _record_date(record),
            "event_type": _record_event_type(record),
            "branch_label": record.get("branch_label"),
            "replicate_id": record.get("replicate_id"),
            "passage_index": record.get("passage_number") or record.get("passage"),
            "duration_hours_since_parent": duration_hours,
            "cell_count": record.get("cellCount"),
            "corrected_count": record.get("correctedCount"),
            "areaOccupied_um2": record.get("areaOccupied_um2"),
            "cellSize_um2": record.get("cellSize_um2"),
            "confluence_proxy": density_proxy,
            "density_proxy_relative_area": area_relative,
            "count_proxy_relative_max": count_relative,
            "cumulative_confluence_exposure_before_event": round(cumulative_confluence, 6),
            "cumulative_area_history_proxy_before_event": round(cumulative_area, 6),
            "cumulative_count_history_proxy_before_event": round(cumulative_count, 6),
            "transfer_reset_semantics": transfer_reset,
            "derived_phenotype_provenance": "event-linked Passaging/Image-derived phenotype proxy; deterministic mock values in mock mode",
        }
        rows.append(row)
        if density_proxy is not None:
            cumulative_confluence += density_proxy
        if area_relative is not None:
            cumulative_area += area_relative
        if count_relative is not None:
            cumulative_count += count_relative

    return {
        "dataset_regime": dataset.get("dataset_regime", "CLONEID_full_native_record"),
        "dataset_id": dataset.get("dataset_id", dataset.get("root_id")),
        "data_status": dataset.get("data_status", "deterministic_mock_schema_fixture_not_observed_cloneid_data"),
        "covariate_schema_version": "cloneid_lte_history_covariates_v2",
        "covariate_rows": rows,
        "summary": {
            "event_count": len(records),
            "events_with_areaOccupied_um2": sum(1 for row in rows if row["areaOccupied_um2"] not in (None, "")),
            "events_with_correctedCount": sum(1 for row in rows if row["corrected_count"] not in (None, "")),
            "events_with_confluence_proxy": sum(1 for row in rows if row["confluence_proxy"] is not None),
            "transfer_reset_count": sum(1 for row in rows if row["transfer_reset_semantics"]),
            "has_continuous_event_order_context": bool(rows),
            "has_cumulative_density_history_proxy": any(
                row["cumulative_confluence_exposure_before_event"] for row in rows
            ),
            "endpoint_perspective_count": len(dataset.get("perspective_records", [])),
            "identity_secondary_count": len(dataset.get("identity_records", [])),
        },
        "strict_provenance_notes": [
            "Transfer/passaging events are schedule resets, not biological growth episodes.",
            "Endpoint Perspective is validation/support only, not a fitting target.",
            "Identity is inferred secondary support only.",
            "Mock values are schema fixtures and cannot support manuscript numerical interpretation.",
        ],
    }


def render_history_covariates_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    return "\n".join(
        [
            "# History Covariates",
            "",
            f"- Dataset regime: `{payload.get('dataset_regime')}`",
            f"- Dataset id: `{payload.get('dataset_id')}`",
            f"- Data status: `{payload.get('data_status')}`",
            f"- Event count: `{summary['event_count']}`",
            f"- Transfer resets: `{summary['transfer_reset_count']}`",
            f"- Events with confluence proxy: `{summary['events_with_confluence_proxy']}`",
            f"- Has cumulative density history proxy: `{summary['has_cumulative_density_history_proxy']}`",
            "",
            "## Provenance Notes",
            "",
            *[f"- {item}" for item in payload["strict_provenance_notes"]],
            "",
        ]
    )


def write_history_covariates(output_dir: str | Path, payload: dict[str, Any]) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": write_json(output / "history_covariates.json", payload),
        "md": write_markdown(output / "history_covariates.md", render_history_covariates_markdown(payload)),
    }
    rows = payload.get("covariate_rows", [])
    csv_path = output / "history_covariates.csv"
    if rows:
        with csv_path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    else:
        csv_path.write_text("")
    paths["csv"] = csv_path
    return paths
