"""Deterministic observable selection from a selected lineage object."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .run_io import write_json, write_markdown


def _count_non_null(records: list[dict[str, Any]], field: str) -> int:
    return sum(1 for record in records if record.get(field) is not None)


def summarize_calibration_candidates(passaging_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = [
        {
            "source": "Passaging.correctedCount",
            "target": "viable cell count",
            "supporting_rows": _count_non_null(passaging_records, "correctedCount"),
            "priority": 0,
            "evidence_class": "derived_event_linked_phenotype",
            "is_direct_observation": False,
            "derived_quantity": True,
        },
        {
            "source": "Passaging.cellCount",
            "target": "raw cell count",
            "supporting_rows": _count_non_null(passaging_records, "cellCount"),
            "priority": 1,
            "evidence_class": "derived_event_linked_phenotype",
            "is_direct_observation": False,
            "derived_quantity": True,
        },
        {
            "source": "Passaging.areaOccupied_um2",
            "target": "occupied area",
            "supporting_rows": _count_non_null(passaging_records, "areaOccupied_um2"),
            "priority": 2,
            "evidence_class": "derived_event_linked_phenotype",
            "is_direct_observation": False,
            "derived_quantity": True,
        },
        {
            "source": "Passaging.cellSize_um2",
            "target": "cell size proxy",
            "supporting_rows": _count_non_null(passaging_records, "cellSize_um2"),
            "priority": 3,
            "evidence_class": "phenotype_observed",
            "is_direct_observation": True,
            "derived_quantity": False,
        },
    ]
    candidates = [item for item in candidates if item["supporting_rows"] > 0]
    candidates.sort(key=lambda item: (-item["supporting_rows"], item["priority"], item["source"]))
    return candidates


def select_observables_from_lineage_object_payload(lineage_object_payload: dict[str, Any]) -> dict[str, Any]:
    passaging_records = lineage_object_payload.get("passaging_records", [])
    perspective_records = lineage_object_payload.get("perspective_records", [])
    identity_records = lineage_object_payload.get("identity_support_records", lineage_object_payload.get("identity_records", []))

    calibration_candidates = summarize_calibration_candidates(passaging_records)

    selected = []
    excluded = []

    if calibration_candidates:
        top = calibration_candidates[0]
        selected.append(
            {
                "source": top["source"],
                "target": top["target"],
                "evidence_class": top["evidence_class"],
                "is_direct_observation": top["is_direct_observation"],
                "derived_quantity": top["derived_quantity"],
                "allowed_uses": ["calibration", "time_series_validation"],
                "supporting_rows": top["supporting_rows"],
            }
        )
        for item in calibration_candidates[1:]:
            excluded.append(
                {
                    "source": item["source"],
                    "target": item["target"],
                    "reason": f"Lower-priority phenotype observable than {top['source']}",
                    "supporting_rows": item["supporting_rows"],
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
