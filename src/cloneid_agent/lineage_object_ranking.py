"""Ranking for globally discovered lineage objects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .lineage_objects import lineage_object_features
from .run_io import write_json, write_markdown


def _ratio(value: float, full_at: float) -> float:
    if full_at <= 0 or value <= 0:
        return 0.0
    return min(value / full_at, 1.0)


def _candidate_signal(features: dict[str, Any]) -> float:
    score_max = features.get("candidate_segment_score_max")
    score_mean = features.get("candidate_segment_score_mean")
    if score_max is None and score_mean is None:
        return 0.0
    values = [value for value in (score_max, score_mean) if value is not None]
    return sum(float(value) for value in values) / len(values)


def score_lineage_object(object_payload: dict[str, Any]) -> dict[str, Any]:
    features = lineage_object_features(object_payload)
    object_type = object_payload["lineage_object_type"]
    eligible = bool(object_payload.get("selection_eligible", False))

    if object_type == "LineageForest":
        reasons = ["multi-root object is classified as LineageForest and is not eligible for selection"]
        return {
            **object_payload,
            "lineage_object_features": features,
            "lineage_object_score": 0.0,
            "lineage_object_score_components": {},
            "lineage_object_score_penalties": {"invalid_multi_root_penalty": 100.0},
            "lineage_object_score_reasons": reasons,
        }

    candidate_signal = _candidate_signal(features)
    phenotype_strength = 25.0 * (
        0.65 * _ratio(float(features["phenotype_observation_count"]), 18.0)
        + 0.35 * _ratio(float(features["phenotype_time_span_days"]), 60.0)
    )
    endpoint_support = 20.0 * _ratio(float(features["terminal_perspective_support"]), 4.0)
    context_signal = 10.0 * (
        0.65 * _ratio(float(features["transition_count"]), 8.0)
        + 0.35 * float(bool(features["calibration_validation_split_possible"]))
    )
    candidate_segment_signal = 10.0 * _ratio(float(candidate_signal), 100.0)

    if object_type == "LineagePath":
        structure_signal = 25.0 * _ratio(float(features["lineage_path_length"]), 12.0)
        tractability = 10.0 * (
            0.6 * _ratio(float(features["lineage_path_length"]), 10.0)
            + 0.4 * (1.0 if features["lineage_path_length"] <= 20 else max(0.0, 1.0 - (features["lineage_path_length"] - 20) / 20.0))
        )
    else:
        structure_signal = 25.0 * (
            0.6 * _ratio(float(features["event_graph_depth"]), 8.0)
            + 0.4 * _ratio(float(features["event_count"]), 80.0)
        )
        tractability = 10.0 * (
            0.5 * (1.0 if features["event_graph_depth"] <= 12 else max(0.0, 1.0 - (features["event_graph_depth"] - 12) / 12.0))
            + 0.5 * (1.0 if features["event_count"] <= 120 else max(0.0, 1.0 - (features["event_count"] - 120) / 120.0))
        )

    penalties = {
        "missing_endpoint_perspective_penalty": 0.0,
        "invalid_path_penalty": 0.0,
    }
    if features["terminal_perspective_support"] == 0:
        penalties["missing_endpoint_perspective_penalty"] = 20.0
    if not eligible:
        penalties["invalid_path_penalty"] = 100.0

    components = {
        "structure_signal": round(structure_signal, 3),
        "phenotype_strength": round(phenotype_strength, 3),
        "endpoint_support": round(endpoint_support, 3),
        "context_signal": round(context_signal, 3),
        "candidate_segment_signal": round(candidate_segment_signal, 3),
        "tractability": round(tractability, 3),
    }
    total_score = round(max(sum(components.values()) - sum(penalties.values()), 0.0), 3)

    reasons = []
    if object_type == "LineagePath":
        reasons.append("global discovery recovered an explicit endpoint-to-root lineage path")
    else:
        reasons.append("global discovery recovered a single-root descendant subtree")
    if features["lineage_path_length"] >= 8:
        reasons.append("lineage path is long enough to span multiple primary-lineage transitions")
    if features["event_graph_depth"] >= 4:
        reasons.append("object covers substantial primary-lineage depth")
    if features["phenotype_observation_count"] >= 5:
        reasons.append("repeated phenotype observations support calibration")
    if features["terminal_perspective_support"] > 0:
        reasons.append("endpoint Perspective support is available")
    if candidate_signal >= 60:
        reasons.append("covered CandidateSegments include strong local modelability signals")
    for name, value in penalties.items():
        if value > 0:
            reasons.append(f"penalized for {name.replace('_', ' ')}")

    return {
        **object_payload,
        "lineage_object_features": features,
        "lineage_object_score": total_score,
        "lineage_object_score_components": components,
        "lineage_object_score_penalties": {key: round(value, 3) for key, value in penalties.items()},
        "lineage_object_score_reasons": reasons,
    }


def rank_lineage_object_inventory(inventory_payload: dict[str, Any]) -> dict[str, Any]:
    ranked = [score_lineage_object(item) for item in inventory_payload.get("global_lineage_objects", [])]
    ranked.sort(
        key=lambda item: (
            not bool(item.get("selection_eligible", False)),
            -float(item["lineage_object_score"]),
            item["lineage_object_id"],
        )
    )
    return {
        "score_model": "global_lineage_object_v1",
        "lineage_object_count": len(ranked),
        "ranked_lineage_objects": ranked,
        "source_inventory_summary": {
            "discovered_object_counts": inventory_payload.get("discovered_object_counts", {}),
            "lineage_path_length_distribution": inventory_payload.get("lineage_path_length_distribution", []),
            "rooted_trajectory_bundle_depth_distribution": inventory_payload.get(
                "rooted_trajectory_bundle_depth_distribution",
                [],
            ),
        },
        "warnings": [
            "Global lineage-object discovery is performed before CandidateSegment scores are used as annotations or ranking features.",
            "LineageForests are not eligible for selection.",
            "passaged_from_id2 is recorded but not traversed by default.",
        ],
    }


def rank_lineage_objects_from_file(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    return rank_lineage_object_inventory(payload)


def write_ranked_lineage_objects(output_dir: str | Path, ranked_payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    write_json(output_dir / "ranked_lineage_objects.json", ranked_payload)
    lines = [
        "# Ranked Lineage Objects",
        "",
        f"- Lineage object count: `{ranked_payload['lineage_object_count']}`",
        f"- Score model: `{ranked_payload['score_model']}`",
        "",
        "## Top 10 Ranked Lineage Objects",
        "",
    ]
    for item in ranked_payload.get("ranked_lineage_objects", [])[:10]:
        lines.append(
            f"- `{item['lineage_object_id']}` type `{item['lineage_object_type']}` score `{item['lineage_object_score']}` eligible `{item['selection_eligible']}`"
        )
    write_markdown(output_dir / "ranked_lineage_objects.md", "\n".join(lines) + "\n")
