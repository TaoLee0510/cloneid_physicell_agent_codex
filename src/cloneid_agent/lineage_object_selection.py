"""Selection helpers for ranked global lineage objects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .run_io import write_json, write_markdown


def select_top_lineage_object(ranked_payload: dict[str, Any]) -> dict[str, Any]:
    ranked = ranked_payload.get("ranked_lineage_objects", [])
    eligible = [item for item in ranked if item.get("selection_eligible", False)]
    if not eligible:
        raise ValueError("No selection-eligible lineage objects found")
    top = eligible[0]
    top_score = top["lineage_object_score"]
    ties = [
        item["lineage_object_id"]
        for item in eligible
        if item["lineage_object_score"] == top_score
    ]
    return {
        "selected_lineage_object_id": top["lineage_object_id"],
        "selected_lineage_object_type": top["lineage_object_type"],
        "lineage_object_score": top_score,
        "lineage_object_score_reasons": top.get("lineage_object_score_reasons", []),
        "ties_at_top_score": ties,
        "selection_policy": "Highest-ranked selection-eligible global lineage object wins; ties are retained for review.",
        "selected_record": top,
    }


def select_top_lineage_object_from_file(path: str | Path) -> dict[str, Any]:
    return select_top_lineage_object(json.loads(Path(path).read_text()))


def build_selected_lineage_object_record(selection_payload: dict[str, Any]) -> dict[str, Any]:
    selected = dict(selection_payload["selected_record"])
    return {
        "selected_lineage_object_id": selection_payload["selected_lineage_object_id"],
        "selected_lineage_object_type": selection_payload["selected_lineage_object_type"],
        "selection_summary": {
            "lineage_object_score": selection_payload["lineage_object_score"],
            "lineage_object_score_reasons": selection_payload["lineage_object_score_reasons"],
            "ties_at_top_score": selection_payload["ties_at_top_score"],
        },
        **selected,
    }


def write_selected_lineage_object(output_dir: str | Path, selection_payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    record = build_selected_lineage_object_record(selection_payload)
    write_json(output_dir / "selected_lineage_object.json", record)
    write_json(output_dir / "selected_lineage_object_selection.json", selection_payload)

    features = record.get("lineage_object_features", {})
    lines = [
        "# Selected Lineage Object",
        "",
        f"- Selected lineage object: `{record['selected_lineage_object_id']}`",
        f"- Type: `{record['selected_lineage_object_type']}`",
        f"- Root count: `{features.get('root_count')}`",
        f"- Path length: `{features.get('lineage_path_length')}`",
        f"- Subtree depth: `{features.get('event_graph_depth')}`",
        f"- CandidateSegments covered: `{features.get('connected_segment_count')}`",
        f"- Selection starts from CandidateSegment: `false`",
        "",
        "## Reasons",
        "",
    ]
    lines.extend(f"- {reason}" for reason in selection_payload.get("lineage_object_score_reasons", []))
    write_markdown(output_dir / "selected_lineage_object.md", "\n".join(lines) + "\n")
