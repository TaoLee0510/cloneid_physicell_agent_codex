"""Deterministic selection and bundling over ranked TrajectoryBundles."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .run_io import write_json, write_markdown


def select_top_trajectory_bundle_payload(ranked_payload: dict[str, Any]) -> dict[str, Any]:
    ranked = ranked_payload.get("ranked_trajectory_bundles", [])
    if not ranked:
        raise ValueError("ranked_trajectory_bundles is empty")

    top = ranked[0]
    top_score = top["trajectory_bundle_score"]
    tied = [item["bundle_id"] for item in ranked if item["trajectory_bundle_score"] == top_score]

    return {
        "selected_bundle_id": top["bundle_id"],
        "seed_candidate_segment_id": top.get("seed_candidate_segment_id"),
        "trajectory_bundle_score": top_score,
        "trajectory_bundle_score_reasons": top.get("trajectory_bundle_score_reasons", []),
        "ties_at_top_score": tied,
        "selection_policy": "Highest TrajectoryBundle score wins; ties are retained for user review.",
        "selected_record": top,
    }


def select_top_trajectory_bundle_from_file(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    return select_top_trajectory_bundle_payload(payload)


def build_selected_trajectory_bundle_record(selection_payload: dict[str, Any]) -> dict[str, Any]:
    selected = dict(selection_payload["selected_record"])
    return {
        "selected_bundle_id": selection_payload["selected_bundle_id"],
        "seed_candidate_segment_id": selection_payload.get("seed_candidate_segment_id"),
        "selection_summary": {
            "trajectory_bundle_score": selection_payload["trajectory_bundle_score"],
            "trajectory_bundle_score_reasons": selection_payload["trajectory_bundle_score_reasons"],
            "ties_at_top_score": selection_payload["ties_at_top_score"],
        },
        "bundle_role": selected.get("bundle_role"),
        "connected_candidate_segments": selected.get("connected_candidate_segments", []),
        "passaging_records": selected.get("passaging_records", []),
        "context_transitions": selected.get("context_transitions", []),
        "perspective_records": selected.get("perspective_records", []),
        "identity_records": selected.get("identity_records", []),
        "trajectory_bundle_features": selected.get("trajectory_bundle_features", {}),
        "attachment_policy": selected.get("attachment_policy", {}),
        "warnings": selected.get("warnings", []),
        "provenance": {
            "selected_from": "ranked_trajectory_bundles.json",
            "identity_role": "inferred_secondary_support_only",
            "perspective_role": "primary_endpoint_molecular_support",
        },
    }


def write_selected_trajectory_bundle(output_dir: str | Path, selection_payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    write_json(output_dir / "selected_trajectory_bundle.json", build_selected_trajectory_bundle_record(selection_payload))
    write_json(output_dir / "selected_trajectory_bundle_selection.json", selection_payload)

    features = selection_payload["selected_record"].get("trajectory_bundle_features", {})
    lines = [
        "# Selected Trajectory Bundle",
        "",
        f"- Selected bundle: `{selection_payload['selected_bundle_id']}`",
        f"- Seed CandidateSegment: `{selection_payload.get('seed_candidate_segment_id')}`",
        f"- Score: `{selection_payload['trajectory_bundle_score']}`",
        f"- Connected CandidateSegments: `{features.get('connected_segment_count', 0)}`",
        f"- Event count: `{features.get('event_count', 0)}`",
        f"- Terminal Perspective support: `{features.get('terminal_perspective_support', 0)}`",
        "",
        "## Reasons",
        "",
    ]
    lines.extend(f"- {reason}" for reason in selection_payload["trajectory_bundle_score_reasons"])
    if selection_payload["ties_at_top_score"]:
        lines.extend(["", "## Ties at Top Score", ""])
        lines.extend(f"- `{bundle_id}`" for bundle_id in selection_payload["ties_at_top_score"])
    write_markdown(output_dir / "selected_trajectory_bundle.md", "\n".join(lines) + "\n")
