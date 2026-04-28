"""Bounded modeling-candidate selection from globally discovered lineage objects."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .observable_selection import summarize_calibration_candidates
from .run_io import write_json, write_markdown


DEFAULT_MODELING_FILTERS = {
    "max_event_count": 200,
    "max_graph_depth": 40,
    "max_time_span_days": 180.0,
    "max_context_regimes": 3,
    "min_repeated_phenotype_observations": 4,
    "min_bundle_terminal_perspective_endpoints": 2,
    "min_path_terminal_perspective_endpoints": 1,
}
DEFAULT_SMOKE_FILTERS = {
    "max_planned_max_time_min": 86400,
    "max_event_count": 200,
    "max_graph_depth": 40,
}
DEFAULT_BIOLOGICAL_PROOF_FILTERS = {
    "min_event_count": 8,
    "min_repeated_phenotype_observations": 6,
    "min_terminal_perspective_support": 1,
    "max_phase_abstracted_path_event_count": 120,
    "max_phase_abstracted_bundle_event_count": 80,
    "max_phase_abstracted_bundle_depth": 40,
    "normalized_phase_duration_min": 1440,
}


def _context_regimes(object_payload: dict[str, Any]) -> list[dict[str, Any]]:
    regimes = {
        (
            record.get("cellLine"),
            record.get("growthType"),
            record.get("media"),
        )
        for record in object_payload.get("passaging_records", [])
    }
    ordered = sorted(regimes, key=lambda item: tuple("" if value is None else str(value) for value in item))
    return [
        {
            "cellLine": cell_line,
            "growthType": growth_type,
            "media": media,
        }
        for cell_line, growth_type, media in ordered
    ]


def _modeling_score(object_payload: dict[str, Any], filters: dict[str, Any]) -> float:
    features = object_payload.get("lineage_object_features", {})
    base = float(object_payload.get("lineage_object_score", 0.0))
    object_type = object_payload.get("lineage_object_type")
    path_length = float(features.get("lineage_path_length", 0))
    event_depth = float(features.get("event_graph_depth", 0))
    event_count = float(features.get("event_count", 0))
    span_days = float(features.get("phenotype_time_span_days", 0.0))
    terminal_support = float(features.get("terminal_perspective_support", 0))

    boundedness_bonus = 0.0
    if object_type == "LineagePath":
        boundedness_bonus += 10.0
        boundedness_bonus += min(path_length / 12.0, 1.0) * 10.0
    else:
        boundedness_bonus += 4.0
        boundedness_bonus += max(0.0, 1.0 - max(event_count - 80.0, 0.0) / 120.0) * 6.0

    boundedness_bonus += max(0.0, 1.0 - max(event_depth - 12.0, 0.0) / 28.0) * 8.0
    boundedness_bonus += max(0.0, 1.0 - max(span_days - 90.0, 0.0) / max(float(filters["max_time_span_days"]) - 90.0, 1.0)) * 6.0
    boundedness_bonus += min(terminal_support / 4.0, 1.0) * 4.0
    return round(base + boundedness_bonus, 3)


def _planned_max_time_min(features: dict[str, Any]) -> int:
    span_days = float(features.get("phenotype_time_span_days", 0.0) or 0.0)
    if span_days <= 0:
        return 1440
    return max(60, int(round(span_days * 1440.0)))


def _parse_date(text: Any) -> Any:
    if not isinstance(text, str):
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            from datetime import datetime

            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _record_index(passaging_records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(record.get("id")): record for record in passaging_records if record.get("id") is not None}


def _ordered_records_for_object(object_payload: dict[str, Any]) -> list[dict[str, Any]]:
    passaging_records = object_payload.get("passaging_records", [])
    by_id = _record_index(passaging_records)
    if object_payload.get("lineage_object_type") == "LineagePath":
        ordered = [by_id[str(event_id)] for event_id in object_payload.get("lineage_path_event_ids", []) if str(event_id) in by_id]
        if ordered:
            return ordered
    return sorted(
        passaging_records,
        key=lambda record: (
            record.get("date") or "",
            str(record.get("id") or ""),
        ),
    )


def _phase_context_signature(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "cellLine": record.get("cellLine"),
        "growthType": record.get("growthType"),
        "media": record.get("media"),
        "flask": record.get("flask"),
        "passage": record.get("passage"),
    }


def _phase_transition_tags(start: dict[str, Any], end: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    if start.get("passage") != end.get("passage"):
        tags.append("passage_interval")
    if start.get("media") != end.get("media"):
        tags.append("media_regime_change")
    if start.get("growthType") != end.get("growthType"):
        tags.append("growth_regime_change")
    if start.get("flask") != end.get("flask"):
        tags.append("flask_transfer")
    end_id = str(end.get("id") or "")
    if "harvest" in end_id.lower():
        tags.append("harvest_interval")
    if not tags:
        tags.append("within_regime_interval")
    return tags


def _build_phase_abstraction_plan(
    object_payload: dict[str, Any],
    *,
    normalized_phase_duration_min: int,
) -> dict[str, Any]:
    ordered = _ordered_records_for_object(object_payload)
    phases: list[dict[str, Any]] = []
    transition_kinds: set[str] = set()
    for index, (start, end) in enumerate(zip(ordered, ordered[1:]), start=1):
        start_dt = _parse_date(start.get("date"))
        end_dt = _parse_date(end.get("date"))
        real_elapsed_min = None
        if start_dt is not None and end_dt is not None:
            real_elapsed_min = max(0, int(round((end_dt - start_dt).total_seconds() / 60.0)))
        tags = _phase_transition_tags(start, end)
        transition_kinds.update(tags)
        phases.append(
            {
                "phase_index": index,
                "start_event_id": start.get("id"),
                "end_event_id": end.get("id"),
                "real_elapsed_minutes": real_elapsed_min,
                "real_elapsed_days": None if real_elapsed_min is None else round(real_elapsed_min / 1440.0, 3),
                "simulated_phase_duration_min": int(normalized_phase_duration_min),
                "start_context": _phase_context_signature(start),
                "end_context": _phase_context_signature(end),
                "transition_tags": tags,
                "provenance_event_order": [start.get("id"), end.get("id")],
            }
        )
    phase_count = len(phases)
    return {
        "mapping_policy": "primary_lineage_intervals_normalized",
        "description": (
            "Represent each primary lineage interval as a model phase, preserve event order and provenance, "
            "and compare observed phenotype values at phase boundaries without simulating idle calendar time literally."
        ),
        "normalized_phase_duration_min": int(normalized_phase_duration_min),
        "phase_count": phase_count,
        "passage_interval_count": phase_count,
        "simulated_total_duration_min": phase_count * int(normalized_phase_duration_min),
        "transition_kinds": sorted(transition_kinds),
        "phases": phases,
    }


def _lineage_label_tokens(lineage_object_id: str) -> list[str]:
    label = lineage_object_id.split("::", 1)[-1]
    return [token for token in re.split(r"[_]+", label) if token]


def _anchor_tokens(tokens: list[str]) -> set[str]:
    anchors = set()
    for token in tokens:
        if re.match(r"^[A-Z]\d+[A-Z]*$", token):
            anchors.add(token)
        elif re.match(r"^(harvesT\d+|harvest|seedT?\d*)$", token, flags=re.IGNORECASE):
            anchors.add(token.lower())
    return anchors


def _comparison_tokens(tokens: list[str]) -> set[str]:
    comparisons = set()
    for token in tokens:
        if re.match(r"^(2N|4N|O1|O2|G\d+|RevG\d*|K\d+)$", token):
            comparisons.add(token)
    return comparisons


def _same_cell_line(item: dict[str, Any], other: dict[str, Any]) -> bool:
    left = {record.get("cellLine") for record in item.get("passaging_records", []) if record.get("cellLine") is not None}
    right = {record.get("cellLine") for record in other.get("passaging_records", []) if record.get("cellLine") is not None}
    return bool(left) and left == right


def _matched_lineage_candidates(
    item: dict[str, Any],
    ranked_items: list[dict[str, Any]],
) -> tuple[list[str], list[str]]:
    item_tokens = _lineage_label_tokens(item["lineage_object_id"])
    item_anchors = _anchor_tokens(item_tokens)
    item_comparisons = _comparison_tokens(item_tokens)
    matched: list[str] = []
    siblings: list[str] = []
    for other in ranked_items:
        other_id = other["lineage_object_id"]
        if other_id == item["lineage_object_id"] or other.get("lineage_object_type") != item.get("lineage_object_type"):
            continue
        if not _same_cell_line(item, other):
            continue
        other_tokens = _lineage_label_tokens(other_id)
        other_anchors = _anchor_tokens(other_tokens)
        other_comparisons = _comparison_tokens(other_tokens)
        shared_anchor = bool(item_anchors & other_anchors)
        if not shared_anchor:
            continue
        siblings.append(other_id)
        if item_comparisons != other_comparisons:
            matched.append(other_id)
    return sorted(set(matched)), sorted(set(siblings))


def _suggested_biological_question(
    item: dict[str, Any],
    matched_lineage_candidates: list[str],
) -> str:
    lineage_id = item["lineage_object_id"]
    passaging_records = item.get("passaging_records", [])
    cell_line = next((record.get("cellLine") for record in passaging_records if record.get("cellLine") is not None), None)
    if cell_line == "SUM-159" and matched_lineage_candidates:
        return (
            "Inference from lineage labels: compare matched SUM-159 ploidy / oxygen-state lineage paths to test "
            "whether state-specific history changes expansion behavior across repeated passages and harvest endpoints."
        )
    if cell_line == "HGC-27" and matched_lineage_candidates:
        return (
            "Inference from lineage labels: compare matched HGC-27 G2 versus RevG lineage paths to test whether "
            "the reverted branch reproduces or diverges from the paired growth trajectory under related passaging contexts."
        )
    if cell_line == "SNU-668":
        return (
            "Test whether repeated count / area trajectories on the primary lineage backbone can be explained by a "
            "single growth-history model before adding more detailed branch-specific mechanisms."
        )
    return (
        "Test whether repeated phenotype observations along the primary lineage backbone can be recapitulated with a "
        "small mechanistic model while using terminal Perspective support as endpoint validation."
    )


def _recommended_modeling_form(item: dict[str, Any], matched_lineage_candidates: list[str]) -> str:
    if item.get("lineage_object_type") == "LineagePath" and matched_lineage_candidates:
        return "matched LineagePath pair"
    if item.get("lineage_object_type") == "LineagePath":
        return "single LineagePath"
    return "small RootedTrajectoryBundle"


def _biological_candidate_score(item: dict[str, Any]) -> float:
    features = item.get("lineage_object_features", {})
    base = float(item.get("lineage_object_score", 0.0))
    event_count = float(features.get("event_count", 0))
    depth = float(features.get("event_graph_depth", 0))
    terminal_support = float(features.get("terminal_perspective_support", 0))
    phenotype_count = float(features.get("phenotype_observation_count", 0))
    matched_count = float(len(item.get("matched_lineage_candidates", [])))
    raw_time_bonus = 0.0 if item.get("raw_time_simulation_eligible") else -2.0
    phase_bonus = 8.0 if item.get("phase_abstracted_modeling_eligible") else 0.0
    pair_bonus = min(matched_count, 2.0) * 6.0
    phenotype_bonus = min(phenotype_count / 12.0, 1.0) * 6.0
    terminal_bonus = min(terminal_support, 2.0) * 2.0
    size_penalty = max(event_count - 40.0, 0.0) / 6.0 + max(depth - 30.0, 0.0) / 5.0
    if item.get("technical_smoke_only_candidate"):
        size_penalty += 30.0
    return round(base + raw_time_bonus + phase_bonus + pair_bonus + phenotype_bonus + terminal_bonus - size_penalty, 3)


def classify_lineage_objects_for_modeling(
    ranked_payload: dict[str, Any],
    *,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    filters = dict(DEFAULT_MODELING_FILTERS if filters is None else {**DEFAULT_MODELING_FILTERS, **filters})
    modeling_candidates: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []

    for item in ranked_payload.get("ranked_lineage_objects", []):
        features = item.get("lineage_object_features", {})
        object_type = item.get("lineage_object_type")
        reasons: list[str] = []
        event_count = int(features.get("event_count", 0))
        graph_depth = int(features.get("event_graph_depth", 0))
        span_days = float(features.get("phenotype_time_span_days", 0.0) or 0.0)
        phenotype_count = int(features.get("phenotype_observation_count", 0))
        terminal_support = int(features.get("terminal_perspective_support", 0))
        root_count = int(features.get("root_count", 0))
        endpoint_count = int(features.get("endpoint_count", 0))
        regimes = _context_regimes(item)
        context_regime_count = len(regimes)
        calibration_candidates = summarize_calibration_candidates(item.get("passaging_records", []))
        top_calibration = calibration_candidates[0] if calibration_candidates else None

        if object_type == "LineageForest" or root_count != 1:
            reasons.append("multi_root_forest")
        if not bool(item.get("selection_eligible", False)):
            reasons.append("unclear_root_endpoint_structure")
        if event_count > int(filters["max_event_count"]):
            reasons.append("too_many_events")
        if graph_depth > int(filters["max_graph_depth"]):
            reasons.append("excessive_depth")
        if span_days > float(filters["max_time_span_days"]):
            reasons.append("excessive_time_span")
        if context_regime_count > int(filters["max_context_regimes"]):
            reasons.append("too_many_context_regimes")
        if phenotype_count < int(filters["min_repeated_phenotype_observations"]):
            reasons.append("insufficient_repeated_phenotype")
        if endpoint_count < 1:
            reasons.append("unclear_endpoint_structure")
        if object_type == "LineagePath":
            if terminal_support < int(filters["min_path_terminal_perspective_endpoints"]):
                reasons.append("no_terminal_perspective")
        else:
            if terminal_support < int(filters["min_bundle_terminal_perspective_endpoints"]):
                reasons.append("no_terminal_perspective")
        if (
            object_type == "RootedTrajectoryBundle"
            and (
                event_count > int(filters["max_event_count"])
                or graph_depth > int(filters["max_graph_depth"])
                or span_days > float(filters["max_time_span_days"])
            )
            and (
                int(features.get("connected_segment_count", 0)) >= 8
                or endpoint_count >= 8
                or context_regime_count >= 3
            )
        ):
            reasons.append("whole_cell_line_supertree")

        annotated = {
            **item,
            "global_lineage_object_category": "global_lineage_object",
            "modeling_category": (
                "excluded_lineage_object"
                if reasons
                else "modeling_candidate_lineage_object"
            ),
            "modeling_exclusion_reasons": reasons,
            "context_regimes": regimes,
            "context_regime_count": context_regime_count,
            "planned_max_time_min": _planned_max_time_min(features),
            "raw_time_simulation_eligible": not any(
                reason in reasons
                for reason in ("too_many_events", "excessive_depth", "excessive_time_span", "whole_cell_line_supertree")
            ),
            "calibration_candidates": calibration_candidates,
            "top_calibration_observable": top_calibration,
        }
        if reasons:
            excluded.append(annotated)
        else:
            annotated["modeling_candidate_score"] = _modeling_score(annotated, filters)
            modeling_candidates.append(annotated)

    modeling_candidates.sort(
        key=lambda item: (
            item.get("lineage_object_type") != "LineagePath",
            -float(item.get("modeling_candidate_score", 0.0)),
            item["lineage_object_id"],
        )
    )
    excluded.sort(
        key=lambda item: (
            len(item.get("modeling_exclusion_reasons", [])),
            -float(item.get("lineage_object_score", 0.0)),
            item["lineage_object_id"],
        )
    )
    return {
        "selection_model": "bounded_modeling_lineage_object_v1",
        "filters": filters,
        "global_lineage_object_count": len(ranked_payload.get("ranked_lineage_objects", [])),
        "modeling_candidate_count": len(modeling_candidates),
        "excluded_lineage_object_count": len(excluded),
        "modeling_candidate_lineage_objects": modeling_candidates,
        "excluded_lineage_objects": excluded,
        "warnings": [
            "Bounded modeling-candidate selection is applied after global lineage-object discovery.",
            "Candidate selection excludes whole-cell-line supertrees for first proof-of-principle use by default.",
            "LineagePaths are preferred over large RootedTrajectoryBundles when support is otherwise comparable.",
        ],
    }


def classify_modeling_candidates_for_smoke(
    modeling_payload: dict[str, Any],
    *,
    smoke_filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    smoke_filters = dict(DEFAULT_SMOKE_FILTERS if smoke_filters is None else {**DEFAULT_SMOKE_FILTERS, **smoke_filters})
    smoke_candidates: list[dict[str, Any]] = []
    excluded_smoke: list[dict[str, Any]] = []

    for item in modeling_payload.get("modeling_candidate_lineage_objects", []):
        features = item.get("lineage_object_features", {})
        reasons: list[str] = []
        planned_max_time_min = int(item.get("planned_max_time_min", _planned_max_time_min(features)))
        terminal_support = int(features.get("terminal_perspective_support", 0))
        phenotype_count = int(features.get("phenotype_observation_count", 0))
        event_count = int(features.get("event_count", 0))
        graph_depth = int(features.get("event_graph_depth", 0))
        top_calibration = item.get("top_calibration_observable")

        if planned_max_time_min > int(smoke_filters["max_planned_max_time_min"]):
            reasons.append("exceeds_smoke_runtime_guardrail")
        if event_count > int(smoke_filters["max_event_count"]):
            reasons.append("too_many_events")
        if graph_depth > int(smoke_filters["max_graph_depth"]):
            reasons.append("excessive_depth")
        if phenotype_count < int(modeling_payload.get("filters", {}).get("min_repeated_phenotype_observations", 4)):
            reasons.append("insufficient_repeated_phenotype")
        if terminal_support <= 0:
            reasons.append("no_terminal_perspective")
        if "whole_cell_line_supertree" in item.get("modeling_exclusion_reasons", []):
            reasons.append("whole_cell_line_supertree")
        if "multi_root_forest" in item.get("modeling_exclusion_reasons", []):
            reasons.append("multi_root_forest")
        if top_calibration is None:
            reasons.append("weak_calibration_observable")
            reasons.append("no_count_or_area_trajectory")
        elif top_calibration["source"] == "Passaging.cellSize_um2":
            reasons.append("weak_calibration_observable")
            reasons.append("cell_size_only_calibration")
            reasons.append("no_count_or_area_trajectory")

        annotated = {
            **item,
            "smoke_eligibility_filters": smoke_filters,
            "smoke_eligibility_exclusion_reasons": reasons,
            "smoke_eligible": not reasons,
            "raw_time_simulation_eligible": not reasons,
        }
        if reasons:
            excluded_smoke.append(annotated)
        else:
            annotated["smoke_candidate_score"] = round(
                float(item.get("modeling_candidate_score", 0.0))
                + max(0.0, 10.0 - planned_max_time_min / 8640.0),
                3,
            )
            smoke_candidates.append(annotated)

    smoke_candidates.sort(
        key=lambda item: (
            item.get("lineage_object_type") != "LineagePath",
            -float(item.get("smoke_candidate_score", 0.0)),
            item["lineage_object_id"],
        )
    )
    excluded_smoke.sort(
        key=lambda item: (
            len(item.get("smoke_eligibility_exclusion_reasons", [])),
            -float(item.get("modeling_candidate_score", 0.0)),
            item["lineage_object_id"],
        )
    )
    near_misses = excluded_smoke[:10]
    return {
        "selection_model": "smoke_eligible_modeling_lineage_object_v1",
        "filters": smoke_filters,
        "bounded_modeling_candidate_count": modeling_payload.get("modeling_candidate_count", 0),
        "smoke_eligible_modeling_candidate_count": len(smoke_candidates),
        "smoke_eligible_modeling_lineage_objects": smoke_candidates,
        "smoke_ineligible_modeling_lineage_objects": excluded_smoke,
        "top_smoke_near_misses": near_misses,
        "warnings": [
            "Smoke eligibility is a second selection tier on top of bounded modeling-candidate selection.",
            "Candidate generation should use selected_smoke_lineage_object by default.",
        ],
    }


def classify_biological_proof_of_principle_candidates(
    ranked_payload: dict[str, Any],
    *,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    filters = dict(
        DEFAULT_BIOLOGICAL_PROOF_FILTERS
        if filters is None
        else {**DEFAULT_BIOLOGICAL_PROOF_FILTERS, **filters}
    )
    ranked_items = ranked_payload.get("ranked_lineage_objects", [])
    candidates: list[dict[str, Any]] = []
    near_misses: list[dict[str, Any]] = []

    for item in ranked_items:
        features = item.get("lineage_object_features", {})
        event_count = int(features.get("event_count", 0))
        graph_depth = int(features.get("event_graph_depth", 0))
        phenotype_count = int(features.get("phenotype_observation_count", 0))
        terminal_support = int(features.get("terminal_perspective_support", 0))
        root_count = int(features.get("root_count", 0))
        endpoint_count = int(features.get("endpoint_count", 0))
        planned_max_time_min = _planned_max_time_min(features)
        calibration_candidates = summarize_calibration_candidates(item.get("passaging_records", []))
        top_calibration = calibration_candidates[0] if calibration_candidates else None
        matched_lineages, sibling_lineages = _matched_lineage_candidates(item, ranked_items)
        phase_plan = _build_phase_abstraction_plan(
            item,
            normalized_phase_duration_min=int(filters["normalized_phase_duration_min"]),
        )
        context_regimes = _context_regimes(item)
        technical_smoke_only = event_count <= 5 and float(features.get("phenotype_time_span_days", 0.0) or 0.0) < 1.0
        biologically_interpretable = (
            bool(item.get("selection_eligible", False))
            and root_count == 1
            and endpoint_count >= 1
            and event_count >= int(filters["min_event_count"])
            and phenotype_count >= int(filters["min_repeated_phenotype_observations"])
            and terminal_support >= int(filters["min_terminal_perspective_support"])
            and top_calibration is not None
        )
        phase_abstracted_modeling_eligible = (
            biologically_interpretable
            and not technical_smoke_only
            and top_calibration is not None
            and top_calibration["source"] != "Passaging.cellSize_um2"
            and (
                (
                    item.get("lineage_object_type") == "LineagePath"
                    and event_count <= int(filters["max_phase_abstracted_path_event_count"])
                )
                or (
                    item.get("lineage_object_type") == "RootedTrajectoryBundle"
                    and event_count <= int(filters["max_phase_abstracted_bundle_event_count"])
                    and graph_depth <= int(filters["max_phase_abstracted_bundle_depth"])
                    and "whole_cell_line_supertree" not in item.get("modeling_exclusion_reasons", [])
                )
            )
        )
        eligibility_reasons: list[str] = []
        if technical_smoke_only:
            eligibility_reasons.append("technical_smoke_only_candidate")
        if not bool(item.get("selection_eligible", False)) or root_count != 1 or endpoint_count < 1:
            eligibility_reasons.append("unclear_root_endpoint_structure")
        if event_count < int(filters["min_event_count"]):
            eligibility_reasons.append("too_few_events_for_biological_proof")
        if phenotype_count < int(filters["min_repeated_phenotype_observations"]):
            eligibility_reasons.append("insufficient_repeated_phenotype")
        if terminal_support < int(filters["min_terminal_perspective_support"]):
            eligibility_reasons.append("no_terminal_perspective")
        if top_calibration is None:
            eligibility_reasons.append("weak_calibration_observable")
        elif top_calibration["source"] == "Passaging.cellSize_um2":
            eligibility_reasons.append("cell_size_only_calibration")
        if item.get("lineage_object_type") == "LineagePath" and event_count > int(filters["max_phase_abstracted_path_event_count"]):
            eligibility_reasons.append("phase_graph_too_large")
        if item.get("lineage_object_type") == "RootedTrajectoryBundle" and (
            event_count > int(filters["max_phase_abstracted_bundle_event_count"])
            or graph_depth > int(filters["max_phase_abstracted_bundle_depth"])
            or "whole_cell_line_supertree" in item.get("modeling_exclusion_reasons", [])
        ):
            eligibility_reasons.append("phase_graph_too_large")

        annotated = {
            **item,
            "global_lineage_object_category": "global_lineage_object",
            "raw_time_simulation_eligible": (
                planned_max_time_min <= int(DEFAULT_SMOKE_FILTERS["max_planned_max_time_min"])
                and event_count <= int(DEFAULT_SMOKE_FILTERS["max_event_count"])
                and graph_depth <= int(DEFAULT_SMOKE_FILTERS["max_graph_depth"])
            ),
            "biologically_interpretable": biologically_interpretable,
            "phase_abstracted_modeling_eligible": phase_abstracted_modeling_eligible,
            "technical_smoke_only_candidate": technical_smoke_only,
            "planned_max_time_min": planned_max_time_min,
            "calibration_candidates": calibration_candidates,
            "top_calibration_observable": top_calibration,
            "context_regimes": context_regimes,
            "context_regime_count": len(context_regimes),
            "matched_lineage_candidates": matched_lineages,
            "sibling_lineage_candidates": sibling_lineages,
            "phase_abstraction_plan": phase_plan,
            "phase_abstraction_summary": {
                "phase_count": phase_plan["phase_count"],
                "passage_interval_count": phase_plan["passage_interval_count"],
                "media_stressor_regime_count": len(context_regimes),
                "simulated_total_duration_min": phase_plan["simulated_total_duration_min"],
                "mapping_policy": phase_plan["mapping_policy"],
            },
            "suggested_phase_mapping": (
                f"Normalize each primary lineage interval to {phase_plan['normalized_phase_duration_min']} simulated minutes; "
                "preserve event order and context transitions; calibrate or validate at phase boundaries using observed phenotype values."
            ),
            "suggested_biological_question": _suggested_biological_question(item, matched_lineages),
            "recommended_modeling_form": _recommended_modeling_form(item, matched_lineages),
            "biological_proof_exclusion_reasons": eligibility_reasons,
        }
        annotated["biological_candidate_score"] = _biological_candidate_score(annotated)
        if phase_abstracted_modeling_eligible:
            candidates.append(annotated)
        else:
            near_misses.append(annotated)

    candidates.sort(
        key=lambda item: (
            item.get("recommended_modeling_form") != "matched LineagePath pair",
            item.get("lineage_object_type") != "LineagePath",
            -float(item.get("biological_candidate_score", 0.0)),
            item["lineage_object_id"],
        )
    )
    near_misses.sort(
        key=lambda item: (
            len(item.get("biological_proof_exclusion_reasons", [])),
            -float(item.get("biological_candidate_score", 0.0)),
            item["lineage_object_id"],
        )
    )
    return {
        "selection_model": "biological_proof_of_principle_candidate_v1",
        "filters": filters,
        "global_lineage_object_count": len(ranked_items),
        "biological_proof_of_principle_candidate_count": len(candidates),
        "biological_proof_of_principle_candidates": candidates,
        "top_biological_proof_near_misses": near_misses[:20],
        "warnings": [
            "Raw elapsed clock time is not used as a sole rejection criterion for biological proof-of-principle candidates.",
            "Phase abstraction preserves event order and provenance while avoiding literal simulation of idle calendar time.",
            "Technical smoke-test objects remain separate from biological proof-of-principle candidates.",
        ],
    }


def classify_modeling_candidates_for_smoke_from_file(
    path: str | Path,
    *,
    smoke_filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return classify_modeling_candidates_for_smoke(json.loads(Path(path).read_text()), smoke_filters=smoke_filters)


def classify_lineage_objects_for_modeling_from_file(
    path: str | Path,
    *,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return classify_lineage_objects_for_modeling(json.loads(Path(path).read_text()), filters=filters)


def classify_biological_proof_of_principle_candidates_from_file(
    path: str | Path,
    *,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return classify_biological_proof_of_principle_candidates(json.loads(Path(path).read_text()), filters=filters)


def _excluded_parent_objects(selected: dict[str, Any], excluded_payload: dict[str, Any]) -> list[dict[str, Any]]:
    selected_event_ids = {
        str(event_id)
        for event_id in selected.get("lineage_path_event_ids", []) + selected.get("rooted_subtree_event_ids", [])
    }
    parents: list[dict[str, Any]] = []
    for item in excluded_payload.get("excluded_lineage_objects", []):
        item_event_ids = {
            str(event_id)
            for event_id in item.get("lineage_path_event_ids", []) + item.get("rooted_subtree_event_ids", [])
        }
        if selected_event_ids and selected_event_ids.issubset(item_event_ids):
            parents.append(
                {
                    "lineage_object_id": item["lineage_object_id"],
                    "lineage_object_type": item["lineage_object_type"],
                    "event_count": item.get("lineage_object_features", {}).get("event_count"),
                    "event_graph_depth": item.get("lineage_object_features", {}).get("event_graph_depth"),
                    "phenotype_time_span_days": item.get("lineage_object_features", {}).get("phenotype_time_span_days"),
                    "modeling_exclusion_reasons": item.get("modeling_exclusion_reasons", []),
                }
            )
    parents.sort(key=lambda item: (-(item["event_count"] or 0), item["lineage_object_id"]))
    return parents[:5]


def select_modeling_lineage_object(payload: dict[str, Any]) -> dict[str, Any]:
    candidates = payload.get("modeling_candidate_lineage_objects", [])
    if not candidates:
        raise ValueError("No bounded modeling-candidate lineage objects found")
    top = candidates[0]
    top_score = top["modeling_candidate_score"]
    ties = [item["lineage_object_id"] for item in candidates if item.get("modeling_candidate_score") == top_score]
    return {
        "selected_lineage_object_id": top["lineage_object_id"],
        "selected_lineage_object_type": top["lineage_object_type"],
        "modeling_candidate_score": top_score,
        "selection_policy": "Highest-ranked bounded modeling candidate wins; larger excluded parent objects are retained for provenance.",
        "ties_at_top_score": ties,
        "selected_record": {
            **top,
            "excluded_parent_objects": _excluded_parent_objects(top, payload),
        },
    }


def select_smoke_lineage_object(payload: dict[str, Any]) -> dict[str, Any]:
    candidates = payload.get("smoke_eligible_modeling_lineage_objects", [])
    if not candidates:
        raise ValueError("No smoke-eligible lineage objects found")
    top = candidates[0]
    top_score = top["smoke_candidate_score"]
    ties = [item["lineage_object_id"] for item in candidates if item.get("smoke_candidate_score") == top_score]
    return {
        "selected_lineage_object_id": top["lineage_object_id"],
        "selected_lineage_object_type": top["lineage_object_type"],
        "smoke_candidate_score": top_score,
        "selection_policy": "Highest-ranked smoke-eligible lineage object wins; no runtime override is applied by default.",
        "ties_at_top_score": ties,
        "selected_record": top,
    }


def select_biological_proof_of_principle_candidate(payload: dict[str, Any]) -> dict[str, Any]:
    candidates = payload.get("biological_proof_of_principle_candidates", [])
    if not candidates:
        raise ValueError("No biological proof-of-principle candidates found")
    top = candidates[0]
    top_score = top["biological_candidate_score"]
    ties = [item["lineage_object_id"] for item in candidates if item.get("biological_candidate_score") == top_score]
    return {
        "selected_lineage_object_id": top["lineage_object_id"],
        "selected_lineage_object_type": top["lineage_object_type"],
        "biological_candidate_score": top_score,
        "selection_policy": (
            "Select the strongest biologically interpretable, phase-abstractable lineage object; "
            "raw elapsed time alone does not exclude a candidate."
        ),
        "ties_at_top_score": ties,
        "selected_record": top,
    }


def select_modeling_lineage_object_from_file(path: str | Path) -> dict[str, Any]:
    return select_modeling_lineage_object(json.loads(Path(path).read_text()))


def select_smoke_lineage_object_from_file(path: str | Path) -> dict[str, Any]:
    return select_smoke_lineage_object(json.loads(Path(path).read_text()))


def select_biological_proof_of_principle_candidate_from_file(path: str | Path) -> dict[str, Any]:
    return select_biological_proof_of_principle_candidate(json.loads(Path(path).read_text()))


def write_modeling_candidate_artifacts(output_dir: str | Path, payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    write_json(output_dir / "modeling_candidate_lineage_objects.json", payload)
    write_json(
        output_dir / "excluded_lineage_objects.json",
        {
            "selection_model": payload["selection_model"],
            "filters": payload["filters"],
            "excluded_lineage_object_count": payload["excluded_lineage_object_count"],
            "excluded_lineage_objects": payload["excluded_lineage_objects"],
        },
    )

    candidate_lines = [
        "# Modeling Candidate Lineage Objects",
        "",
        f"- Candidate count: `{payload['modeling_candidate_count']}`",
        f"- Excluded count: `{payload['excluded_lineage_object_count']}`",
        "",
        "## Top 10 Bounded Candidates",
        "",
    ]
    for item in payload.get("modeling_candidate_lineage_objects", [])[:10]:
        features = item.get("lineage_object_features", {})
        candidate_lines.append(
            f"- `{item['lineage_object_id']}` type `{item['lineage_object_type']}` score `{item['modeling_candidate_score']}` events `{features.get('event_count')}` depth `{features.get('event_graph_depth')}` span_days `{features.get('phenotype_time_span_days')}` terminal_perspective `{features.get('terminal_perspective_support')}`"
        )
    write_markdown(output_dir / "modeling_candidate_lineage_objects.md", "\n".join(candidate_lines) + "\n")

    excluded_lines = [
        "# Excluded Lineage Objects",
        "",
        f"- Excluded count: `{payload['excluded_lineage_object_count']}`",
        "",
        "## Top Exclusions",
        "",
    ]
    for item in payload.get("excluded_lineage_objects", [])[:20]:
        excluded_lines.append(
            f"- `{item['lineage_object_id']}`: {', '.join(item.get('modeling_exclusion_reasons', []))}"
        )
    write_markdown(output_dir / "excluded_lineage_objects.md", "\n".join(excluded_lines) + "\n")


def write_smoke_candidate_artifacts(output_dir: str | Path, payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    write_json(output_dir / "smoke_eligible_modeling_lineage_objects.json", payload)
    lines = [
        "# Smoke-Eligible Modeling Lineage Objects",
        "",
        f"- Smoke-eligible count: `{payload['smoke_eligible_modeling_candidate_count']}`",
        f"- Bounded modeling candidate count: `{payload['bounded_modeling_candidate_count']}`",
        "",
        "## Top Smoke-Eligible Candidates",
        "",
    ]
    for item in payload.get("smoke_eligible_modeling_lineage_objects", [])[:10]:
        features = item.get("lineage_object_features", {})
        calib = item.get("top_calibration_observable") or {}
        lines.append(
            f"- `{item['lineage_object_id']}` type `{item['lineage_object_type']}` smoke_score `{item['smoke_candidate_score']}` events `{features.get('event_count')}` depth `{features.get('event_graph_depth')}` planned_max `{item.get('planned_max_time_min')}` calibration `{calib.get('source')}`"
        )
    if payload.get("top_smoke_near_misses"):
        lines.extend(["", "## Top Near Misses", ""])
        for item in payload["top_smoke_near_misses"]:
            lines.append(
                f"- `{item['lineage_object_id']}`: {', '.join(item.get('smoke_eligibility_exclusion_reasons', []))}"
            )
    write_markdown(output_dir / "smoke_eligible_modeling_lineage_objects.md", "\n".join(lines) + "\n")


def write_biological_proof_of_principle_candidate_artifacts(output_dir: str | Path, payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    write_json(output_dir / "biological_proof_of_principle_candidates.json", payload)
    lines = [
        "# Biological Proof-of-Principle Candidates",
        "",
        f"- Candidate count: `{payload['biological_proof_of_principle_candidate_count']}`",
        f"- Global lineage object count: `{payload['global_lineage_object_count']}`",
        "",
        "## Top Biological Candidates",
        "",
    ]
    for item in payload.get("biological_proof_of_principle_candidates", [])[:10]:
        features = item.get("lineage_object_features", {})
        lines.append(
            f"- `{item['lineage_object_id']}` type `{item['lineage_object_type']}` score `{item['biological_candidate_score']}` "
            f"events `{features.get('event_count')}` depth `{features.get('event_graph_depth')}` "
            f"raw_span_days `{features.get('phenotype_time_span_days')}` matched `{len(item.get('matched_lineage_candidates', []))}` "
            f"phase_count `{item.get('phase_abstraction_summary', {}).get('phase_count')}`"
        )
    if payload.get("top_biological_proof_near_misses"):
        lines.extend(["", "## Near Misses", ""])
        for item in payload["top_biological_proof_near_misses"][:10]:
            lines.append(
                f"- `{item['lineage_object_id']}`: {', '.join(item.get('biological_proof_exclusion_reasons', []))}"
            )
    write_markdown(output_dir / "biological_proof_of_principle_candidates.md", "\n".join(lines) + "\n")


def write_selected_modeling_lineage_object(output_dir: str | Path, selection_payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    record = {
        "selected_lineage_object_id": selection_payload["selected_lineage_object_id"],
        "selected_lineage_object_type": selection_payload["selected_lineage_object_type"],
        "selection_summary": {
            "modeling_candidate_score": selection_payload["modeling_candidate_score"],
            "ties_at_top_score": selection_payload["ties_at_top_score"],
            "selection_policy": selection_payload["selection_policy"],
        },
        **selection_payload["selected_record"],
    }
    write_json(output_dir / "selected_modeling_lineage_object.json", record)

    features = record.get("lineage_object_features", {})
    lines = [
        "# Selected Modeling Lineage Object",
        "",
        f"- Selected lineage object: `{record['selected_lineage_object_id']}`",
        f"- Type: `{record['selected_lineage_object_type']}`",
        f"- Root event: `{record.get('root_event_id')}`",
        f"- Endpoint event(s): `{', '.join(record.get('endpoint_event_ids', []))}`",
        f"- Event count: `{features.get('event_count')}`",
        f"- Path length: `{features.get('lineage_path_length')}`",
        f"- Graph depth: `{features.get('event_graph_depth')}`",
        f"- Time span days: `{features.get('phenotype_time_span_days')}`",
        f"- Context regimes: `{record.get('context_regime_count')}`",
        f"- Phenotype observation count: `{features.get('phenotype_observation_count')}`",
        f"- Terminal Perspective support: `{features.get('terminal_perspective_support')}`",
        "",
        "## Selection reasons",
        "",
    ]
    for reason in record.get("lineage_object_score_reasons", []):
        lines.append(f"- {reason}")
    lines.extend(["", "## Larger excluded parent objects", ""])
    for parent in record.get("excluded_parent_objects", []):
        lines.append(
            f"- `{parent['lineage_object_id']}` excluded for: {', '.join(parent['modeling_exclusion_reasons'])}"
        )
    write_markdown(output_dir / "selected_modeling_lineage_object.md", "\n".join(lines) + "\n")


def write_selected_smoke_lineage_object(output_dir: str | Path, selection_payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    record = {
        "selected_lineage_object_id": selection_payload["selected_lineage_object_id"],
        "selected_lineage_object_type": selection_payload["selected_lineage_object_type"],
        "selection_summary": {
            "smoke_candidate_score": selection_payload["smoke_candidate_score"],
            "ties_at_top_score": selection_payload["ties_at_top_score"],
            "selection_policy": selection_payload["selection_policy"],
        },
        **selection_payload["selected_record"],
    }
    write_json(output_dir / "selected_smoke_lineage_object.json", record)
    features = record.get("lineage_object_features", {})
    calib = record.get("top_calibration_observable") or {}
    lines = [
        "# Selected Smoke Lineage Object",
        "",
        f"- Selected lineage object: `{record['selected_lineage_object_id']}`",
        f"- Type: `{record['selected_lineage_object_type']}`",
        f"- Root event: `{record.get('root_event_id')}`",
        f"- Endpoint event(s): `{', '.join(record.get('endpoint_event_ids', []))}`",
        f"- Event count: `{features.get('event_count')}`",
        f"- Path length: `{features.get('lineage_path_length')}`",
        f"- Graph depth: `{features.get('event_graph_depth')}`",
        f"- Time span days: `{features.get('phenotype_time_span_days')}`",
        f"- Planned max time min: `{record.get('planned_max_time_min')}`",
        f"- Terminal Perspective support: `{features.get('terminal_perspective_support')}`",
        f"- Selected calibration observable: `{calib.get('source')}`",
    ]
    write_markdown(output_dir / "selected_smoke_lineage_object.md", "\n".join(lines) + "\n")


def write_selected_biological_proof_of_principle_candidate(
    output_dir: str | Path,
    selection_payload: dict[str, Any],
) -> None:
    output_dir = Path(output_dir)
    record = {
        "selected_lineage_object_id": selection_payload["selected_lineage_object_id"],
        "selected_lineage_object_type": selection_payload["selected_lineage_object_type"],
        "selection_summary": {
            "biological_candidate_score": selection_payload["biological_candidate_score"],
            "ties_at_top_score": selection_payload["ties_at_top_score"],
            "selection_policy": selection_payload["selection_policy"],
        },
        **selection_payload["selected_record"],
    }
    write_json(output_dir / "selected_biological_proof_of_principle_candidate.json", record)
    features = record.get("lineage_object_features", {})
    phase_summary = record.get("phase_abstraction_summary", {})
    lines = [
        "# Selected Biological Proof-of-Principle Candidate",
        "",
        f"- Selected lineage object: `{record['selected_lineage_object_id']}`",
        f"- Type: `{record['selected_lineage_object_type']}`",
        f"- Recommended modeling form: `{record.get('recommended_modeling_form')}`",
        f"- Root event: `{record.get('root_event_id')}`",
        f"- Endpoint event(s): `{', '.join(record.get('endpoint_event_ids', []))}`",
        f"- Event count: `{features.get('event_count')}`",
        f"- Path length: `{features.get('lineage_path_length')}`",
        f"- Graph depth: `{features.get('event_graph_depth')}`",
        f"- Raw elapsed time days: `{features.get('phenotype_time_span_days')}`",
        f"- Planned raw-time runtime min: `{record.get('planned_max_time_min')}`",
        f"- Raw-time simulation eligible: `{record.get('raw_time_simulation_eligible')}`",
        f"- Phase-abstracted modeling eligible: `{record.get('phase_abstracted_modeling_eligible')}`",
        f"- Biologically interpretable: `{record.get('biologically_interpretable')}`",
        f"- Phase count: `{phase_summary.get('phase_count')}`",
        f"- Simulated phase-abstracted duration min: `{phase_summary.get('simulated_total_duration_min')}`",
        f"- Terminal Perspective support: `{features.get('terminal_perspective_support')}`",
        "",
        "## Suggested biological question",
        "",
        f"- {record.get('suggested_biological_question')}",
        "",
        "## Matched / sibling structure",
        "",
        f"- Matched lineage candidates: `{', '.join(record.get('matched_lineage_candidates', []))}`",
        f"- Sibling lineage candidates: `{', '.join(record.get('sibling_lineage_candidates', []))}`",
        "",
        "## Suggested phase mapping",
        "",
        f"- {record.get('suggested_phase_mapping')}",
    ]
    write_markdown(output_dir / "selected_biological_proof_of_principle_candidate.md", "\n".join(lines) + "\n")
