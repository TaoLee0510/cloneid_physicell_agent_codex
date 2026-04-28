"""Deterministic observable selection from a selected lineage object."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .run_io import write_json, write_markdown


def _count_non_null(records: list[dict[str, Any]], field: str) -> int:
    return sum(1 for record in records if record.get(field) is not None)


def select_observables_from_lineage_object_payload(lineage_object_payload: dict[str, Any]) -> dict[str, Any]:
    passaging_records = lineage_object_payload.get("passaging_records", [])
    perspective_records = lineage_object_payload.get("perspective_records", [])
    identity_records = lineage_object_payload.get("identity_support_records", lineage_object_payload.get("identity_records", []))

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
        evidence_class = "phenotype_observed"
        is_direct_observation = True
        derived_quantity = False
        if top_source == "Passaging.correctedCount":
            evidence_class = "derived_event_linked_phenotype"
            is_direct_observation = False
            derived_quantity = True
        selected.append(
            {
                "source": top_source,
                "target": top_target,
                "evidence_class": evidence_class,
                "is_direct_observation": is_direct_observation,
                "derived_quantity": derived_quantity,
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
        "selected_lineage_object_id": lineage_object_payload.get("selected_lineage_object_id", lineage_object_payload.get("selected_bundle_id")),
        "selected_lineage_object_type": lineage_object_payload.get("selected_lineage_object_type"),
        "selection_policy": "Prefer repeated observed phenotype for calibration and Perspective endpoint support for validation.",
        "selected": selected,
        "excluded": excluded,
    }


def select_observables_from_lineage_object_file(path: str | Path) -> dict[str, Any]:
    return select_observables_from_lineage_object_payload(json.loads(Path(path).read_text()))


def select_observables_from_bundle_payload(bundle_payload: dict[str, Any]) -> dict[str, Any]:
    return select_observables_from_lineage_object_payload(bundle_payload)


def select_observables_from_bundle_file(path: str | Path) -> dict[str, Any]:
    return select_observables_from_lineage_object_file(path)


def write_selected_observables(output_dir: str | Path, payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    write_json(output_dir / "selected_observables.json", payload)

    lines = [
        "# Selected Observables",
        "",
        f"- Selected lineage object: `{payload.get('selected_lineage_object_id')}`",
        f"- Type: `{payload.get('selected_lineage_object_type')}`",
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
