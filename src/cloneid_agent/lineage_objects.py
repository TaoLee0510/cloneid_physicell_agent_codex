"""Global lineage-object discovery over full CLONEID-like record fixtures."""

from __future__ import annotations

import json
from collections import defaultdict, deque
from pathlib import Path
from statistics import mean
from typing import Any

from .run_io import write_json, write_markdown
from .trajectory_bundles import (
    TRANSITION_FIELDS,
    TRAVERSAL_POLICY,
    bundle_time_span_days,
    dataset_id_from_passaging_record,
    group_candidate_segments,
)


def candidate_score_map_from_ranked_candidates(ranked_candidates_payload: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not ranked_candidates_payload:
        return {}
    score_map: dict[str, dict[str, Any]] = {}
    for rank, item in enumerate(ranked_candidates_payload.get("ranked_candidates", []), start=1):
        dataset_id = str(item["dataset_id"])
        score_map[dataset_id] = {
            "candidate_segment_score": item.get("score"),
            "candidate_segment_rank": rank,
            "candidate_segment_score_reasons": item.get("score_reasons", []),
        }
    return score_map


def _build_primary_parent_map(passaging_records: list[dict[str, Any]]) -> dict[str, str]:
    parent_map: dict[str, str] = {}
    for record in passaging_records:
        parent_id = record.get("passaged_from_id1")
        if parent_id not in (None, ""):
            parent_map[str(record["id"])] = str(parent_id)
    return parent_map


def _build_primary_children_map(passaging_records: list[dict[str, Any]]) -> dict[str, list[str]]:
    children_map: dict[str, list[str]] = defaultdict(list)
    for record in passaging_records:
        parent_id = record.get("passaged_from_id1")
        if parent_id not in (None, ""):
            children_map[str(parent_id)].append(str(record["id"]))
    return children_map


def _build_secondary_parent_map(passaging_records: list[dict[str, Any]]) -> dict[str, str]:
    parent_map: dict[str, str] = {}
    for record in passaging_records:
        parent_id = record.get("passaged_from_id2")
        if parent_id not in (None, ""):
            parent_map[str(record["id"])] = str(parent_id)
    return parent_map


def _build_undirected_primary_neighbors(
    event_ids: set[str],
    primary_parent_map: dict[str, str],
    primary_children_map: dict[str, list[str]],
) -> dict[str, set[str]]:
    neighbors: dict[str, set[str]] = {event_id: set() for event_id in event_ids}
    for child_id, parent_id in primary_parent_map.items():
        if child_id in event_ids:
            neighbors.setdefault(child_id, set())
            if parent_id in event_ids:
                neighbors[child_id].add(parent_id)
                neighbors.setdefault(parent_id, set()).add(child_id)
    for parent_id, child_ids in primary_children_map.items():
        if parent_id not in event_ids:
            continue
        for child_id in child_ids:
            if child_id in event_ids:
                neighbors[parent_id].add(child_id)
                neighbors.setdefault(child_id, set()).add(parent_id)
    return neighbors


def _connected_components(neighbors: dict[str, set[str]]) -> list[set[str]]:
    remaining = set(neighbors)
    components: list[set[str]] = []
    while remaining:
        start = next(iter(remaining))
        queue = deque([start])
        component: set[str] = set()
        while queue:
            event_id = queue.popleft()
            if event_id in component:
                continue
            component.add(event_id)
            for neighbor in neighbors.get(event_id, set()):
                if neighbor not in component:
                    queue.append(neighbor)
        remaining -= component
        components.append(component)
    return components


def _attach_perspectives(event_ids: set[str], perspective_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    event_ids_str = {str(event_id) for event_id in event_ids}
    linked = []
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


def _primary_edges_for_event_ids(
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


def _secondary_edges_for_event_ids(
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
                "parent_in_object": parent_id in event_ids,
                "child_in_object": True,
                "parent_date": None if parent is None else parent.get("date"),
                "child_date": None if child is None else child.get("date"),
                "parent_segment_id": None if parent is None else dataset_id_from_passaging_record(parent),
                "child_segment_id": None if child is None else dataset_id_from_passaging_record(child),
            }
        )
    return edges


def _record_context_transitions(
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
            if parent.get(field) != child.get(field):
                transitions.append(
                    {
                        "parent_event_id": edge["parent_event_id"],
                        "child_event_id": edge["child_event_id"],
                        "link_field": edge["link_field"],
                        "field": field,
                        "from_value": parent.get(field),
                        "to_value": child.get(field),
                        "parent_segment_id": edge.get("parent_segment_id"),
                        "child_segment_id": edge.get("child_segment_id"),
                    }
                )
    return transitions


def _candidate_segments_covered(
    event_ids: set[str],
    grouped_segments: dict[str, dict[str, Any]],
    candidate_score_map: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    covered: list[dict[str, Any]] = []
    for dataset_id, segment in grouped_segments.items():
        segment_event_ids = {str(event_id) for event_id in segment.get("event_ids", [])}
        overlap = sorted(event_ids & segment_event_ids)
        if not overlap:
            continue
        covered.append(
            {
                **segment,
                "covered_event_ids": overlap,
                "covered_event_count": len(overlap),
                **candidate_score_map.get(dataset_id, {}),
            }
        )
    covered.sort(
        key=lambda item: (
            item.get("candidate_segment_rank", 10**9),
            item["dataset_id"],
        )
    )
    return covered


def _leaf_event_ids(event_ids: set[str], primary_children_map: dict[str, list[str]]) -> list[str]:
    return sorted(
        event_id
        for event_id in event_ids
        if not any(child_id in event_ids for child_id in primary_children_map.get(event_id, []))
    )


def _component_roots(event_ids: set[str], primary_parent_map: dict[str, str]) -> list[str]:
    return sorted(event_id for event_id in event_ids if primary_parent_map.get(event_id) not in event_ids)


def _component_depth(
    root_ids: list[str],
    event_ids: set[str],
    primary_children_map: dict[str, list[str]],
) -> int:
    max_depth = 0
    queue = deque((root_id, 0) for root_id in root_ids)
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


def _recover_lineage_path(
    endpoint_event_id: str,
    primary_parent_map: dict[str, str],
    passaging_by_id: dict[str, dict[str, Any]],
) -> tuple[list[str], bool]:
    path = [endpoint_event_id]
    current_id = endpoint_event_id
    broken = False
    while current_id in primary_parent_map:
        parent_id = primary_parent_map[current_id]
        if parent_id not in passaging_by_id:
            broken = True
            break
        path.append(parent_id)
        current_id = parent_id
    path.reverse()
    return path, broken


def _phenotype_time_span_days(records: list[dict[str, Any]]) -> float:
    dated = [record.get("date") for record in records if record.get("date") is not None]
    if len(dated) < 2:
        return 0.0
    return bundle_time_span_days(dated[0], dated[-1])


def lineage_object_features(object_payload: dict[str, Any]) -> dict[str, Any]:
    records = object_payload["passaging_records"]
    phenotype_count = sum(
        1
        for record in records
        if any(record.get(field) is not None for field in ("cellCount", "correctedCount", "areaOccupied_um2", "cellSize_um2"))
    )
    candidate_scores = [
        item.get("candidate_segment_score")
        for item in object_payload.get("candidate_segments_covered", [])
        if item.get("candidate_segment_score") is not None
    ]
    perspective_origin_event_ids = set(object_payload.get("perspective_origin_event_ids", []))
    endpoint_event_ids = object_payload.get("endpoint_event_ids", [])
    return {
        "object_type": object_payload["lineage_object_type"],
        "root_count": len(object_payload.get("root_event_ids", [])),
        "endpoint_count": len(endpoint_event_ids),
        "event_count": len(records),
        "event_graph_depth": object_payload.get("event_graph_depth", 0),
        "lineage_path_length": len(object_payload.get("lineage_path_event_ids", [])),
        "connected_segment_count": len(object_payload.get("candidate_segments_covered", [])),
        "candidate_segment_score_max": None if not candidate_scores else max(candidate_scores),
        "candidate_segment_score_mean": None if not candidate_scores else round(mean(candidate_scores), 3),
        "phenotype_observation_count": phenotype_count,
        "phenotype_time_span_days": object_payload.get("phenotype_time_span_days", 0.0),
        "terminal_perspective_support": sum(1 for event_id in endpoint_event_ids if event_id in perspective_origin_event_ids),
        "identity_support_count": len(object_payload.get("identity_support_records", [])),
        "transition_count": len(object_payload.get("context_transitions_primary", [])),
        "calibration_validation_split_possible": len({record.get("date") for record in records if record.get("date") is not None}) >= 3
        and bool(perspective_origin_event_ids),
    }


def _common_object_fields(
    *,
    event_ids: set[str],
    passaging_by_id: dict[str, dict[str, Any]],
    grouped_segments: dict[str, dict[str, Any]],
    candidate_score_map: dict[str, dict[str, Any]],
    perspective_records: list[dict[str, Any]],
    identity_records: list[dict[str, Any]],
    primary_parent_map: dict[str, str],
    primary_children_map: dict[str, list[str]],
    secondary_parent_map: dict[str, str],
) -> dict[str, Any]:
    ordered_records = sorted(
        (passaging_by_id[event_id] for event_id in event_ids),
        key=lambda record: (str(record.get("date")), str(record["id"])),
    )
    primary_lineage_edges = _primary_edges_for_event_ids(event_ids, passaging_by_id, primary_parent_map)
    secondary_lineage_edges = _secondary_edges_for_event_ids(event_ids, passaging_by_id, secondary_parent_map)
    context_transitions_primary = _record_context_transitions(primary_lineage_edges, passaging_by_id)
    context_transitions_secondary = _record_context_transitions(
        [edge for edge in secondary_lineage_edges if edge["parent_event_id"] in passaging_by_id],
        passaging_by_id,
    )
    linked_perspectives = _attach_perspectives(event_ids, perspective_records)
    linked_identities = _attach_identities(linked_perspectives, identity_records)
    perspective_origin_event_ids = sorted(
        {str(record.get("origin")) for record in linked_perspectives if record.get("origin") is not None}
    )
    return {
        "passaging_records": ordered_records,
        "primary_lineage_edges": primary_lineage_edges,
        "secondary_lineage_edges": secondary_lineage_edges,
        "context_transitions_primary": context_transitions_primary,
        "context_transitions_secondary": context_transitions_secondary,
        "candidate_segments_covered": _candidate_segments_covered(event_ids, grouped_segments, candidate_score_map),
        "perspective_records": linked_perspectives,
        "identity_support_records": linked_identities,
        "perspective_origin_event_ids": perspective_origin_event_ids,
        "phenotype_time_span_days": _phenotype_time_span_days(ordered_records),
    }


def discover_global_lineage_objects(
    *,
    passaging_records: list[dict[str, Any]],
    perspective_records: list[dict[str, Any]] | None = None,
    identity_records: list[dict[str, Any]] | None = None,
    ranked_candidates_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    perspective_records = perspective_records or []
    identity_records = identity_records or []
    grouped_segments = group_candidate_segments(passaging_records)
    candidate_score_map = candidate_score_map_from_ranked_candidates(ranked_candidates_payload)

    passaging_by_id = {str(record["id"]): record for record in passaging_records}
    all_event_ids = set(passaging_by_id)
    primary_parent_map = _build_primary_parent_map(passaging_records)
    primary_children_map = _build_primary_children_map(passaging_records)
    secondary_parent_map = _build_secondary_parent_map(passaging_records)
    neighbors = _build_undirected_primary_neighbors(all_event_ids, primary_parent_map, primary_children_map)
    components = _connected_components(neighbors)

    lineage_objects: list[dict[str, Any]] = []
    rooted_bundles: list[dict[str, Any]] = []
    forests: list[dict[str, Any]] = []

    for component_index, component_event_ids in enumerate(sorted(components, key=lambda item: (len(item), sorted(item)[0])), start=1):
        root_ids = _component_roots(component_event_ids, primary_parent_map)
        leaf_ids = _leaf_event_ids(component_event_ids, primary_children_map)
        base = _common_object_fields(
            event_ids=component_event_ids,
            passaging_by_id=passaging_by_id,
            grouped_segments=grouped_segments,
            candidate_score_map=candidate_score_map,
            perspective_records=perspective_records,
            identity_records=identity_records,
            primary_parent_map=primary_parent_map,
            primary_children_map=primary_children_map,
            secondary_parent_map=secondary_parent_map,
        )
        object_type = "RootedTrajectoryBundle" if len(root_ids) == 1 else "LineageForest"
        object_payload = {
            "lineage_object_id": (
                f"rooted_trajectory_bundle::{root_ids[0]}"
                if len(root_ids) == 1
                else f"lineage_forest::{component_index}"
            ),
            "lineage_object_type": object_type,
            "selection_eligible": len(root_ids) == 1,
            "validity_checks": {
                "single_root_required": len(root_ids) == 1,
                "secondary_edges_not_traversed": True,
                "context_annotation_only": True,
            },
            "root_event_id": root_ids[0] if len(root_ids) == 1 else None,
            "root_event_ids": root_ids,
            "endpoint_event_ids": leaf_ids,
            "rooted_subtree_event_ids": sorted(component_event_ids),
            "lineage_path_event_ids": [],
            "traversal_policy": dict(TRAVERSAL_POLICY),
            "object_types": {
                "CandidateSegment": "local_context_bucket",
                "LineagePath": "single_ancestor_to_endpoint_path_via_passaged_from_id1",
                "RootedTrajectoryBundle": "descendants_of_single_root_via_passaged_from_id1",
                "LineageForest": "multi_root_primary_component_not_selectable_as_rooted_bundle",
            },
            "event_graph_depth": _component_depth(root_ids, component_event_ids, primary_children_map),
            **base,
        }
        object_payload["lineage_object_features"] = lineage_object_features(object_payload)
        lineage_objects.append(object_payload)
        if object_type == "RootedTrajectoryBundle":
            rooted_bundles.append(object_payload)
        else:
            forests.append(object_payload)

    lineage_paths: list[dict[str, Any]] = []
    perspective_endpoints = [
        event_id
        for event_id in {
            str(record.get("origin"))
            for record in perspective_records
            if record.get("origin") not in (None, "")
        }
        if event_id in all_event_ids and event_id in _leaf_event_ids(all_event_ids, primary_children_map)
    ]
    for endpoint_event_id in sorted(perspective_endpoints):
        path_event_ids, broken = _recover_lineage_path(endpoint_event_id, primary_parent_map, passaging_by_id)
        path_event_id_set = set(path_event_ids)
        root_event_id = path_event_ids[0] if path_event_ids else None
        base = _common_object_fields(
            event_ids=path_event_id_set,
            passaging_by_id=passaging_by_id,
            grouped_segments=grouped_segments,
            candidate_score_map=candidate_score_map,
            perspective_records=perspective_records,
            identity_records=identity_records,
            primary_parent_map=primary_parent_map,
            primary_children_map=primary_children_map,
            secondary_parent_map=secondary_parent_map,
        )
        object_payload = {
            "lineage_object_id": f"lineage_path::{endpoint_event_id}",
            "lineage_object_type": "LineagePath",
            "selection_eligible": not broken and bool(root_event_id),
            "validity_checks": {
                "single_root_required": bool(root_event_id) and not broken,
                "single_endpoint_required": True,
                "broken_primary_link": broken,
                "secondary_edges_not_traversed": True,
                "context_annotation_only": True,
            },
            "root_event_id": root_event_id,
            "root_event_ids": [] if root_event_id is None else [root_event_id],
            "endpoint_event_ids": [endpoint_event_id],
            "rooted_subtree_event_ids": [],
            "lineage_path_event_ids": path_event_ids,
            "traversal_policy": dict(TRAVERSAL_POLICY),
            "object_types": {
                "CandidateSegment": "local_context_bucket",
                "LineagePath": "single_ancestor_to_endpoint_path_via_passaged_from_id1",
                "RootedTrajectoryBundle": "descendants_of_single_root_via_passaged_from_id1",
                "LineageForest": "multi_root_primary_component_not_selectable_as_rooted_bundle",
            },
            "event_graph_depth": max(len(path_event_ids) - 1, 0),
            **base,
        }
        object_payload["lineage_object_features"] = lineage_object_features(object_payload)
        lineage_paths.append(object_payload)
        lineage_objects.append(object_payload)

    path_lengths = sorted(
        len(item.get("lineage_path_event_ids", []))
        for item in lineage_paths
    )
    bundle_depths = sorted(
        item.get("event_graph_depth", 0)
        for item in rooted_bundles
        if item.get("selection_eligible")
    )
    longest_paths = sorted(
        (
            {
                "lineage_object_id": item["lineage_object_id"],
                "root_event_id": item.get("root_event_id"),
                "endpoint_event_id": item["endpoint_event_ids"][0],
                "lineage_path_length": len(item.get("lineage_path_event_ids", [])),
                "candidate_segments_covered": [seg["dataset_id"] for seg in item.get("candidate_segments_covered", [])],
            }
            for item in lineage_paths
        ),
        key=lambda item: (-item["lineage_path_length"], item["lineage_object_id"]),
    )[:10]
    deepest_bundles = sorted(
        (
            {
                "lineage_object_id": item["lineage_object_id"],
                "root_event_id": item.get("root_event_id"),
                "event_graph_depth": item.get("event_graph_depth", 0),
                "event_count": len(item.get("rooted_subtree_event_ids", [])),
                "endpoint_event_count": len(item.get("endpoint_event_ids", [])),
                "candidate_segments_covered": [seg["dataset_id"] for seg in item.get("candidate_segments_covered", [])],
            }
            for item in rooted_bundles
            if item.get("selection_eligible")
        ),
        key=lambda item: (-item["event_graph_depth"], -item["event_count"], item["lineage_object_id"]),
    )[:10]

    return {
        "inventory_version": "global_lineage_objects_v1",
        "traversal_policy": dict(TRAVERSAL_POLICY),
        "global_graph_summary": {
            "passaging_record_count": len(passaging_records),
            "primary_edge_count": sum(1 for record in passaging_records if record.get("passaged_from_id1") not in (None, "")),
            "secondary_edge_count": sum(1 for record in passaging_records if record.get("passaged_from_id2") not in (None, "")),
            "candidate_segment_count": len(grouped_segments),
        },
        "discovered_object_counts": {
            "LineagePath": len(lineage_paths),
            "RootedTrajectoryBundle": len(rooted_bundles),
            "LineageForest": len(forests),
        },
        "lineage_path_length_distribution": path_lengths,
        "rooted_trajectory_bundle_depth_distribution": bundle_depths,
        "top_10_longest_endpoint_supported_lineage_paths": longest_paths,
        "top_10_deepest_endpoint_supported_rooted_trajectory_bundles": deepest_bundles,
        "global_lineage_objects": lineage_objects,
        "warnings": [
            "Global lineage objects are discovered from the full passaged_from_id1 graph before CandidateSegment scores are used for annotation or ranking.",
            "passaged_from_id2 is recorded only as secondary support and is not traversed by default.",
            "Context buckets annotate graph nodes but do not create graph connectivity.",
        ],
    }


def write_global_lineage_inventory(output_dir: str | Path, payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    write_json(output_dir / "global_lineage_object_inventory.json", payload)
    counts = payload["discovered_object_counts"]
    lines = [
        "# Global Lineage Object Inventory",
        "",
        f"- LineagePaths: `{counts['LineagePath']}`",
        f"- RootedTrajectoryBundles: `{counts['RootedTrajectoryBundle']}`",
        f"- LineageForests: `{counts['LineageForest']}`",
        "",
        "## Top 10 Longest Endpoint-Supported LineagePaths",
        "",
    ]
    for item in payload["top_10_longest_endpoint_supported_lineage_paths"]:
        lines.append(
            f"- `{item['lineage_object_id']}` length `{item['lineage_path_length']}` root `{item['root_event_id']}` endpoint `{item['endpoint_event_id']}`"
        )
    lines.extend(["", "## Top 10 Deepest Endpoint-Supported RootedTrajectoryBundles", ""])
    for item in payload["top_10_deepest_endpoint_supported_rooted_trajectory_bundles"]:
        lines.append(
            f"- `{item['lineage_object_id']}` depth `{item['event_graph_depth']}` events `{item['event_count']}` root `{item['root_event_id']}`"
        )
    write_markdown(output_dir / "global_lineage_object_inventory.md", "\n".join(lines) + "\n")


def discover_global_lineage_objects_from_file(
    path: str | Path,
    ranked_candidates_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    return discover_global_lineage_objects(
        passaging_records=payload["passaging"],
        perspective_records=payload.get("perspective", []),
        identity_records=payload.get("identity", []),
        ranked_candidates_payload=ranked_candidates_payload,
    )
