"""Write a concise run report from lineage-object and model-candidate artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .run_io import write_markdown


def build_run_report(
    selected_lineage_object_payload: dict[str, Any],
    selected_observables_payload: dict[str, Any],
    mapping_payload: dict[str, Any],
    generated_model_candidates_payload: dict[str, Any],
    evaluation_payload: dict[str, Any],
) -> str:
    lines = [
        "# CLONEID-PhysiCell Run Report",
        "",
        "## Selected lineage object",
        "",
        f"- Id: `{selected_lineage_object_payload.get('selected_lineage_object_id')}`",
        f"- Type: `{selected_lineage_object_payload.get('selected_lineage_object_type')}`",
        f"- Root event: `{selected_lineage_object_payload.get('root_event_id')}`",
        f"- Event count: `{selected_lineage_object_payload.get('lineage_object_features', {}).get('event_count')}`",
        f"- Graph depth: `{selected_lineage_object_payload.get('lineage_object_features', {}).get('event_graph_depth')}`",
        "",
        "## Selected observables",
        "",
    ]
    for observable in selected_observables_payload.get("selected", []):
        lines.append(
            f"- `{observable['source']}` -> `{observable['target']}` (`{', '.join(observable['allowed_uses'])}`)"
        )
    lines.extend(
        [
            "",
            "## Mapping",
            "",
            f"- Mapping version: `{mapping_payload.get('mapping_version')}`",
            f"- Recommended model families: `{', '.join(mapping_payload.get('recommended_model_families', []))}`",
            "",
            "## Generated model candidates",
            "",
        ]
    )
    for candidate in generated_model_candidates_payload.get("model_candidates", []):
        lines.append(f"- `{candidate['family']}` -> `{candidate['candidate_dir']}`")
    lines.extend(["", "## Evaluation", ""])
    for item in evaluation_payload.get("candidate_evaluations", []):
        lines.append(f"- `{item['family']}`: `{item['runtime_status']}`")
    lines.extend(
        [
            "",
            "## Caveat",
            "",
            "- This report confirms lineage-object discovery, deterministic mapping, candidate generation, and runtime readiness. It does not claim biological calibration or fit yet.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_run_report(
    output_dir: str | Path,
    *,
    selected_lineage_object_path: str | Path,
    selected_observables_path: str | Path,
    mapping_path: str | Path,
    generated_model_candidates_path: str | Path,
    evaluation_path: str | Path,
) -> None:
    report = build_run_report(
        selected_lineage_object_payload=json.loads(Path(selected_lineage_object_path).read_text()),
        selected_observables_payload=json.loads(Path(selected_observables_path).read_text()),
        mapping_payload=json.loads(Path(mapping_path).read_text()),
        generated_model_candidates_payload=json.loads(Path(generated_model_candidates_path).read_text()),
        evaluation_payload=json.loads(Path(evaluation_path).read_text()),
    )
    write_markdown(Path(output_dir) / "report.md", report)
