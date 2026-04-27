"""Deterministic TrajectoryBundle discovery over mock or cached CLONEID-like records."""

from __future__ import annotations

import json
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any

from .run_io import write_json, write_markdown


SEGMENT_CONTEXT_FIELDS = ("cellLine", "growthType", "passage", "media", "flask")
TRANSITION_FIELDS = ("growthType", "passage", "media", "flask")


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


def _build_parent_to_children(passaging_records: list[dict[str, Any]]) -> dict[str, list[str]]:
    graph: dict[str, list[str]] = defaultdict(list)
    for record in passaging_records:
        child_id = str(record["id"])
        for field in ("passaged_from_id1", "passaged_from_id2"):
            parent_id = record.get(field)
            if parent_id not in (None, ""):
                graph[str(parent_id)].append(child_id)
    return graph


def _collect_connected_event_ids(
    seed_event_ids: set[str],
    passaging_by_id: dict[str, dict[str, Any]],
    parent_to_children: dict[str, list[str]],
    *,
    max_upstream_depth: int,
    max_downstream_depth: int,
    stop_on_cell_line_change: bool,
) -> tuple[set[str], list[dict[str, Any]], list[dict[str, Any]]]:
    connected: set[str] = set(seed_event_ids)
    excluded_neighbors: list[dict[str, Any]] = []
    expansions: list[dict[str, Any]] = []
    seed_cell_lines = {str(passaging_by_id[event_id].get("cellLine")) for event_id in seed_event_ids}

    upstream_queue = deque((event_id, 0) for event_id in seed_event_ids)
    seen_upstream: set[tuple[str, int]] = set()
    while upstream_queue:
        event_id, depth = upstream_queue.popleft()
        if (event_id, depth) in seen_upstream:
            continue
        seen_upstream.add((event_id, depth))
        if depth >= max_upstream_depth:
            continue
        record = passaging_by_id[event_id]
        for field in ("passaged_from_id1", "passaged_from_id2"):
            parent_id = record.get(field)
            if parent_id in (None, ""):
                continue
            parent_id = str(parent_id)
            parent_record = passaging_by_id.get(parent_id)
            if parent_record is None:
                excluded_neighbors.append(
                    {"event_id": parent_id, "reason": "missing parent record", "direction": "upstream"}
                )
                continue
            if stop_on_cell_line_change and str(parent_record.get("cellLine")) not in seed_cell_lines:
                excluded_neighbors.append(
                    {"event_id": parent_id, "reason": "cell line change", "direction": "upstream"}
                )
                continue
            if parent_id not in connected:
                connected.add(parent_id)
                expansions.append({"event_id": parent_id, "direction": "upstream", "depth": depth + 1})
            upstream_queue.append((parent_id, depth + 1))

    downstream_queue = deque((event_id, 0) for event_id in seed_event_ids)
    seen_downstream: set[tuple[str, int]] = set()
    while downstream_queue:
        event_id, depth = downstream_queue.popleft()
        if (event_id, depth) in seen_downstream:
            continue
        seen_downstream.add((event_id, depth))
        if depth >= max_downstream_depth:
            continue
        for child_id in parent_to_children.get(event_id, []):
            child_record = passaging_by_id.get(child_id)
            if child_record is None:
                excluded_neighbors.append(
                    {"event_id": child_id, "reason": "missing child record", "direction": "downstream"}
                )
                continue
            if stop_on_cell_line_change and str(child_record.get("cellLine")) not in seed_cell_lines:
                excluded_neighbors.append(
                    {"event_id": child_id, "reason": "cell line change", "direction": "downstream"}
                )
                continue
            if child_id not in connected:
                connected.add(child_id)
                expansions.append({"event_id": child_id, "direction": "downstream", "depth": depth + 1})
            downstream_queue.append((child_id, depth + 1))

    return connected, expansions, excluded_neighbors


def _record_context_transitions(ordered_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transitions: list[dict[str, Any]] = []
    if not ordered_records:
        return transitions
    previous = ordered_records[0]
    for current in ordered_records[1:]:
        for field in TRANSITION_FIELDS:
            prev_value = previous.get(field)
            curr_value = current.get(field)
            if prev_value != curr_value:
                transitions.append(
                    {
                        "from_event_id": previous["id"],
                        "to_event_id": current["id"],
                        "field": field,
                        "from_value": prev_value,
                        "to_value": curr_value,
                    }
                )
        previous = current
    return transitions


def _build_lineage_edges(
    ordered_records: list[dict[str, Any]],
    passaging_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    event_ids = {str(record["id"]) for record in ordered_records}
    edges: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str]] = set()
    for child in ordered_records:
        child_id = str(child["id"])
        for field in ("passaged_from_id1", "passaged_from_id2"):
            parent_id = child.get(field)
            if parent_id in (None, ""):
                continue
            parent_id = str(parent_id)
            if parent_id not in event_ids:
                continue
            parent = passaging_by_id[parent_id]
            key = (parent_id, child_id, field)
            if key in seen:
                continue
            seen.add(key)
            edges.append(
                {
                    "parent_event_id": parent_id,
                    "child_event_id": child_id,
                    "link_field": field,
                    "parent_date": parent.get("date"),
                    "child_date": child.get("date"),
                    "parent_segment_id": dataset_id_from_passaging_record(parent),
                    "child_segment_id": dataset_id_from_passaging_record(child),
                }
            )
    edges.sort(
        key=lambda edge: (
            str(edge.get("parent_date")),
            str(edge.get("child_date")),
            edge["parent_event_id"],
            edge["child_event_id"],
        )
    )
    return edges


