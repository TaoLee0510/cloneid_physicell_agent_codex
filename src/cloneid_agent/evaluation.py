"""First-pass deterministic evaluation of generated PhysiCell model candidates."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .run_io import write_json, write_markdown


EXPECTED_RUNTIME_FILES = (
    "initial.xml",
    "final.xml",
    "initial.svg",
    "final.svg",
)


def _latest_runtime_output(candidate_dir: Path) -> Path | None:
    candidates = sorted(
        path for path in candidate_dir.iterdir()
        if path.is_dir() and path.name.startswith("simulation_output_runtime_")
    )
    return candidates[-1] if candidates else None


def evaluate_generated_model_candidates(payload: dict[str, Any]) -> dict[str, Any]:
    evaluations: list[dict[str, Any]] = []
    for candidate in payload.get("model_candidates", []):
        candidate_dir = Path(candidate["candidate_dir"])
        config_path = Path(candidate["config_path"])
        latest_runtime = _latest_runtime_output(candidate_dir) if candidate_dir.exists() else None
        present_files = []
        missing_files = []
        if latest_runtime is not None:
            for name in EXPECTED_RUNTIME_FILES:
                if (latest_runtime / name).exists():
                    present_files.append(name)
                else:
                    missing_files.append(name)
        evaluations.append(
            {
                "candidate_id": candidate["candidate_id"],
                "family": candidate["family"],
                "config_exists": config_path.exists(),
                "latest_runtime_output": None if latest_runtime is None else str(latest_runtime),
                "runtime_run_detected": latest_runtime is not None,
                "expected_runtime_files_present": present_files,
                "expected_runtime_files_missing": missing_files,
                "runtime_status": (
                    "runtime_executed"
                    if latest_runtime is not None and not missing_files and config_path.exists()
                    else "generated_only"
                ),
            }
        )
    return {
        "selected_lineage_object_id": payload.get("selected_lineage_object_id"),
        "selected_lineage_object_type": payload.get("selected_lineage_object_type"),
        "evaluation_policy": "Runtime-readiness and runtime-output presence only; no scientific fit claim is made here.",
        "candidate_evaluations": evaluations,
    }


def evaluate_generated_model_candidates_from_file(path: str | Path) -> dict[str, Any]:
    return evaluate_generated_model_candidates(json.loads(Path(path).read_text()))


def write_evaluation(output_dir: str | Path, payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    write_json(output_dir / "evaluation.json", payload)
    lines = [
        "# Model Candidate Evaluation",
        "",
        f"- Selected lineage object: `{payload.get('selected_lineage_object_id')}`",
        f"- Type: `{payload.get('selected_lineage_object_type')}`",
        f"- Policy: {payload['evaluation_policy']}",
        "",
        "## Candidates",
        "",
    ]
    for item in payload.get("candidate_evaluations", []):
        lines.append(
            f"- `{item['family']}`: `{item['runtime_status']}`"
        )
        if item["latest_runtime_output"]:
            lines.append(f"  Latest runtime output: `{item['latest_runtime_output']}`")
    write_markdown(output_dir / "evaluation.md", "\n".join(lines) + "\n")
