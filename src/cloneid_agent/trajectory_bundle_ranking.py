"""Deterministic ranking for discovered TrajectoryBundle payloads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .run_io import write_json, write_markdown


def _saturating_ratio(value: float, full_at: float) -> float:
    if full_at <= 0 or value <= 0:
        return 0.0
    return min(value / full_at, 1.0)


def _tractability_window(value: float, low: float, ideal_low: float, ideal_high: float, high: float) -> float:
    if value <= low or value >= high:
        return 0.0
    if ideal_low <= value <= ideal_high:
        return 1.0
    if value < ideal_low:
        return (value - low) / max(ideal_low - low, 1e-9)
    return (high - value) / max(high - ideal_high, 1e-9)


def score_trajectory_bundle_payload(bundle_payload: dict[str, Any]) -> dict[str, Any]:
    features = bundle_payload["trajectory_bundle_features"]

    connected_history_strength = 25.0 * (
        0.35 * _saturating_ratio(float(features["connected_segment_count"]), 6.0)
        + 0.40 * _saturating_ratio(float(features["event_graph_depth"]), 5.0)
        + 0.25 * _saturating_ratio(float(features["event_count"]), 14.0)
    )
    transition_coverage = 15.0 * (
        0.75 * _saturating_ratio(float(features["transition_count"]), 8.0)
        + 0.25 * float(bool(features["has_longitudinal_context_change"]))
    )
    phenotype_trajectory_strength = 25.0 * (
        0.65 * _saturating_ratio(float(features["phenotype_observation_count"]), 12.0)
        + 0.35 * _saturating_ratio(float(features["phenotype_time_span_days"]), 30.0)
    )
    terminal_perspective_value = 15.0 * (
        0.75 * _saturating_ratio(float(features["terminal_perspective_support"]), 6.0)
        + 0.25 * float(bool(bundle_payload.get("perspective_records")))
    )
    calibration_validation_split = 10.0 * float(bool(features["calibration_validation_split_possible"]))

    event_window = _tractability_window(float(features["event_count"]), 1.0, 4.0, 16.0, 48.0)
    transition_window = _tractability_window(float(features["transition_count"]), 0.0, 1.0, 8.0, 20.0)
    segment_window = _tractability_window(float(features["connected_segment_count"]), 0.0, 1.0, 5.0, 12.0)
    tractability = 10.0 * (
        0.45 * event_window
        + 0.30 * transition_window
        + 0.25 * segment_window
    )

    penalties = {
        "tractability_penalty": min(float(features["trajectory_bundle_complexity_penalty"]), 12.0),
        "branching_penalty": 0.0,
        "sparse_phenotype_penalty": 0.0,
    }
    if bool(features["has_branching"]) and int(features["event_count"]) > 10:
        penalties["branching_penalty"] = 4.0
    if int(features["phenotype_observation_count"]) < 3:
        penalties["sparse_phenotype_penalty"] = 6.0 - min(int(features["phenotype_observation_count"]), 3) * 2.0

    components = {
        "connected_history_strength": round(connected_history_strength, 3),
        "transition_coverage": round(transition_coverage, 3),
        "phenotype_trajectory_strength": round(phenotype_trajectory_strength, 3),
        "terminal_perspective_value": round(terminal_perspective_value, 3),
        "calibration_validation_split": round(calibration_validation_split, 3),
        "tractability": round(tractability, 3),
    }
    total_penalty = sum(penalties.values())
    total_score = round(max(sum(components.values()) - total_penalty, 0.0), 3)

    component_labels = {
        "connected_history_strength": "connected event history spans multiple useful local segments",
        "transition_coverage": "context transitions are explicit and model-relevant",
        "phenotype_trajectory_strength": "repeated phenotype observations exist across the connected history",
        "terminal_perspective_value": "terminal Perspective support is available for endpoint comparison",
        "calibration_validation_split": "bundle supports a calibration/validation split",
        "tractability": "bundle complexity is still tractable for a first proof of principle",
    }
    penalty_labels = {
        "tractability_penalty": "bundle complexity is high relative to the first-round-trip scope",
        "branching_penalty": "branching topology may complicate first-pass mechanistic mapping",
        "sparse_phenotype_penalty": "too few phenotype observations across the connected history",
    }
    reasons = [
        component_labels[name]
        for name, value in sorted(components.items(), key=lambda item: (-item[1], item[0]))
        if value >= 6.0
    ][:4]
    reasons.extend(
        f"penalized for {penalty_labels[name]}"
        for name, value in penalties.items()
        if value > 0
    )
    if not reasons:
        reasons.append("limited evidence for a first-pass TrajectoryBundle round trip")

    return {
        **bundle_payload,
        "trajectory_bundle_score": total_score,
        "trajectory_bundle_score_components": components,
        "trajectory_bundle_score_penalties": {
            key: round(value, 3) for key, value in penalties.items()
        },
        "trajectory_bundle_score_reasons": reasons,
    }


def rank_trajectory_bundle_payloads(bundle_payloads: list[dict[str, Any]]) -> dict[str, Any]:
    ranked = [score_trajectory_bundle_payload(payload) for payload in bundle_payloads]
    ranked.sort(
        key=lambda item: (-item["trajectory_bundle_score"], item["bundle_id"])
    )
    return {
        "bundle_count": len(ranked),
        "score_model": "trajectory_bundle_v1",
        "score_scale": "0-100",
        "ranked_trajectory_bundles": ranked,
        "warnings": [
            "CandidateSegment ranking remains the first-stage screen.",
            "TrajectoryBundle ranking compares connected event-history modeling units discovered from those seed segments.",
            "Perspective is primary endpoint support; Identity remains inferred secondary support only.",
        ],
    }


def rank_trajectory_bundles_from_files(paths: list[str | Path]) -> dict[str, Any]:
    payloads = [json.loads(Path(path).read_text()) for path in paths]
    return rank_trajectory_bundle_payloads(payloads)


def write_ranked_trajectory_bundles(output_dir: str | Path, ranked_payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    write_json(output_dir / "ranked_trajectory_bundles.json", ranked_payload)

    lines = [
        "# Ranked Trajectory Bundles",
        "",
        f"- Bundle count: `{ranked_payload['bundle_count']}`",
        f"- Score model: `{ranked_payload['score_model']}`",
        "",
        "## Top bundles",
        "",
    ]
    for bundle in ranked_payload["ranked_trajectory_bundles"][:10]:
        lines.append(
            f"- `{bundle['bundle_id']}` score `{bundle['trajectory_bundle_score']}`"
        )
    write_markdown(output_dir / "ranked_trajectory_bundles.md", "\n".join(lines) + "\n")