def _record_context_transitions_from_edges(
    lineage_edges: list[dict[str, Any]],
    passaging_by_id: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    transitions: list[dict[str, Any]] = []
    for edge in lineage_edges:
        parent = passaging_by_id[edge["parent_event_id"]]
        child = passaging_by_id[edge["child_event_id"]]
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
                        "parent_segment_id": edge["parent_segment_id"],
                        "child_segment_id": edge["child_segment_id"],
                    }
                )
    return transitions


def _build_segment_connections(
    lineage_edges: list[dict[str, Any]],
    context_transitions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    transition_map: dict[tuple[str, str, str], dict[str, Any]] = {}
    for transition in context_transitions:
        key = (
            transition["parent_event_id"],
            transition["child_event_id"],
            transition["field"],
        )
        transition_map[key] = transition

    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for edge in lineage_edges:
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
                "lineage_edges": [],
                "context_changes": [],
            },
        )
        bucket["lineage_edges"].append(
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


def _graph_distance_from_roots(passaging_records: list[dict[str, Any]]) -> int:
    if not passaging_records:
        return 0

    children_by_parent = _build_parent_to_children(passaging_records)
    event_ids = {str(record["id"]) for record in passaging_records}
    roots = [
        str(record["id"])
        for record in passaging_records
        if all(
            parent_id in (None, "") or str(parent_id) not in event_ids
            for parent_id in (record.get("passaged_from_id1"), record.get("passaged_from_id2"))
        )
    ]
    if not roots:
        return 0

    max_depth = 0
    queue = deque((event_id, 0) for event_id in roots)
    seen: set[str] = set()
    while queue:
        event_id, depth = queue.popleft()
        if event_id in seen:
            continue
        seen.add(event_id)
        max_depth = max(max_depth, depth)
        for child_id in children_by_parent.get(event_id, []):
            queue.append((child_id, depth + 1))
    return max_depth


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


def trajectory_bundle_features(bundle_payload: dict[str, Any]) -> dict[str, Any]:
    passaging_records = bundle_payload["passaging_records"]
    context_transitions = bundle_payload["context_transitions"]
    perspective_records = bundle_payload["perspective_records"]
    identity_records = bundle_payload["identity_records"]
    connected_segments = bundle_payload["connected_candidate_segments"]

    phenotype_count = sum(
        1
        for record in passaging_records
        if any(record.get(field) is not None for field in ("cellCount", "correctedCount", "areaOccupied_um2", "cellSize_um2"))
    )
    event_ids = {str(record["id"]) for record in passaging_records}
    root_ids = {
        str(record["id"])
        for record in passaging_records
        if all(
            parent_id in (None, "") or str(parent_id) not in event_ids
            for parent_id in (record.get("passaged_from_id1"), record.get("passaged_from_id2"))
        )
    }
    leaf_ids = event_ids.copy()
    for record in passaging_records:
        for field in ("passaged_from_id1", "passaged_from_id2"):
            parent_id = record.get(field)
            if parent_id not in (None, ""):
                leaf_ids.discard(str(parent_id))

    distinct_dates = sorted({record.get("date") for record in passaging_records if record.get("date") is not None})
    bundle_complexity_penalty = max(0, len(passaging_records) - 25) + max(0, len(context_transitions) - 10)
    event_graph_depth = _graph_distance_from_roots(passaging_records)

    return {
        "connected_segment_count": len(connected_segments),
        "event_graph_depth": event_graph_depth,
        "event_count": len(passaging_records),
        "transition_count": len(context_transitions),
        "has_branching": any(
            sum(record.get(field) not in (None, "") for field in ("passaged_from_id1", "passaged_from_id2")) > 1
            for record in passaging_records
        ),
        "has_longitudinal_context_change": bool(context_transitions),
        "phenotype_observation_count": phenotype_count,
        "phenotype_time_span_days": bundle_payload["phenotype_time_span_days"],
        "terminal_perspective_support": sum(1 for record in perspective_records if str(record.get("origin")) in leaf_ids),
        "identity_support_count": len(identity_records),
        "calibration_validation_split_possible": len(distinct_dates) >= 3 and len(perspective_records) >= 1,
        "trajectory_bundle_complexity_penalty": bundle_complexity_penalty,
        "root_event_count": len(root_ids),
        "leaf_event_count": len(leaf_ids),
    }


def discover_trajectory_bundle(
    *,
    seed_dataset_id: str,
    passaging_records: list[dict[str, Any]],
    perspective_records: list[dict[str, Any]] | None = None,
    identity_records: list[dict[str, Any]] | None = None,
    max_upstream_depth: int = 6,
    max_downstream_depth: int = 6,
    stop_on_cell_line_change: bool = True,
) -> dict[str, Any]:
    perspective_records = perspective_records or []
    identity_records = identity_records or []
    segments = group_candidate_segments(passaging_records)
    if seed_dataset_id not in segments:
        raise ValueError(f"Seed dataset_id not found in passaging records: {seed_dataset_id}")

    passaging_by_id = {str(record["id"]): record for record in passaging_records}
    parent_to_children = _build_parent_to_children(passaging_records)
    seed_event_ids = {str(event_id) for event_id in segments[seed_dataset_id]["event_ids"]}
    connected_ids, expansions, excluded_neighbors = _collect_connected_event_ids(
        seed_event_ids,
        passaging_by_id,
        parent_to_children,
        max_upstream_depth=max_upstream_depth,
        max_downstream_depth=max_downstream_depth,
        stop_on_cell_line_change=stop_on_cell_line_change,
    )

    ordered_records = sorted(
        (passaging_by_id[event_id] for event_id in connected_ids),
        key=lambda record: (str(record.get("date")), str(record["id"])),
    )
    connected_segment_ids = sorted({dataset_id_from_passaging_record(record) for record in ordered_records})
    connected_segment_records = [segments[dataset_id] for dataset_id in connected_segment_ids]
    lineage_edges = _build_lineage_edges(ordered_records, passaging_by_id)
    context_transitions = _record_context_transitions_from_edges(lineage_edges, passaging_by_id)
    segment_connections = _build_segment_connections(lineage_edges, context_transitions)
    linked_perspectives = _attach_perspectives(connected_ids, perspective_records)
    linked_identities = _attach_identities(linked_perspectives, identity_records)

    phenotype_dates = [record.get("date") for record in ordered_records if record.get("date") is not None]
    phenotype_time_span_days = 0.0
    if phenotype_dates:
        phenotype_time_span_days = 0.0 if len(phenotype_dates) < 2 else bundle_time_span_days(phenotype_dates[0], phenotype_dates[-1])

    bundle_payload = {
        "seed_candidate_segment_id": seed_dataset_id,
        "bundle_id": f"trajectory_bundle::{seed_dataset_id}",
        "bundle_role": "connected_event_history_modeling_unit",
        "graph_expansion": {
            "max_upstream_depth_requested": max_upstream_depth,
            "max_downstream_depth_requested": max_downstream_depth,
            "max_upstream_depth_reached": max((item["depth"] for item in expansions if item["direction"] == "upstream"), default=0),
            "max_downstream_depth_reached": max((item["depth"] for item in expansions if item["direction"] == "downstream"), default=0),
            "stop_on_cell_line_change": stop_on_cell_line_change,
            "expansion_events": expansions,
            "excluded_neighbors": excluded_neighbors,
        },
        "connected_candidate_segments": connected_segment_records,
        "passaging_records": ordered_records,
        "lineage_edges": lineage_edges,
        "segment_connections": segment_connections,
        "context_transitions": context_transitions,
        "perspective_records": linked_perspectives,
        "identity_records": linked_identities,
        "attachment_policy": {
            "perspective": "Attach directly via Perspective.origin -> Passaging.id.",
            "identity": "Attach only as inferred secondary support via Perspective-linked sampleSource or perspective-reference fields.",
        },
        "phenotype_time_span_days": phenotype_time_span_days,
        "warnings": [
            "CandidateSegment ranking remains a first-stage local screen; TrajectoryBundle is the preferred modeling unit when connected event histories exist.",
            "Identity records are attached only as inferred secondary support and must not be treated as directly observed phenotype.",
        ],
    }
    bundle_payload["trajectory_bundle_features"] = trajectory_bundle_features(bundle_payload)
    return bundle_payload


def bundle_time_span_days(first_date: str, last_date: str) -> float:
    start = _parse_event_datetime(first_date)
    stop = _parse_event_datetime(last_date)
    if start is None or stop is None:
        return 0.0
    return round(max((stop - start).total_seconds() / 86400.0, 0.0), 3)


def write_trajectory_bundle(output_dir: str | Path, bundle_payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    write_json(output_dir / "trajectory_bundle.json", bundle_payload)

    features = bundle_payload["trajectory_bundle_features"]
    lines = [
        "# Trajectory Bundle",
        "",
        f"- Bundle ID: `{bundle_payload['bundle_id']}`",
        f"- Seed CandidateSegment: `{bundle_payload['seed_candidate_segment_id']}`",
        f"- Connected CandidateSegments: `{features['connected_segment_count']}`",
        f"- Event count: `{features['event_count']}`",
        f"- Transition count: `{features['transition_count']}`",
        f"- Terminal Perspective support: `{features['terminal_perspective_support']}`",
        f"- Identity support count: `{features['identity_support_count']}`",
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
