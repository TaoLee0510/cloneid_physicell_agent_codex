"""First-pass deterministic CLONEID-to-PhysiCell mapping from selected bundle artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .run_io import write_json, write_markdown


def _root_event_ids(passaging_records: list[dict[str, Any]]) -> list[str]:
    event_ids = {str(record["id"]) for record in passaging_records}
    return [
        str(record["id"])
        for record in passaging_records
        if all(
            parent_id in (None, "") or str(parent_id) not in event_ids
            for parent_id in (record.get("passaged_from_id1"),)
        )
    ]


def build_physicell_mapping(
    selected_bundle_payload: dict[str, Any],
    selected_observables_payload: dict[str, Any],
) -> dict[str, Any]:
    passaging_records = selected_bundle_payload.get("passaging_records", [])
    features = selected_bundle_payload.get("trajectory_bundle_features", {})
    root_event_ids = selected_bundle_payload.get("rooted_subtree_root_event_ids", []) or _root_event_ids(passaging_records)
    earliest = passaging_records[0] if passaging_records else {}
    latest = passaging_records[-1] if passaging_records else {}

    return {
        "selected_bundle_id": selected_bundle_payload.get("selected_bundle_id"),
        "mapping_version": "physicell_mapping_v1",
        "initialization": {
            "root_event_ids": root_event_ids,
            "initial_event_id": selected_bundle_payload.get("root_event_id") or (root_event_ids[0] if root_event_ids else earliest.get("id")),
            "initial_cell_line": earliest.get("cellLine"),
            "initial_flask": earliest.get("flask"),
            "initial_media": earliest.get("media"),
            "initial_passage": earliest.get("passage"),
        },
        "timeline": {
            "event_count": features.get("event_count", len(passaging_records)),
            "phenotype_time_span_days": features.get("phenotype_time_span_days"),
            "first_event_date": earliest.get("date"),
            "last_event_date": latest.get("date"),
        },
        "observables": selected_observables_payload.get("selected", []),
        "context_transitions": selected_bundle_payload.get("context_transitions", []),
        "endpoint_support": {
            "terminal_perspective_support": features.get("terminal_perspective_support", 0),
            "identity_support_count": features.get("identity_support_count", 0),
            "identity_role": "inferred_secondary_support_only",
        },
        "recommended_model_families": [
            "neutral_growth",
            "fixed_state_fitness",
            "density_dependent_growth",
        ],
        "warnings": [
            "This is a first-pass deterministic mapping artifact, not a final simulation configuration.",
            "Identity support is retained for interpretation only and is not mapped as direct observed phenotype.",
        ],
    }


def build_physicell_mapping_from_files(
    selected_bundle_path: str | Path,
    selected_observables_path: str | Path,
) -> dict[str, Any]:
    return build_physicell_mapping(
        json.loads(Path(selected_bundle_path).read_text()),
        json.loads(Path(selected_observables_path).read_text()),
    )


def write_physicell_mapping(output_dir: str | Path, payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    write_json(output_dir / "physicell_mapping.json", payload)

    lines = [
        "# PhysiCell Mapping",
        "",
        f"- Selected bundle: `{payload.get('selected_bundle_id')}`",
        f"- Initial event: `{payload['initialization'].get('initial_event_id')}`",
        f"- Event count: `{payload['timeline'].get('event_count')}`",
        f"- Phenotype time span days: `{payload['timeline'].get('phenotype_time_span_days')}`",
        "",
        "## Recommended Model Families",
        "",
    ]
    lines.extend(f"- `{family}`" for family in payload["recommended_model_families"])
    lines.extend(["", "## Selected Observables", ""])
    for observable in payload["observables"]:
        lines.append(
            f"- `{observable['source']}` -> `{observable['target']}` (`{', '.join(observable['allowed_uses'])}`)"
        )
    write_markdown(output_dir / "physicell_mapping.md", "\n".join(lines) + "\n")
