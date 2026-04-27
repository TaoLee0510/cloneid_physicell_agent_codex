"""Fine-grained ontology-aware ranking over candidate-dataset inventory records."""

from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any

from .run_io import write_json, write_markdown


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value in (0, 0.0, None, "", "FALSE", "False", "false"):
        return False
    return True


def _safe_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.strptime(str(value), "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return None


def _span_days(date_min: Any, date_max: Any) -> float:
    start = _parse_datetime(date_min)
    stop = _parse_datetime(date_max)
    if start is None or stop is None:
        return 0.0
    return max((stop - start).total_seconds() / 86400.0, 0.0)


def _saturating_ratio(value: float, full_at: float) -> float:
    if full_at <= 0:
        return 0.0
    if value <= 0:
        return 0.0
    return min(value / full_at, 1.0)


def _log_saturation(value: float, full_at: float) -> float:
    if value <= 0 or full_at <= 1:
        return 0.0
    return min(math.log1p(value) / math.log1p(full_at), 1.0)


def _band_score(value: float, low: float, ideal_low: float, ideal_high: float, high: float) -> float:
    if value <= low or value >= high:
        return 0.0
    if ideal_low <= value <= ideal_high:
        return 1.0
    if value < ideal_low:
        return (value - low) / max(ideal_low - low, 1e-9)
    return (high - value) / max(high - ideal_high, 1e-9)


def extract_candidate_features(record: dict[str, Any]) -> dict[str, Any]:
    """Normalize the grouped candidate-inventory record into ranking features."""
    passaging_rows = _safe_int(record.get("passaging_rows"))
    distinct_dates = _safe_int(record.get("distinct_dates"))
    corrected_count_rows = _safe_int(record.get("corrected_count_rows"))
    area_rows = _safe_int(record.get("area_rows"))
    qupath_rows = _safe_int(record.get("qupath_rows"))
    perspective_rows = _safe_int(record.get("perspective_rows"))
    distinct_perspectives = _safe_int(record.get("distinct_perspectives"))
    distinct_perspective_states = _safe_int(record.get("distinct_perspective_states"))
    harvest_events = _safe_int(record.get("harvest_events"))
    seeding_events = _safe_int(record.get("seeding_events"))
    lineage_link_rows = _safe_int(record.get("lineage_link_rows"))
    context_complete = _bool(record.get("context_complete", False))

    phenotype_rows = max(corrected_count_rows, area_rows, qupath_rows)
    phenotype_modalities = sum(
        1 for count in (corrected_count_rows, area_rows, qupath_rows) if count > 0
    )
    trajectory_available = distinct_dates >= 2 and phenotype_rows >= 2
    event_history_available = passaging_rows >= 2 and (
        lineage_link_rows >= 1 or harvest_events >= 1 or seeding_events >= 1
    )
    endpoint_molecular_available = perspective_rows > 0 or distinct_perspectives > 0

    return {
        "dataset_id": str(record["dataset_id"]),
        "passaging_rows": passaging_rows,
        "distinct_dates": distinct_dates,
        "corrected_count_rows": corrected_count_rows,
        "area_rows": area_rows,
        "qupath_rows": qupath_rows,
        "phenotype_rows": phenotype_rows,
        "phenotype_modalities": phenotype_modalities,
        "perspective_rows": perspective_rows,
        "distinct_perspectives": distinct_perspectives,
        "distinct_perspective_states": distinct_perspective_states,
        "harvest_events": harvest_events,
        "seeding_events": seeding_events,
        "lineage_link_rows": lineage_link_rows,
        "context_complete": context_complete,
        "trajectory_available": trajectory_available,
        "event_history_available": event_history_available,
        "endpoint_molecular_available": endpoint_molecular_available,
        "temporal_span_days": _span_days(record.get("date_min"), record.get("date_max")),
    }


def fine_score_candidate_record(record: dict[str, Any]) -> dict[str, Any]:
    """Assign a fine-grained 0-to-100 score with auditable components and penalties."""
    features = extract_candidate_features(record)

    trajectory_strength = 30.0 * (
        0.55 * _log_saturation(features["distinct_dates"], 12)
        + 0.25 * _log_saturation(features["passaging_rows"], 20)
        + 0.20 * _saturating_ratio(features["temporal_span_days"], 90.0)
    )

    corrected_signal = _log_saturation(features["corrected_count_rows"], 12)
    area_signal = _log_saturation(features["area_rows"], 12)
    qupath_signal = _log_saturation(features["qupath_rows"], 12)
    phenotype_quality = 20.0 * (
        0.45 * corrected_signal
        + 0.35 * area_signal
        + 0.10 * qupath_signal
        + 0.10 * _saturating_ratio(features["phenotype_modalities"], 2.0)
    )

    transition_signal = _saturating_ratio(
        features["seeding_events"] + features["harvest_events"],
        6.0,
    )
    event_context_coherence = 15.0 * (
        0.40 * float(features["context_complete"])
        + 0.35 * _log_saturation(features["lineage_link_rows"], 12)
        + 0.25 * transition_signal
    )

    perspective_presence = float(features["endpoint_molecular_available"])
    perspective_state_signal = _log_saturation(features["distinct_perspective_states"], 12)
    perspective_row_signal = _log_saturation(features["perspective_rows"], 48)
    molecular_endpoint_value = 15.0 * (
        0.25 * perspective_presence
        + 0.50 * perspective_state_signal
        + 0.25 * perspective_row_signal
    )

    calibration_validation_alignment = 10.0 * (
        0.50 * float(features["trajectory_available"])
        + 0.30 * perspective_presence
        + 0.20 * float(features["context_complete"])
    )

    event_window = _band_score(features["passaging_rows"], 1, 4, 30, 160)
    state_window = _band_score(features["distinct_perspective_states"], 0, 2, 24, 64)
    phenotype_window = _band_score(features["distinct_dates"], 1, 4, 24, 120)
    first_round_trip_tractability = 10.0 * (
        0.45 * event_window
        + 0.25 * state_window
        + 0.20 * phenotype_window
        + 0.10 * float(features["context_complete"])
    )

    penalties = {
        "molecular_only_penalty": 0.0,
        "sparse_trajectory_penalty": 0.0,
        "context_ambiguity_penalty": 0.0,
        "overaggregated_candidate_penalty": 0.0,
    }
    if not features["trajectory_available"] and features["endpoint_molecular_available"]:
        penalties["molecular_only_penalty"] = 20.0 * max(
            perspective_state_signal,
            perspective_row_signal,
        )
    if features["distinct_dates"] < 4:
        penalties["sparse_trajectory_penalty"] = 15.0 * (4 - features["distinct_dates"]) / 4.0
    if not features["context_complete"]:
        penalties["context_ambiguity_penalty"] = 15.0
    if (
        (features["passaging_rows"] <= 3 and features["perspective_rows"] > 100)
        or (features["distinct_dates"] <= 3 and features["distinct_perspective_states"] > 15)
    ):
        penalties["overaggregated_candidate_penalty"] = 10.0

    components = {
        "trajectory_strength": round(trajectory_strength, 3),
        "phenotype_quality": round(phenotype_quality, 3),
        "event_context_coherence": round(event_context_coherence, 3),
        "molecular_endpoint_value": round(molecular_endpoint_value, 3),
        "calibration_validation_alignment": round(calibration_validation_alignment, 3),
        "first_round_trip_tractability": round(first_round_trip_tractability, 3),
    }
    total_penalty = sum(penalties.values())
    total_score = round(max(sum(components.values()) - total_penalty, 0.0), 3)

    component_labels = {
        "trajectory_strength": "strong repeated phenotypic trajectory",
        "phenotype_quality": "usable phenotype measurements for calibration",
        "event_context_coherence": "coherent event history and initialization context",
        "molecular_endpoint_value": "informative endpoint Perspective support",
        "calibration_validation_alignment": "clear phenotype-to-endpoint comparison path",
        "first_round_trip_tractability": "good first-round-trip tractability",
    }
    penalty_labels = {
        "molecular_only_penalty": "heavy molecular support without enough repeated phenotype",
        "sparse_trajectory_penalty": "too few repeated observation dates",
        "context_ambiguity_penalty": "missing initialization context",
        "overaggregated_candidate_penalty": "molecular detail looks over-aggregated relative to the trajectory",
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
        reasons.append("limited evidence for a first-pass CLONEID-to-PhysiCell round trip")

    return {
        **record,
        "score": total_score,
        "score_components": components,
        "score_penalties": {name: round(value, 3) for name, value in penalties.items()},
        "score_reasons": reasons,
        "temporal_span_days": round(features["temporal_span_days"], 3),
    }


def rank_candidates_from_inventory_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Rank candidate datasets from a candidate-inventory payload."""
    candidates = payload.get("candidates", [])
    ranked_candidates = [fine_score_candidate_record(record) for record in candidates]
    ranked_candidates.sort(key=lambda item: (-item["score"], item["dataset_id"]))
    return {
        "source_run_id": payload.get("run_id"),
        "generated_from": "dataset_inventory.json",
        "grouping_definition": payload.get("grouping_definition"),
        "candidate_count": len(ranked_candidates),
        "score_model": "fine_grained_v1",
        "score_scale": "0-100",
        "ranked_candidates": ranked_candidates,
        "warnings": [
            "Ranking now uses a fine-grained ontology-aware score over grouped candidate inventory records.",
            "Perspective is treated as primary endpoint molecular evidence.",
            "Identity remains secondary / interpretive support and is not promoted to direct phenotype evidence.",
            "Phenotype trajectory strength is weighted more heavily than raw molecular row volume for the first PhysiCell proof of principle.",
        ],
    }


def rank_candidates_from_file(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    return rank_candidates_from_inventory_payload(payload)


def write_ranked_candidates(output_dir: str | Path, ranked_payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    write_json(output_dir / "ranked_candidates.json", ranked_payload)

    lines = [
        "# Ranked Candidates",
        "",
        f"- Candidate count: `{ranked_payload['candidate_count']}`",
        f"- Score model: `{ranked_payload['score_model']}`",
        f"- Score scale: `{ranked_payload['score_scale']}`",
        "",
        "| Rank | Dataset ID | Score | Top Reasons |",
        "|---:|---|---:|---|",
    ]
    for idx, record in enumerate(ranked_payload["ranked_candidates"], start=1):
        lines.append(
            f"| {idx} | `{record['dataset_id']}` | {record['score']:.3f} | {'; '.join(record['score_reasons'])} |"
        )
    if ranked_payload.get("warnings"):
        lines.extend(["", "## Warnings", ""])
        lines.extend([f"- {warning}" for warning in ranked_payload["warnings"]])
    write_markdown(output_dir / "ranked_candidates.md", "\n".join(lines) + "\n")
