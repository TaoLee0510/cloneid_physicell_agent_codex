"""Deterministic primary-lineage interval phase planning for biological proof-of-principle lineage paths."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import re
from typing import Any

from .run_io import write_json, write_markdown

DEFAULT_SIMULATED_DURATION_MINUTES = 1440
DEFAULT_PROOF_OF_PRINCIPLE_GUARDRAIL_MINUTES = 86400


def _parse_date(text: Any) -> datetime | None:
    if not isinstance(text, str):
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _event_index(passaging_records: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(record["id"]): record for record in passaging_records if record.get("id") is not None}


def _perspectives_by_origin(perspective_records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    origins: dict[str, list[dict[str, Any]]] = {}
    for record in perspective_records:
        origin = record.get("origin")
        if origin is None:
            continue
        origins.setdefault(str(origin), []).append(record)
    return origins


def _ordered_lineage_records(lineage_object_payload: dict[str, Any]) -> list[dict[str, Any]]:
    event_ids = [str(event_id) for event_id in lineage_object_payload.get("lineage_path_event_ids", [])]
    by_id = _event_index(lineage_object_payload.get("passaging_records", []))
    return [by_id[event_id] for event_id in event_ids if event_id in by_id]


def build_primary_lineage_interval_phase_plan(
    lineage_object_payload: dict[str, Any],
    *,
    branch_id: str,
    simulated_duration_minutes: int = DEFAULT_SIMULATED_DURATION_MINUTES,
    proof_of_principle_guardrail_minutes: int = DEFAULT_PROOF_OF_PRINCIPLE_GUARDRAIL_MINUTES,
) -> dict[str, Any]:
    ordered_records = _ordered_lineage_records(lineage_object_payload)
    if len(ordered_records) < 2:
        raise ValueError("Phase planning requires at least two ordered lineage-path events")

    perspectives_by_origin = _perspectives_by_origin(lineage_object_payload.get("perspective_records", []))
    endpoint_event_ids = {str(event_id) for event_id in lineage_object_payload.get("endpoint_event_ids", [])}
    phases: list[dict[str, Any]] = []
    primary_link_failures: list[dict[str, str]] = []

    for index, (parent, child) in enumerate(zip(ordered_records, ordered_records[1:]), start=1):
        parent_id = str(parent["id"])
        child_id = str(child["id"])
        parent_date = _parse_date(parent.get("date"))
        child_date = _parse_date(child.get("date"))
        real_elapsed_minutes = None
        if parent_date is not None and child_date is not None:
            real_elapsed_minutes = int(round((child_date - parent_date).total_seconds() / 60.0))

        child_parent_ref = child.get("passaged_from_id1")
        if child_parent_ref is not None and str(child_parent_ref) != parent_id:
            primary_link_failures.append(
                {
                    "phase_id": f"{branch_id}::phase_{index:03d}",
                    "expected_parent_event_id": parent_id,
                    "observed_passaged_from_id1": str(child_parent_ref),
                }
            )

        child_perspectives = perspectives_by_origin.get(child_id, [])
        phases.append(
            {
                "phase_id": f"{branch_id}::phase_{index:03d}",
                "branch_id": branch_id,
                "phase_index": index,
                "parent_event_id": parent_id,
                "child_event_id": child_id,
                "real_elapsed_minutes": real_elapsed_minutes,
                "simulated_duration_minutes": int(simulated_duration_minutes),
                "passage_from": parent.get("passage"),
                "passage_to": child.get("passage"),
                "media_from": parent.get("media"),
                "media_to": child.get("media"),
                "flask_from": parent.get("flask"),
                "flask_to": child.get("flask"),
                "cellCount_parent": parent.get("cellCount"),
                "cellCount_child": child.get("cellCount"),
                "correctedCount_parent": parent.get("correctedCount"),
                "correctedCount_child": child.get("correctedCount"),
                "areaOccupied_parent": parent.get("areaOccupied_um2"),
                "areaOccupied_child": child.get("areaOccupied_um2"),
                "has_perspective_at_child_event": bool(child_perspectives),
                "perspective_record_count_at_child_event": len(child_perspectives),
                "event_provenance": {
                    "lineage_object_id": lineage_object_payload.get("lineage_object_id"),
                    "root_event_id": lineage_object_payload.get("root_event_id"),
                    "parent_event": {
                        "id": parent_id,
                        "event": parent.get("event"),
                        "date": parent.get("date"),
                    },
                    "child_event": {
                        "id": child_id,
                        "event": child.get("event"),
                        "date": child.get("date"),
                    },
                },
            }
        )

    terminal_supported_event_count = sum(1 for event_id in endpoint_event_ids if perspectives_by_origin.get(event_id))
    terminal_record_count = sum(len(perspectives_by_origin.get(event_id, [])) for event_id in endpoint_event_ids)
    total_simulated_duration_minutes = len(phases) * int(simulated_duration_minutes)

    payload = {
        "plan_version": "primary_lineage_interval_phase_plan_v1",
        "lineage_object_id": lineage_object_payload.get("lineage_object_id"),
        "lineage_object_type": lineage_object_payload.get("lineage_object_type"),
        "branch_id": branch_id,
        "phase_strategy": "primary_lineage_interval_phases",
        "simulation_duration_policy": {
            "mode": "fixed_duration_per_primary_lineage_interval",
            "simulated_duration_minutes_per_phase": int(simulated_duration_minutes),
            "proof_of_principle_guardrail_minutes": int(proof_of_principle_guardrail_minutes),
            "real_elapsed_time_retained_but_not_runtime": True,
        },
        "observable_definitions": {
            "Passaging.cellCount": {
                "evidence_class": "derived_event_linked_phenotype",
                "is_direct_observation": False,
                "derived_quantity": True,
            },
            "Passaging.correctedCount": {
                "evidence_class": "derived_event_linked_phenotype",
                "is_direct_observation": False,
                "derived_quantity": True,
            },
            "Passaging.areaOccupied_um2": {
                "evidence_class": "derived_event_linked_phenotype",
                "is_direct_observation": False,
                "derived_quantity": True,
            },
            "Perspective.size": {
                "evidence_class": "perspective_molecular",
                "is_direct_observation": True,
                "derived_quantity": False,
                "role": "endpoint_support",
            },
            "Identity": {
                "evidence_class": "identity_inferred",
                "is_direct_observation": False,
                "derived_quantity": True,
                "role": "secondary_support_only",
            },
        },
        "summary": {
            "event_count": len(ordered_records),
            "phase_count": len(phases),
            "root_event_id": lineage_object_payload.get("root_event_id"),
            "endpoint_event_ids": lineage_object_payload.get("endpoint_event_ids", []),
            "terminal_perspective_supported_event_count": terminal_supported_event_count,
            "terminal_perspective_record_count": terminal_record_count,
            "total_simulated_duration_minutes": total_simulated_duration_minutes,
            "raw_elapsed_time_days": lineage_object_payload.get("lineage_object_features", {}).get("phenotype_time_span_days"),
        },
        "phases": phases,
        "validation": {
            "phases_follow_passaged_from_id1_order": not primary_link_failures,
            "passaged_from_id1_validation_failures": primary_link_failures,
            "fixed_simulated_duration_per_interval": all(
                phase["simulated_duration_minutes"] == int(simulated_duration_minutes) for phase in phases
            ),
            "real_elapsed_time_retained_not_runtime": True,
            "correctedCount_labeled_derived_event_linked_phenotype": True,
            "areaOccupied_labeled_derived_event_linked_phenotype": True,
            "perspective_size_labeled_endpoint_molecular_support": True,
            "terminal_perspective_event_vs_record_counts_separated": True,
            "total_simulated_duration_within_guardrail": total_simulated_duration_minutes
            <= int(proof_of_principle_guardrail_minutes),
        },
    }
    return payload


def build_primary_lineage_interval_phase_plan_from_inventory(
    inventory_payload: dict[str, Any],
    *,
    lineage_object_id: str,
    branch_id: str,
    simulated_duration_minutes: int = DEFAULT_SIMULATED_DURATION_MINUTES,
    proof_of_principle_guardrail_minutes: int = DEFAULT_PROOF_OF_PRINCIPLE_GUARDRAIL_MINUTES,
) -> dict[str, Any]:
    lineage_object = next(
        item for item in inventory_payload.get("global_lineage_objects", []) if item["lineage_object_id"] == lineage_object_id
    )
    return build_primary_lineage_interval_phase_plan(
        lineage_object,
        branch_id=branch_id,
        simulated_duration_minutes=simulated_duration_minutes,
        proof_of_principle_guardrail_minutes=proof_of_principle_guardrail_minutes,
    )


def build_matched_primary_lineage_interval_phase_plan(
    *,
    anchor_plan: dict[str, Any],
    comparison_plan: dict[str, Any],
) -> dict[str, Any]:
    anchor_phases = anchor_plan.get("phases", [])
    comparison_phases = comparison_plan.get("phases", [])
    max_len = max(len(anchor_phases), len(comparison_phases))
    matched: list[dict[str, Any]] = []
    unmatched_anchor: list[dict[str, Any]] = []
    unmatched_comparison: list[dict[str, Any]] = []

    for idx in range(max_len):
        anchor_phase = anchor_phases[idx] if idx < len(anchor_phases) else None
        comparison_phase = comparison_phases[idx] if idx < len(comparison_phases) else None
        phase_index = idx + 1
        if anchor_phase is not None and comparison_phase is not None:
            matched.append(
                {
                    "phase_index": phase_index,
                    "anchor_phase": anchor_phase,
                    "comparison_phase": comparison_phase,
                }
            )
        elif anchor_phase is not None:
            unmatched_anchor.append(anchor_phase)
        elif comparison_phase is not None:
            unmatched_comparison.append(comparison_phase)

    total_simulated_duration_minutes = max(
        int(anchor_plan["summary"]["total_simulated_duration_minutes"]),
        int(comparison_plan["summary"]["total_simulated_duration_minutes"]),
    )
    return {
        "plan_version": "matched_primary_lineage_interval_phase_plan_v1",
        "comparison_id": f"{anchor_plan['branch_id']}_vs_{comparison_plan['branch_id']}",
        "phase_strategy": "primary_lineage_interval_phases",
        "anchor_branch": {
            "branch_id": anchor_plan["branch_id"],
            "lineage_object_id": anchor_plan["lineage_object_id"],
            "phase_count": anchor_plan["summary"]["phase_count"],
            "terminal_perspective_supported_event_count": anchor_plan["summary"]["terminal_perspective_supported_event_count"],
            "terminal_perspective_record_count": anchor_plan["summary"]["terminal_perspective_record_count"],
        },
        "comparison_branch": {
            "branch_id": comparison_plan["branch_id"],
            "lineage_object_id": comparison_plan["lineage_object_id"],
            "phase_count": comparison_plan["summary"]["phase_count"],
            "terminal_perspective_supported_event_count": comparison_plan["summary"]["terminal_perspective_supported_event_count"],
            "terminal_perspective_record_count": comparison_plan["summary"]["terminal_perspective_record_count"],
        },
        "observable_policy": {
            "joint_calibration_targets": [
                "Passaging.cellCount",
                "Passaging.correctedCount",
                "Passaging.areaOccupied_um2",
            ],
            "terminal_validation_target": "Perspective.size",
            "identity_role": "secondary_inferred_support_only",
        },
        "matched_phases": matched,
        "unmatched_anchor_phases": unmatched_anchor,
        "unmatched_comparison_phases": unmatched_comparison,
        "validation": {
            "simulated_duration_fixed_at_1440_minutes": all(
                phase["anchor_phase"]["simulated_duration_minutes"] == DEFAULT_SIMULATED_DURATION_MINUTES
                and phase["comparison_phase"]["simulated_duration_minutes"] == DEFAULT_SIMULATED_DURATION_MINUTES
                for phase in matched
            )
            and all(phase["simulated_duration_minutes"] == DEFAULT_SIMULATED_DURATION_MINUTES for phase in unmatched_anchor)
            and all(phase["simulated_duration_minutes"] == DEFAULT_SIMULATED_DURATION_MINUTES for phase in unmatched_comparison),
            "real_elapsed_time_not_used_as_runtime": True,
            "total_simulated_duration_within_guardrail": total_simulated_duration_minutes
            <= DEFAULT_PROOF_OF_PRINCIPLE_GUARDRAIL_MINUTES,
        },
    }


def _milestone_label(event_id: str) -> str:
    text = event_id.replace("SUM159_", "SUM-159_")
    patterns = [
        r"O2_A7K_harvest",
        r"O2_A7K_seed",
        r"O2_A\d+_seedT\d+",
        r"O2_A\d+_seed",
        r"dp_seedT\d+",
        r"dp_seed",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return text.split("_", 1)[-1] if "_" in text else text


def _milestone_phase_index(phases: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for phase in phases:
        label = _milestone_label(str(phase["child_event_id"]))
        index[label] = phase
    return index


def _window_milestones(start_label: str, end_label: str, phases: list[dict[str, Any]]) -> list[str]:
    labels = [_milestone_label(str(phase["child_event_id"])) for phase in phases]
    if start_label not in labels or end_label not in labels:
        raise ValueError("Comparison-window milestones are not both present in the phase plan")
    start_idx = labels.index(start_label)
    end_idx = labels.index(end_label)
    return labels[start_idx : end_idx + 1]


def build_milestone_matched_primary_lineage_interval_phase_plan(
    *,
    anchor_plan: dict[str, Any],
    comparison_plan: dict[str, Any],
    comparison_window_start: str = "O2_A1_seed",
    comparison_window_end: str = "O2_A7K_harvest",
) -> dict[str, Any]:
    anchor_phases = anchor_plan.get("phases", [])
    comparison_phases = comparison_plan.get("phases", [])
    anchor_by_milestone = _milestone_phase_index(anchor_phases)
    comparison_by_milestone = _milestone_phase_index(comparison_phases)

    anchor_window = _window_milestones(comparison_window_start, comparison_window_end, anchor_phases)
    comparison_window = _window_milestones(comparison_window_start, comparison_window_end, comparison_phases)
    comparison_window_labels = [label for label in anchor_window if label in comparison_window]

    matched_milestone_phases: list[dict[str, Any]] = []
    for milestone in comparison_window_labels:
        matched_milestone_phases.append(
            {
                "milestone_label": milestone,
                "anchor_phase": anchor_by_milestone[milestone],
                "comparison_phase": comparison_by_milestone[milestone],
            }
        )

    def classify_unmatched(phases: list[dict[str, Any]], start: str, end: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
        labels = [_milestone_label(str(phase["child_event_id"])) for phase in phases]
        start_idx = labels.index(start)
        end_idx = labels.index(end)
        prehistory = []
        extra = []
        tail = []
        for idx, phase in enumerate(phases):
            label = labels[idx]
            annotated = {**phase, "milestone_label": label}
            if idx < start_idx:
                prehistory.append(annotated)
            elif idx > end_idx:
                tail.append(annotated)
            elif label not in comparison_window_labels:
                extra.append(annotated)
        return prehistory, extra, tail

    anchor_prehistory, anchor_extra, anchor_tail = classify_unmatched(
        anchor_phases, comparison_window_start, comparison_window_end
    )
    comparison_prehistory, comparison_extra, comparison_tail = classify_unmatched(
        comparison_phases, comparison_window_start, comparison_window_end
    )

    anchor_terminal = anchor_by_milestone.get("O2_A7K_harvest")
    comparison_terminal = comparison_by_milestone.get("O2_A7K_harvest")
    anchor_terminal_supported = bool(anchor_terminal and anchor_terminal["has_perspective_at_child_event"])
    comparison_terminal_supported = bool(comparison_terminal and comparison_terminal["has_perspective_at_child_event"])
    total_simulated_duration_minutes = max(
        len(comparison_window_labels) * DEFAULT_SIMULATED_DURATION_MINUTES,
        len(anchor_window) * DEFAULT_SIMULATED_DURATION_MINUTES,
        len(comparison_window) * DEFAULT_SIMULATED_DURATION_MINUTES,
    )

    return {
        "plan_version": "milestone_matched_primary_lineage_interval_phase_plan_v1",
        "comparison_id": f"{anchor_plan['branch_id']}_vs_{comparison_plan['branch_id']}",
        "matching_strategy": "biological_milestone_alignment",
        "comparison_window": {
            "recommended_start_milestone": comparison_window_start,
            "recommended_end_milestone": comparison_window_end,
            "recommended_start_rationale": (
                "Use O2_A1_seed as the primary manuscript comparison start because both branches are explicitly O2-labeled "
                "from that point onward; preserve dp history as pre-O2 context rather than forcing it into the direct phase alignment."
            ),
            "context_only_prehistory_milestones": ["dp_seed", "dp_seedT1"],
        },
        "anchor_branch": {
            "branch_id": anchor_plan["branch_id"],
            "lineage_object_id": anchor_plan["lineage_object_id"],
            "terminal_perspective_supported_event_count": anchor_plan["summary"]["terminal_perspective_supported_event_count"],
            "terminal_perspective_record_count": anchor_plan["summary"]["terminal_perspective_record_count"],
        },
        "comparison_branch": {
            "branch_id": comparison_plan["branch_id"],
            "lineage_object_id": comparison_plan["lineage_object_id"],
            "terminal_perspective_supported_event_count": comparison_plan["summary"]["terminal_perspective_supported_event_count"],
            "terminal_perspective_record_count": comparison_plan["summary"]["terminal_perspective_record_count"],
        },
        "matched_milestone_phases": matched_milestone_phases,
        "unmatched_pre_o2_phases": {
            "anchor": anchor_prehistory,
            "comparison": comparison_prehistory,
        },
        "unmatched_extra_branch_history": {
            "anchor": anchor_extra,
            "comparison": comparison_extra,
        },
        "unmatched_post_comparison_tail": {
            "anchor": anchor_tail,
            "comparison": comparison_tail,
        },
        "endpoint_alignment": {
            "both_branches_contain_A7K_harvest": bool(anchor_terminal and comparison_terminal),
            "both_A7K_harvest_endpoints_have_perspective_support": anchor_terminal_supported and comparison_terminal_supported,
            "anchor_A7K_harvest_phase": anchor_terminal,
            "comparison_A7K_harvest_phase": comparison_terminal,
        },
        "observable_policy": {
            "joint_calibration_targets": [
                "Passaging.cellCount",
                "Passaging.correctedCount",
                "Passaging.areaOccupied_um2",
            ],
            "terminal_validation_target": "Perspective.size",
            "identity_role": "secondary_inferred_support_only",
        },
        "validation": {
            "terminal_A7K_harvest_endpoints_aligned": bool(anchor_terminal and comparison_terminal),
            "terminal_perspective_supported_events_aligned_as_endpoints": anchor_terminal_supported and comparison_terminal_supported,
            "phase_index_matching_not_primary_alignment": True,
            "unmatched_phases_labeled_as_prehistory_extra_or_post_tail": True,
            "total_simulated_duration_within_guardrail": total_simulated_duration_minutes
            <= DEFAULT_PROOF_OF_PRINCIPLE_GUARDRAIL_MINUTES,
        },
    }


def write_phase_plan(path: str | Path, payload: dict[str, Any]) -> None:
    write_json(Path(path), payload)


def load_inventory(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def write_matched_phase_plan_markdown(path: str | Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Matched Phase Plan",
        "",
        f"- Comparison: `{payload['comparison_id']}`",
        f"- Anchor branch: `{payload['anchor_branch']['lineage_object_id']}`",
        f"- Comparison branch: `{payload['comparison_branch']['lineage_object_id']}`",
        f"- Matched phases: `{len(payload['matched_phases'])}`",
        f"- Unmatched anchor phases: `{len(payload['unmatched_anchor_phases'])}`",
        f"- Unmatched comparison phases: `{len(payload['unmatched_comparison_phases'])}`",
        "",
        "## Validation",
        "",
    ]
    for key, value in payload.get("validation", {}).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Matched phases", ""])
    for pair in payload.get("matched_phases", [])[:50]:
        lines.append(
            f"- phase `{pair['phase_index']}`: anchor `{pair['anchor_phase']['parent_event_id']} -> {pair['anchor_phase']['child_event_id']}` "
            f"vs comparison `{pair['comparison_phase']['parent_event_id']} -> {pair['comparison_phase']['child_event_id']}`"
        )
    if payload.get("unmatched_anchor_phases"):
        lines.extend(["", "## Unmatched anchor phases", ""])
        for phase in payload["unmatched_anchor_phases"]:
            lines.append(f"- `{phase['phase_id']}` `{phase['parent_event_id']} -> {phase['child_event_id']}`")
    if payload.get("unmatched_comparison_phases"):
        lines.extend(["", "## Unmatched comparison phases", ""])
        for phase in payload["unmatched_comparison_phases"]:
            lines.append(f"- `{phase['phase_id']}` `{phase['parent_event_id']} -> {phase['child_event_id']}`")
    write_markdown(Path(path), "\n".join(lines) + "\n")


def write_milestone_matched_phase_plan_markdown(path: str | Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Milestone-Matched Phase Plan",
        "",
        f"- Comparison: `{payload['comparison_id']}`",
        f"- Matching strategy: `{payload['matching_strategy']}`",
        f"- Recommended comparison window: `{payload['comparison_window']['recommended_start_milestone']} -> {payload['comparison_window']['recommended_end_milestone']}`",
        f"- Start rationale: {payload['comparison_window']['recommended_start_rationale']}",
        "",
        "## Endpoint alignment",
        "",
        f"- Both branches contain A7K harvest: `{payload['endpoint_alignment']['both_branches_contain_A7K_harvest']}`",
        f"- Both A7K harvest endpoints have Perspective support: `{payload['endpoint_alignment']['both_A7K_harvest_endpoints_have_perspective_support']}`",
        f"- Anchor terminal supported-event count: `{payload['anchor_branch']['terminal_perspective_supported_event_count']}`",
        f"- Anchor terminal record count: `{payload['anchor_branch']['terminal_perspective_record_count']}`",
        f"- Comparison terminal supported-event count: `{payload['comparison_branch']['terminal_perspective_supported_event_count']}`",
        f"- Comparison terminal record count: `{payload['comparison_branch']['terminal_perspective_record_count']}`",
        "",
        "## Matched milestone phases",
        "",
    ]
    for pair in payload.get("matched_milestone_phases", []):
        lines.append(
            f"- `{pair['milestone_label']}`: anchor `{pair['anchor_phase']['parent_event_id']} -> {pair['anchor_phase']['child_event_id']}` "
            f"vs comparison `{pair['comparison_phase']['parent_event_id']} -> {pair['comparison_phase']['child_event_id']}`"
        )
    for section_key, heading in [
        ("unmatched_pre_o2_phases", "Unmatched pre-O2 phases"),
        ("unmatched_extra_branch_history", "Unmatched extra branch history"),
        ("unmatched_post_comparison_tail", "Unmatched post-comparison tail"),
    ]:
        lines.extend(["", f"## {heading}", ""])
        section = payload[section_key]
        lines.append(f"- Anchor count: `{len(section['anchor'])}`")
        lines.append(f"- Comparison count: `{len(section['comparison'])}`")
        for side in ("anchor", "comparison"):
            for phase in section[side]:
                lines.append(
                    f"- `{side}` `{phase['milestone_label']}` `{phase['parent_event_id']} -> {phase['child_event_id']}`"
                )
    lines.extend(["", "## Validation", ""])
    for key, value in payload.get("validation", {}).items():
        lines.append(f"- `{key}`: `{value}`")
    write_markdown(Path(path), "\n".join(lines) + "\n")
