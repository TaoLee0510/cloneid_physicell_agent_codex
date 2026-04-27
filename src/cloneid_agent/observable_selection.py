"""Deterministic observable selection from a selected TrajectoryBundle."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .run_io import write_json, write_markdown


def _count_non_null(records: list[dict[str, Any]], field: str) -> int:
    return sum(1 for record in records if record.get(field) is not None)


def select_observables_from_bundle_payload(bundle_payload: dict[str, Any]) -> dict[str, Any]:
    passaging_records = bundle_payload.get("passaging_records", [])
    perspective_records = bundle_payload.get("perspective_records", [])
    identity_records = bundle_payload.get("identity_records", [])

    calibration_candidates = [
        ("Passaging.correctedCount", "viable cell count", _count_non_null(passaging_records, "correctedCount"), 0),
        ("Passaging.areaOccupied_um2", "occupied area", _count_non_null(passaging_records, "areaOccupied_um2"), 1),
        ("Passaging.cellCount", "raw cell count", _count_non_null(passaging_records, "cellCount"), 2),
        ("Passaging.cellSize_um2", "cell size proxy", _count_non_null(passaging_records, "cellSize_um2"), 3),
    ]
    calibration_candidates = [item for item in calibration_candidates if item[2] > 0]
    calibration_candidates.sort(key=lambda item: (-item[2], item[3], item[0]))

    selected = []
    excluded = []

    if calibration_candidates:
        top_source, top_target, support, _ = calibration_candidates[0]
        selected.append(
            {
                "source": top_source,
                "target": top_target,
                "evidence_class": "phenotype_observed",
                "is_direct_observation": True,
                "allowed_uses": ["calibration", "time_series_validation"],
                "supporting_rows": support,
            }
        )
        for source, target, support, _ in calibration_candidates[1:]:
            excluded.append(
                {
                    "source": source,
                    "target": target,
                    "reason": f"Lower-priority phenotype observable than {top_source}",
                    "supporting_rows": support,
                }
            )

    if perspective_records:
        selected.append(
            {
                "source": "Perspective.size",
                "target": "endpoint state fraction",
                "evidence_class": "perspective_molecular",
                "is_direct_observation": True,
                "allowed_uses": ["validation", "endpoint_constraint"],
                "supporting_rows": len(perspective_records),
            }
        )
    if identity_records:
        excluded.append(
            {
                "source": "Identity.size/state",
                "target": "inferred endpoint state summary",
                "reason": "Identity is retained as inferred secondary support, not selected as primary observable",
                "supporting_rows": len(identity_records),
            }
        )

    return {
        "selected_bundle_id": bundle_payload.get("selected_bundle_id"),
        "selection_policy": "Prefer repeated observed phenotype for calibration and Perspective endpoint support for validation.",
        "selected": selected,
        "excluded": excluded,
    }


def select_observables_from_bundle_file(path: str | Path) -> dict[str, Any]:
    return select_observables_from_bundle_payload(json.loads(Path(path).read_text()))


def write_selected_observables(output_dir: str | Path, payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    write_json(output_dir / "selected_observables.json", payload)

    lines = [
        "# Selected Observables",
        "",
        f"- Selected bundle: `{payload.get('selected_bundle_id')}`",
        f"- Selection policy: {payload['selection_policy']}",
        "",
        "## Selected",
        "",
    ]
    for item in payload["selected"]:
        lines.append(
            f"- `{item['source']}` -> `{item['target']}` (`{', '.join(item['allowed_uses'])}`)"
        )
    if payload["excluded"]:
        lines.extend(["", "## Excluded", ""])
        for item in payload["excluded"]:
            lines.append(f"- `{item['source']}`: {item['reason']}")
    write_markdown(output_dir / "selected_observables.md", "\n".join(lines) + "\n")
