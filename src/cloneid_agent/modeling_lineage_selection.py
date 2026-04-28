"""Bounded modeling-candidate selection from globally discovered lineage objects."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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


def classify_lineage_objects_for_modeling_from_file(
    path: str | Path,
    *,
    filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return classify_lineage_objects_for_modeling(json.loads(Path(path).read_text()), filters=filters)


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


def select_modeling_lineage_object_from_file(path: str | Path) -> dict[str, Any]:
    return select_modeling_lineage_object(json.loads(Path(path).read_text()))


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
