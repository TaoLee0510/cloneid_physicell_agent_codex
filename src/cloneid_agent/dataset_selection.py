"""Deterministic selection over ranked candidate datasets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .run_io import write_json, write_markdown


def select_top_candidate_payload(ranked_payload: dict[str, Any]) -> dict[str, Any]:
    """Select the highest-ranked candidate and record ties for review."""
    ranked = ranked_payload.get("ranked_candidates", [])
    if not ranked:
        raise ValueError("ranked_candidates is empty")

    top = ranked[0]
    top_score = top["score"]
    tied = [item["dataset_id"] for item in ranked if item["score"] == top_score]

    return {
        "source_run_id": ranked_payload.get("source_run_id"),
        "selected_dataset_id": top["dataset_id"],
        "score": top_score,
        "score_reasons": top.get("score_reasons", []),
        "ties_at_top_score": tied,
        "selection_policy": "Highest score wins; ties are retained for user review.",
        "selected_record": top,
    }


def select_top_candidate_from_file(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    return select_top_candidate_payload(payload)


def write_selected_candidate(output_dir: str | Path, selection_payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    write_json(output_dir / "selected_candidate.json", selection_payload)
    lines = [
        "# Selected Candidate",
        "",
        f"- Selected dataset: `{selection_payload['selected_dataset_id']}`",
        f"- Score: `{selection_payload['score']}`",
        f"- Tied top candidates: `{len(selection_payload['ties_at_top_score'])}`",
        "",
        "## Reasons",
        "",
    ]
    lines.extend([f"- {reason}" for reason in selection_payload["score_reasons"]])
    if selection_payload["ties_at_top_score"]:
        lines.extend(["", "## Ties at Top Score", ""])
        lines.extend([f"- `{dataset_id}`" for dataset_id in selection_payload["ties_at_top_score"]])
    write_markdown(output_dir / "selected_candidate.md", "\n".join(lines) + "\n")
