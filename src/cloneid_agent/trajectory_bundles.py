"""Deterministic lineage-object discovery over mock or cached CLONEID-like records."""

from __future__ import annotations

import json
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any

from .run_io import write_json, write_markdown


SEGMENT_CONTEXT_FIELDS = ("cellLine", "growthType", "passage", "media", "flask")
TRANSITION_FIELDS = ("growthType", "passage", "media", "flask")
TRAVERSAL_POLICY = {
    "primary_backbone": "passaged_from_id1",
    "secondary_edges": "passaged_from_id2_recorded_not_traversed",
    "context_grouping_role": "annotation_only",
    "perspective_attachment": "Perspective.origin",
    "identity_attachment": "secondary_inferred_support",
}


def _segment_value(value: Any) -> str:
    if value is None or value == "":
        return "NA"
    return str(value)


def _parse_event_datetime(value: str | None) -> datetime | None:
    if value in (None, ""):
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            continue
    raise ValueError(f"Unsupported date format: {value!r}")


def dataset_id_from_passaging_record(record: dict[str, Any]) -> str:
    return "__".join(_segment_value(record.get(field)) for field in SEGMENT_CONTEXT_FIELDS)


def group_candidate_segments(passaging_records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for record in passaging_records:
        dataset_id = dataset_id_from_passaging_record(record)
        bucket = grouped.setdefault(
            dataset_id,
            {
                "dataset_id": dataset_id,
                "context": {field: record.get(field) for field in SEGMENT_CONTEXT_FIELDS},
                "event_ids": [],
                "event_count": 0,
                "phenotype_observation_count": 0,
                "date_min": None,
                "date_max": None,
            },
        )
        bucket["event_ids"].append(record["id"])
        bucket["event_count"] += 1
        if any(record.get(field) is not None for field in ("cellCount", "correctedCount", "areaOccupied_um2", "cellSize_um2")):
            bucket["phenotype_observation_count"] += 1
        date_value = record.get("date")
        if date_value is not None:
            if bucket["date_min"] is None or date_value < bucket["date_min"]:
                bucket["date_min"] = date_value
            if bucket["date_max"] is None or date_value > bucket["date_max"]:
                bucket["date_max"] = date_value
    return grouped


def _build_primary_parent_map(passaging_records: list[dict[str, Any]]) -> dict[str, str]:
    parent_map: dict[str, str] = {}
    for record in passaging_records:
        child_id = str(record["id"])
        parent_id = record.get("passaged_from_id1")
        if parent_id not in (None, ""):
            parent_map[child_id] = str(parent_id)
    return parent_map


def _build_primary_children_map(passaging_records: list[dict[str, Any]]) -> dict[str, list[str]]:
    children: dict[str, list[str]] = defaultdict(list)
    for record in passaging_records:
        parent_id = record.get("passaged_from_id1")
        if parent_id not in (None, ""):
            children[str(parent_id)].append(str(record["id"]))
    return children


def _build_secondary_parent_map(passaging_records: list[dict[str, Any]]) -> dict[str, str]:
    parent_map: dict[str, str] = {}
    for record in passaging_records:
        child_id = str(record["id"])
        parent_id = record.get("passaged_from_id2")
        if parent_id not in (None, ""):
            parent_map[child_id] = str(parent_id)
    return parent_map


def _walk_primary_ancestors(
    seed_event_ids: set[str],
    passaging_by_id: dict[str, dict[str, Any]],
    primary_parent_map: dict[str, str],
    *,
    max_upstream_depth: int,
    stop_on_cell_line_change: bool,
) -> tuple[set[str], dict[str, str], list[dict[str, Any]]]:
    ancestors: set[str] = set(seed_event_ids)
    root_by_seed: dict[str, str] = {}
    excluded_neighbors: list[dict[str, Any]] = []

    for seed_event_id in seed_event_ids:
        current_id = seed_event_id
        current_depth = 0
        seed_cell_line = str(passaging_by_id[seed_event_id].get("cellLine"))
        while current_id in primary_parent_map and current_depth < max_upstream_depth:
            parent_id = primary_parent_map[current_id]
            parent_record = passaging_by_id.get(parent_id)
            if parent_record is None:
                excluded_neighbors.append(
                    {"event_id": parent_id, "reason": "missing primary parent record", "direction": "upstream"}
                )
                break
            if stop_on_cell_line_change and str(parent_record.get("cellLine")) != seed_cell_line:
                excluded_neighbors.append(
                    {"event_id": parent_id, "reason": "cell line change", "direction": "upstream"}
                )
                break
            ancestors.add(parent_id)
            current_id = parent_id
            current_depth += 1
        root_by_seed[seed_event_id] = current_id

    return ancestors, root_by_seed, excluded_neighbors


def _collect_primary_descendants(
    root_event_ids: set[str],
    passaging_by_id: dict[str, dict[str, Any]],
    primary_children_map: dict[str, list[str]],
    *,
    max_downstream_depth: int,
    stop_on_cell_line_change: bool,
) -> tuple[set[str], list[dict[str, Any]], list[dict[str, Any]]]:
    if not root_event_ids:
        return set(), [], []

    root_cell_lines = {
        str(passaging_by_id[event_id].get("cellLine"))
        for event_id in root_event_ids
        if event_id in passaging_by_id
    }
    connected: set[str] = set()
    expansions: list[dict[str, Any]] = []
    excluded_neighbors: list[dict[str, Any]] = []
    queue = deque((event_id, 0) for event_id in sorted(root_event_ids))

    while queue:
        event_id, depth = queue.popleft()
        if event_id in connected:
            continue
        connected.add(event_id)
        for child_id in primary_children_map.get(event_id, []):
            child_record = passaging_by_id.get(child_id)
            if child_record is None:
                excluded_neighbors.append(
                    {"event_id": child_id, "reason": "missing primary child record", "direction": "downstream"}
                )
                continue
            if stop_on_cell_line_change and str(child_record.get("cellLine")) not in root_cell_lines:
                excluded_neighbors.append(
                    {"event_id": child_id, "reason": "cell line change", "direction": "downstream"}
                )
                continue
            if depth >= max_downstream_depth:
                excluded_neighbors.append(
                    {"event_id": child_id, "reason": "max downstream depth reached", "direction": "downstream"}
                )
                continue
            expansions.append({"event_id": child_id, "direction": "downstream", "depth": depth + 1})
            queue.append((child_id, depth + 1))

    return connected, expansions, excluded_neighbors


def _primary_roots_within_event_ids(
    event_ids: set[str],
    primary_parent_map: dict[str, str],
) -> list[str]:
    roots = sorted(event_id for event_id in event_ids if primary_parent_map.get(event_id) not in event_ids)
    return roots


def _primary_leaf_event_ids(
    event_ids: set[str],
    primary_children_map: dict[str, list[str]],
) -> list[str]:
    return sorted(event_id for event_id in event_ids if not any(child in event_ids for child in primary_children_map.get(event_id, [])))


def _attach_perspectives(event_ids: set[str], perspective_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    linked = []
    event_ids_str = {str(event_id) for event_id in event_ids}
    for record in perspective_records:
        if str(record.get("origin")) in event_ids_str:
            linked.append({**record, "attachment_role": "terminal_or_event_linked_perspective"})
    return linked


def _attach_identities(perspective_records: list[dict[str, Any]], identity_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not perspective_records:
        return []

    perspective_ids = {str(record.get("cloneID")) for record in perspective_records if record.get("cloneID") is not None}
    perspective_sample_sources = {
        str(record.get("sampleSource"))
        for record in perspective_records
        if record.get("sampleSource") not in (None, "")
    }
    linked: list[dict[str, Any]] = []
    perspective_fields = (
        "GenomePerspective",
        "TranscriptomePerspective",
        "ExomePerspective",
        "KaryotypePerspective",
    )
    for record in identity_records:
        matched_clone_links = [field for field in perspective_fields if str(record.get(field)) in perspective_ids]
        sample_source_match = str(record.get("sampleSource")) in perspective_sample_sources
        if matched_clone_links or sample_source_match:
            linked.append(
                {
                    **record,
                    "attachment_role": "inferred_secondary_identity_support",
                    "identity_linkage": {
                        "matched_perspective_fields": matched_clone_links,
                        "sample_source_match": sample_source_match,
                    },
                }
            )
    return linked


def _build_primary_lineage_edges(
    event_ids: set[str],
    passaging_by_id: dict[str, dict[str, Any]],
    primary_parent_map: dict[str, str],
) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for child_id in sorted(event_ids):
        parent_id = primary_parent_map.get(child_id)
        if parent_id is None or parent_id not in event_ids:
            continue
        parent = passaging_by_id[parent_id]
        child = passaging_by_id[child_id]
        edges.append(
            {
                "parent_event_id": parent_id,
                "child_event_id": child_id,
                "link_field": "passaged_from_id1",
                "parent_date": parent.get("date"),
                "child_date": child.get("date"),
                "parent_segment_id": dataset_id_from_passaging_record(parent),
                "child_segment_id": dataset_id_from_passaging_record(child),
            }
        )
    return edges


def _build_secondary_lineage_edges(
    event_ids: set[str],
    passaging_by_id: dict[str, dict[str, Any]],
    secondary_parent_map: dict[str, str],
) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for child_id in sorted(event_ids):
        parent_id = secondary_parent_map.get(child_id)
        if parent_id is None:
            continue
        child = passaging_by_id.get(child_id)
        parent = passaging_by_id.get(parent_id)
        edges.append(
            {
                "parent_event_id": parent_id,
                "child_event_id": child_id,
                "link_field": "passaged_from_id2",
                "parent_in_rooted_subtree": parent_id in event_ids,
                "child_in_rooted_subtree": child_id in event_ids,
                "parent_date": None if parent is None else parent.get("date"),
                "child_date": None if child is None else child.get("date"),
                "parent_segment_id": None if parent is None else dataset_id_from_passaging_record(parent),
                "child_segment_id": None if child is None else dataset_id_from_passaging_record(child),
            }
        )
    return edges


def _record_context_transitions_from_edges(
    edges: list[dict[str, Any]],
    passaging_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    transitions: list[dict[str, Any]] = []
    for edge in edges:
        parent = passaging_by_id.get(edge["parent_event_id"])
        child = passaging_by_id.get(edge["child_event_id"])
        if parent is None or child is None:
            continue
        for field in TRANSITION_FIELDS:
            parent_value = parent.get(field)
            child_value = child.get(field)
            if parent_value != child_value:
                transitions.append(
                    {
                        "parent_event_id": edge["parent_event_id"],
                        "child_event_id": edge["child_event_id"],
                        "link_field": edge["link_field"],
                        "field": field,
                        "from_value": parent_value,
                        "to_value": child_value,
                        "parent_segment_id": edge.get("parent_segment_id"),
                        "child_segment_id": edge.get("child_segment_id"),
                    }
                )
    return transitions


def _build_segment_connections(
    primary_lineage_edges: list[dict[str, Any]],
    context_transitions_primary: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    transition_map: dict[tuple[str, str, str], dict[str, Any]] = {}
    for transition in context_transitions_primary:
        transition_map[(transition["parent_event_id"], transition["child_event_id"], transition["field"])] = transition

    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for edge in primary_lineage_edges:
        parent_segment_id = edge["parent_segment_id"]
        child_segment_id = edge["child_segment_id"]
        if parent_segment_id == child_segment_id:
            continue
        key = (parent_segment_id, child_segment_id)
        bucket = grouped.setdefault(
            key,
            {
                "parent_segment_id": parent_segment_id,
                "child_segment_id": child_segment_id,
                "primary_lineage_edges": [],
                "context_changes": [],
            },
        )
        bucket["primary_lineage_edges"].append(
            {
                "parent_event_id": edge["parent_event_id"],
                "child_event_id": edge["child_event_id"],
                "link_field": edge["link_field"],
                "parent_date": edge.get("parent_date"),
                "child_date": edge.get("child_date"),
            }
        )
        for field in TRANSITION_FIELDS:
            transition = transition_map.get((edge["parent_event_id"], edge["child_event_id"], field))
            if transition is not None:
                bucket["context_changes"].append(
                    {
                        "field": field,
                        "from_value": transition["from_value"],
                        "to_value": transition["to_value"],
                    }
                )

    connections = list(grouped.values())
    connections.sort(key=lambda item: (item["parent_segment_id"], item["child_segment_id"]))
    return connections


def _recover_primary_lineage_path(
    endpoint_event_id: str,
    primary_parent_map: dict[str, str],
    rooted_subtree_event_ids: set[str],
) -> list[str]:
    path = [endpoint_event_id]
    current_id = endpoint_event_id
    while current_id in primary_parent_map:
        parent_id = primary_parent_map[current_id]
        if parent_id not in rooted_subtree_event_ids:
            break
        path.append(parent_id)
        current_id = parent_id
    path.reverse()
    return path


def _score_endpoint(
    event_id: str,
    passaging_by_id: dict[str, dict[str, Any]],
    perspectives_by_origin: dict[str, list[dict[str, Any]]],
) -> tuple[int, datetime | None, str]:
    record = passaging_by_id[event_id]
    return (
        len(perspectives_by_origin.get(event_id, [])),
        _parse_event_datetime(record.get("date")),
        event_id,
    )


def _graph_distance_from_roots(primary_roots: list[str], primary_children_map: dict[str, list[str]], event_ids: set[str]) -> int:
    if not primary_roots:
        return 0

    max_depth = 0
    queue = deque((event_id, 0) for event_id in primary_roots)
    seen: set[str] = set()
    while queue:
        event_id, depth = queue.popleft()
        if event_id in seen:
            continue
        seen.add(event_id)
        max_depth = max(max_depth, depth)
        for child_id in primary_children_map.get(event_id, []):
            if child_id in event_ids:
                queue.append((child_id, depth + 1))
    return max_depth


def trajectory_bundle_features(bundle_payload: dict[str, Any]) -> dict[str, Any]:
    passaging_records = bundle_payload["passaging_records"]
    event_ids = {str(record["id"]) for record in passaging_records}
    passaging_by_id = {str(record["id"]): record for record in passaging_records}
    if bundle_payload.get("primary_lineage_edges"):
        primary_lineage_edges = bundle_payload["primary_lineage_edges"]
    else:
        primary_parent_map = _build_primary_parent_map(passaging_records)
        primary_lineage_edges = _build_primary_lineage_edges(event_ids, passaging_by_id, primary_parent_map)
    context_transitions_primary = bundle_payload.get("context_transitions_primary", bundle_payload.get("context_transitions", []))
    perspective_records = bundle_payload["perspective_records"]
    identity_records = bundle_payload.get("identity_support_records", bundle_payload.get("identity_records", []))
    connected_segments = bundle_payload.get("candidate_segments_covered", bundle_payload.get("connected_candidate_segments", []))

    phenotype_count = sum(
        1
        for record in passaging_records
        if any(record.get(field) is not None for field in ("cellCount", "correctedCount", "areaOccupied_um2", "cellSize_um2"))
    )
    distinct_dates = sorted({record.get("date") for record in passaging_records if record.get("date") is not None})
    primary_roots = bundle_payload.get("rooted_subtree_root_event_ids") or _primary_roots_within_event_ids(
        event_ids,
        _build_primary_parent_map(passaging_records),
    )
    primary_children_map: dict[str, list[str]] = defaultdict(list)
    for edge in primary_lineage_edges:
        primary_children_map[edge["parent_event_id"]].append(edge["child_event_id"])
    leaf_ids = _primary_leaf_event_ids(event_ids, primary_children_map)
    bundle_complexity_penalty = max(0, len(passaging_records) - 25) + max(0, len(context_transitions_primary) - 10)
    event_graph_depth = _graph_distance_from_roots(primary_roots, primary_children_map, event_ids)
    branch_children = max((len(children) for children in primary_children_map.values()), default=0)

    return {
        "connected_segment_count": len(connected_segments),
        "event_graph_depth": event_graph_depth,
        "event_count": len(passaging_records),
        "transition_count": len(context_transitions_primary),
        "has_branching": branch_children > 1,
        "has_longitudinal_context_change": bool(context_transitions_primary),
        "phenotype_observation_count": phenotype_count,
        "phenotype_time_span_days": bundle_payload["phenotype_time_span_days"],
        "terminal_perspective_support": sum(1 for record in perspective_records if str(record.get("origin")) in leaf_ids),
        "identity_support_count": len(identity_records),
        "calibration_validation_split_possible": len(distinct_dates) >= 3 and len(perspective_records) >= 1,
        "trajectory_bundle_complexity_penalty": bundle_complexity_penalty,
        "root_event_count": len(primary_roots),
        "leaf_event_count": len(leaf_ids),
    }


def bundle_time_span_days(first_date: str, last_date: str) -> float:
    start = _parse_event_datetime(first_date)
    stop = _parse_event_datetime(last_date)
    if start is None or stop is None:
        return 0.0
    return round(max((stop - start).total_seconds() / 86400.0, 0.0), 3)


def discover_trajectory_bundle(
    *,
    seed_dataset_id: str,
    passaging_records: list[dict[str, Any]],
    perspective_records: list[dict[str, Any]] | None = None,
    identity_records: list[dict[str, Any]] | None = None,
    max_upstream_depth: int = 6,
    max_downstream_depth: int = 6,
    stop_on_cell_line_change: bool = True,
    include_secondary_in_traversal: bool = False,
) -> dict[str, Any]:
    perspective_records = perspective_records or []
    identity_records = identity_records or []
    segments = group_candidate_segments(passaging_records)
    if seed_dataset_id not in segments:
        raise ValueError(f"Seed dataset_id not found in passaging records: {seed_dataset_id}")

    passaging_by_id = {str(record["id"]): record for record in passaging_records}
    primary_parent_map = _build_primary_parent_map(passaging_records)
    primary_children_map = _build_primary_children_map(passaging_records)
    secondary_parent_map = _build_secondary_parent_map(passaging_records)

    seed_event_ids = {str(event_id) for event_id in segments[seed_dataset_id]["event_ids"]}
    ancestor_event_ids, root_by_seed, upstream_excluded = _walk_primary_ancestors(
        seed_event_ids,
        passaging_by_id,
        primary_parent_map,
        max_upstream_depth=max_upstream_depth,
        stop_on_cell_line_change=stop_on_cell_line_change,
    )
    rooted_subtree_root_event_ids = sorted(set(root_by_seed.values()))
    rooted_subtree_event_ids, expansions, downstream_excluded = _collect_primary_descendants(
        set(rooted_subtree_root_event_ids),
        passaging_by_id,
        primary_children_map,
        max_downstream_depth=max_downstream_depth,
        stop_on_cell_line_change=stop_on_cell_line_change,
    )
    rooted_subtree_event_ids.update(ancestor_event_ids)

    ordered_records = sorted(
        (passaging_by_id[event_id] for event_id in rooted_subtree_event_ids),
        key=lambda record: (str(record.get("date")), str(record["id"])),
    )
    connected_segment_ids = sorted({dataset_id_from_passaging_record(record) for record in ordered_records})
    connected_segment_records = [segments[dataset_id] for dataset_id in connected_segment_ids]

    primary_lineage_edges = _build_primary_lineage_edges(rooted_subtree_event_ids, passaging_by_id, primary_parent_map)
    secondary_lineage_edges = _build_secondary_lineage_edges(rooted_subtree_event_ids, passaging_by_id, secondary_parent_map)
    context_transitions_primary = _record_context_transitions_from_edges(primary_lineage_edges, passaging_by_id)
    context_transitions_secondary = _record_context_transitions_from_edges(
        [edge for edge in secondary_lineage_edges if edge["parent_event_id"] in passaging_by_id],
        passaging_by_id,
    )
    segment_connections = _build_segment_connections(primary_lineage_edges, context_transitions_primary)

    linked_perspectives = _attach_perspectives(rooted_subtree_event_ids, perspective_records)
    linked_identities = _attach_identities(linked_perspectives, identity_records)
    perspective_origin_event_ids = sorted({str(record.get("origin")) for record in linked_perspectives if record.get("origin") is not None})

    perspectives_by_origin: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in linked_perspectives:
        origin = record.get("origin")
        if origin is not None:
            perspectives_by_origin[str(origin)].append(record)

    primary_leaf_event_ids = _primary_leaf_event_ids(rooted_subtree_event_ids, primary_children_map)
    endpoint_event_ids = sorted({event_id for event_id in perspective_origin_event_ids if event_id in rooted_subtree_event_ids})
    if not endpoint_event_ids:
        endpoint_event_ids = primary_leaf_event_ids

    selected_endpoint_event_id = None
    lineage_path_event_ids: list[str] = []
    root_event_id = None
    if endpoint_event_ids:
        selected_endpoint_event_id = max(
            endpoint_event_ids,
            key=lambda event_id: _score_endpoint(event_id, passaging_by_id, perspectives_by_origin),
        )
        lineage_path_event_ids = _recover_primary_lineage_path(
            selected_endpoint_event_id,
            primary_parent_map,
            rooted_subtree_event_ids,
        )
        root_event_id = lineage_path_event_ids[0] if lineage_path_event_ids else None

    phenotype_dates = [record.get("date") for record in ordered_records if record.get("date") is not None]
    phenotype_time_span_days = 0.0
    if phenotype_dates:
        phenotype_time_span_days = 0.0 if len(phenotype_dates) < 2 else bundle_time_span_days(phenotype_dates[0], phenotype_dates[-1])

    bundle_payload = {
        "seed_candidate_segment_id": seed_dataset_id,
        "bundle_id": f"trajectory_bundle::{seed_dataset_id}",
        "bundle_role": "rooted_trajectory_bundle",
        "object_types": {
            "CandidateSegment": "local_context_bucket",
            "LineagePath": "single_ancestor_to_endpoint_path_via_passaged_from_id1",
            "RootedTrajectoryBundle": "descendants_of_root_event_via_passaged_from_id1",
        },
        "traversal_policy": {
            **TRAVERSAL_POLICY,
            "secondary_traversal_enabled": include_secondary_in_traversal,
        },
        "graph_expansion": {
            "max_upstream_depth_requested": max_upstream_depth,
            "max_downstream_depth_requested": max_downstream_depth,
            "max_upstream_depth_reached": max(
                (
                    len(_recover_primary_lineage_path(seed_event_id, primary_parent_map, ancestor_event_ids)) - 1
                    for seed_event_id in seed_event_ids
                ),
                default=0,
            ),
            "max_downstream_depth_reached": max(
                (item["depth"] for item in expansions if item["direction"] == "downstream"),
                default=0,
            ),
            "stop_on_cell_line_change": stop_on_cell_line_change,
            "secondary_traversal_enabled": include_secondary_in_traversal,
            "expansion_events": expansions,
            "excluded_neighbors": upstream_excluded + downstream_excluded,
        },
        "root_event_id": root_event_id,
        "rooted_subtree_root_event_ids": rooted_subtree_root_event_ids,
        "endpoint_event_ids": endpoint_event_ids,
        "selected_endpoint_event_id": selected_endpoint_event_id,
        "rooted_subtree_event_ids": sorted(rooted_subtree_event_ids),
        "lineage_path_event_ids": lineage_path_event_ids,
        "candidate_segments_covered": connected_segment_records,
        "connected_candidate_segments": connected_segment_records,
        "passaging_records": ordered_records,
        "primary_lineage_edges": primary_lineage_edges,
        "secondary_lineage_edges": secondary_lineage_edges,
        "lineage_edges": primary_lineage_edges,
        "segment_connections": segment_connections,
        "context_transitions_primary": context_transitions_primary,
        "context_transitions_secondary": context_transitions_secondary,
        "context_transitions": context_transitions_primary,
        "perspective_origin_event_ids": perspective_origin_event_ids,
        "perspective_records": linked_perspectives,
        "identity_support_records": linked_identities,
        "identity_records": linked_identities,
        "attachment_policy": {
            "perspective": "Attach directly via Perspective.origin -> Passaging.id.",
            "identity": "Attach only as inferred secondary support via Perspective-linked sampleSource or perspective-reference fields.",
        },
        "phenotype_time_span_days": phenotype_time_span_days,
        "warnings": [
            "CandidateSegment ranking remains a first-stage local signal; explicit lineage objects are the preferred modeling units.",
            "Primary traversal uses passaged_from_id1 only by default; passaged_from_id2 is recorded separately as secondary support.",
            "Identity records are attached only as inferred secondary support and must not be treated as directly observed phenotype.",
        ],
    }
    bundle_payload["trajectory_bundle_features"] = trajectory_bundle_features(bundle_payload)
    return bundle_payload


def write_trajectory_bundle(output_dir: str | Path, bundle_payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    write_json(output_dir / "trajectory_bundle.json", bundle_payload)

    features = bundle_payload["trajectory_bundle_features"]
    lines = [
        "# Trajectory Bundle",
        "",
        f"- Bundle ID: `{bundle_payload['bundle_id']}`",
        f"- Seed CandidateSegment: `{bundle_payload['seed_candidate_segment_id']}`",
        f"- Root event: `{bundle_payload.get('root_event_id')}`",
        f"- Selected endpoint event: `{bundle_payload.get('selected_endpoint_event_id')}`",
        f"- Connected CandidateSegments: `{features['connected_segment_count']}`",
        f"- Event count: `{features['event_count']}`",
        f"- Primary transitions: `{len(bundle_payload.get('context_transitions_primary', []))}`",
        f"- Secondary edges: `{len(bundle_payload.get('secondary_lineage_edges', []))}`",
        f"- Terminal Perspective support: `{features['terminal_perspective_support']}`",
        f"- Identity support count: `{features['identity_support_count']}`",
        "",
        "## Traversal Policy",
        "",
        f"- Primary backbone: `{bundle_payload['traversal_policy']['primary_backbone']}`",
        f"- Secondary edges: `{bundle_payload['traversal_policy']['secondary_edges']}`",
        f"- Context role: `{bundle_payload['traversal_policy']['context_grouping_role']}`",
        "",
        "## Warnings",
        "",
    ]
    lines.extend(f"- {warning}" for warning in bundle_payload.get("warnings", []))
    write_markdown(output_dir / "trajectory_bundle.md", "\n".join(lines) + "\n")


def discover_trajectory_bundle_from_file(path: str | Path, seed_dataset_id: str) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    return discover_trajectory_bundle(
        seed_dataset_id=seed_dataset_id,
        passaging_records=payload["passaging"],
        perspective_records=payload.get("perspective", []),
        identity_records=payload.get("identity", []),
    )
