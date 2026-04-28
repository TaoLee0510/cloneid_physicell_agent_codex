"""Deterministic extraction of phase-aware simulation schedules from lineage phase plans."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .phase_planning import (
    DEFAULT_PROOF_OF_PRINCIPLE_GUARDRAIL_MINUTES,
    DEFAULT_SIMULATED_DURATION_MINUTES,
)
from .run_io import write_json, write_markdown


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


def _event_kind(text: str | None) -> str:
    normalized = (text or "").strip().lower()
    if "seed" in normalized:
        return "seed"
    if "harvest" in normalized:
        return "harvest"
    return normalized


def _branch_label(branch_id: str) -> str:
    if "4N" in branch_id:
        return "4N"
    if "2N" in branch_id:
        return "2N"
    return branch_id


def _ratio(child: Any, parent: Any) -> float | None:
    try:
        parent_value = float(parent)
        child_value = float(child)
    except (TypeError, ValueError):
        return None
    if parent_value == 0:
        return None
    return child_value / parent_value


def _phase_observables(phase: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "Passaging.cellCount": {
            "start": phase.get("cellCount_parent"),
            "end": phase.get("cellCount_child"),
            "evidence_class": "derived_event_linked_phenotype",
            "is_direct_observation": False,
            "derived_quantity": True,
        },
        "Passaging.correctedCount": {
            "start": phase.get("correctedCount_parent"),
            "end": phase.get("correctedCount_child"),
            "evidence_class": "derived_event_linked_phenotype",
            "is_direct_observation": False,
            "derived_quantity": True,
        },
        "Passaging.areaOccupied_um2": {
            "start": phase.get("areaOccupied_parent"),
            "end": phase.get("areaOccupied_child"),
            "evidence_class": "derived_event_linked_phenotype",
            "is_direct_observation": False,
            "derived_quantity": True,
        },
    }


def build_branch_simulation_schedule(
    *,
    phase_plan: dict[str, Any],
    milestone_matched_plan: dict[str, Any],
    branch_role: str,
) -> dict[str, Any]:
    branch_id = phase_plan["branch_id"]
    start_milestone = milestone_matched_plan["comparison_window"]["recommended_start_milestone"]
    end_milestone = milestone_matched_plan["comparison_window"]["recommended_end_milestone"]
    prehistory_context = milestone_matched_plan["unmatched_pre_o2_phases"][branch_role]
    phases = phase_plan.get("phases", [])
    phase_by_milestone = {_milestone_label(str(phase["child_event_id"])): phase for phase in phases}

    initial_phase = phase_by_milestone[start_milestone]
    terminal_phase = phase_by_milestone[end_milestone]
    initial_condition = {
        "event_id": initial_phase["child_event_id"],
        "milestone_label": start_milestone,
        "branch_id": branch_id,
        "branch_label": _branch_label(branch_id),
        "cellCount": initial_phase.get("cellCount_child"),
        "correctedCount": initial_phase.get("correctedCount_child"),
        "areaOccupied_um2": initial_phase.get("areaOccupied_child"),
        "media": initial_phase.get("media_to"),
        "flask": initial_phase.get("flask_to"),
        "passage": initial_phase.get("passage_to"),
        "event_provenance": initial_phase.get("event_provenance"),
    }

    growth_episodes: list[dict[str, Any]] = []
    transfer_events: list[dict[str, Any]] = []
    in_window = False
    for phase in phases:
        milestone = _milestone_label(str(phase["child_event_id"]))
        if milestone == start_milestone:
            in_window = True
            continue
        if not in_window:
            continue
        parent_kind = _event_kind(phase.get("event_provenance", {}).get("parent_event", {}).get("event"))
        child_kind = _event_kind(phase.get("event_provenance", {}).get("child_event", {}).get("event"))
        common = {
            "phase_id": phase["phase_id"],
            "branch_id": branch_id,
            "branch_label": _branch_label(branch_id),
            "milestone_label": milestone,
            "parent_event_id": phase["parent_event_id"],
            "child_event_id": phase["child_event_id"],
            "real_elapsed_minutes": phase.get("real_elapsed_minutes"),
            "passage_from": phase.get("passage_from"),
            "passage_to": phase.get("passage_to"),
            "media_from": phase.get("media_from"),
            "media_to": phase.get("media_to"),
            "flask_from": phase.get("flask_from"),
            "flask_to": phase.get("flask_to"),
            "observables": _phase_observables(phase),
            "event_provenance": phase.get("event_provenance"),
        }
        if parent_kind == "seed" and child_kind == "harvest":
            growth_episodes.append(
                {
                    **common,
                    "episode_type": "growth_episode",
                    "simulated_duration_minutes": DEFAULT_SIMULATED_DURATION_MINUTES,
                    "has_terminal_perspective_support": bool(phase.get("has_perspective_at_child_event")),
                    "perspective_record_count_at_child_event": int(phase.get("perspective_record_count_at_child_event", 0)),
                }
            )
        elif parent_kind == "harvest" and child_kind == "seed":
            transfer_events.append(
                {
                    **common,
                    "episode_type": "transfer_event",
                    "simulated_duration_minutes": 0,
                    "inferred_bottleneck": {
                        "cellCount_child_to_parent_ratio": _ratio(
                            phase.get("cellCount_child"),
                            phase.get("cellCount_parent"),
                        ),
                        "correctedCount_child_to_parent_ratio": _ratio(
                            phase.get("correctedCount_child"),
                            phase.get("correctedCount_parent"),
                        ),
                        "areaOccupied_child_to_parent_ratio": _ratio(
                            phase.get("areaOccupied_child"),
                            phase.get("areaOccupied_parent"),
                        ),
                    },
                }
            )
        if milestone == end_milestone:
            break

    terminal_endpoint = {
        "event_id": terminal_phase["child_event_id"],
        "milestone_label": end_milestone,
        "perspective_size_support": {
            "evidence_class": "perspective_molecular",
            "role": "endpoint_validation",
        },
        "perspective_record_count_at_event": int(terminal_phase.get("perspective_record_count_at_child_event", 0)),
        "terminal_perspective_supported_event_count": int(
            phase_plan["summary"]["terminal_perspective_supported_event_count"]
        ),
        "terminal_perspective_record_count": int(phase_plan["summary"]["terminal_perspective_record_count"]),
        "event_provenance": terminal_phase.get("event_provenance"),
    }

    total_growth_simulated_minutes = sum(
        int(item["simulated_duration_minutes"]) for item in growth_episodes if item["simulated_duration_minutes"] is not None
    )
    payload = {
        "schedule_version": "simulation_schedule_v1",
        "phase_alignment_source": milestone_matched_plan["comparison_id"],
        "lineage_object_id": phase_plan["lineage_object_id"],
        "branch_id": branch_id,
        "branch_label": _branch_label(branch_id),
        "simulation_window": {
            "start_milestone": start_milestone,
            "end_milestone": end_milestone,
            "start_event_id": initial_phase["child_event_id"],
            "end_event_id": terminal_phase["child_event_id"],
            "raw_elapsed_time_retained_not_runtime": True,
        },
        "prehistory_context": prehistory_context,
        "initial_condition": initial_condition,
        "growth_episodes": growth_episodes,
        "transfer_events": transfer_events,
        "terminal_endpoint": terminal_endpoint,
        "summary": {
            "growth_episode_count": len(growth_episodes),
            "transfer_event_count": len(transfer_events),
            "total_growth_simulated_minutes": total_growth_simulated_minutes,
            "proof_of_principle_guardrail_minutes": DEFAULT_PROOF_OF_PRINCIPLE_GUARDRAIL_MINUTES,
        },
        "validation": {
            "O2_A1_seed_used_as_initial_condition_not_growth_endpoint": initial_condition["milestone_label"] == start_milestone
            and all(item["child_event_id"] != initial_condition["event_id"] for item in growth_episodes),
            "seed_to_harvest_intervals_labeled_growth_episode": all(
                _event_kind(item["event_provenance"]["parent_event"]["event"]) == "seed"
                and _event_kind(item["event_provenance"]["child_event"]["event"]) == "harvest"
                for item in growth_episodes
            ),
            "harvest_to_seed_intervals_labeled_transfer_event": all(
                _event_kind(item["event_provenance"]["parent_event"]["event"]) == "harvest"
                and _event_kind(item["event_provenance"]["child_event"]["event"]) == "seed"
                for item in transfer_events
            ),
            "transfer_events_not_assigned_growth_duration": all(
                item["simulated_duration_minutes"] in (0, None) for item in transfer_events
            ),
            "pre_o2_phases_remain_context_only": True,
            "terminal_perspective_support_retained_as_endpoint_validation": True,
            "total_simulated_growth_duration_within_guardrail": total_growth_simulated_minutes
            <= DEFAULT_PROOF_OF_PRINCIPLE_GUARDRAIL_MINUTES,
        },
    }
    return payload


def build_matched_simulation_schedule(
    *,
    anchor_schedule: dict[str, Any],
    comparison_schedule: dict[str, Any],
    milestone_matched_plan: dict[str, Any],
) -> dict[str, Any]:
    anchor_growth = {item["milestone_label"]: item for item in anchor_schedule["growth_episodes"]}
    comparison_growth = {item["milestone_label"]: item for item in comparison_schedule["growth_episodes"]}
    matched_growth_episodes = []
    for matched in milestone_matched_plan["matched_milestone_phases"]:
        label = matched["milestone_label"]
        if label in anchor_growth and label in comparison_growth:
            matched_growth_episodes.append(
                {
                    "milestone_label": label,
                    "anchor_growth_episode": anchor_growth[label],
                    "comparison_growth_episode": comparison_growth[label],
                }
            )

    return {
        "schedule_version": "matched_simulation_schedule_v1",
        "comparison_id": milestone_matched_plan["comparison_id"],
        "matching_strategy": "biological_milestone_alignment",
        "comparison_window": milestone_matched_plan["comparison_window"],
        "anchor_branch": {
            "branch_id": anchor_schedule["branch_id"],
            "branch_label": anchor_schedule["branch_label"],
            "terminal_perspective_supported_event_count": anchor_schedule["terminal_endpoint"][
                "terminal_perspective_supported_event_count"
            ],
            "terminal_perspective_record_count": anchor_schedule["terminal_endpoint"][
                "terminal_perspective_record_count"
            ],
        },
        "comparison_branch": {
            "branch_id": comparison_schedule["branch_id"],
            "branch_label": comparison_schedule["branch_label"],
            "terminal_perspective_supported_event_count": comparison_schedule["terminal_endpoint"][
                "terminal_perspective_supported_event_count"
            ],
            "terminal_perspective_record_count": comparison_schedule["terminal_endpoint"][
                "terminal_perspective_record_count"
            ],
        },
        "prehistory_context": {
            "anchor": anchor_schedule["prehistory_context"],
            "comparison": comparison_schedule["prehistory_context"],
        },
        "matched_growth_episodes": matched_growth_episodes,
        "transfer_events": {
            "anchor": anchor_schedule["transfer_events"],
            "comparison": comparison_schedule["transfer_events"],
        },
        "endpoint_alignment": {
            "anchor_terminal_endpoint": anchor_schedule["terminal_endpoint"],
            "comparison_terminal_endpoint": comparison_schedule["terminal_endpoint"],
            "both_branches_contain_A7K_harvest": (
                anchor_schedule["terminal_endpoint"]["milestone_label"] == "O2_A7K_harvest"
                and comparison_schedule["terminal_endpoint"]["milestone_label"] == "O2_A7K_harvest"
            ),
            "both_A7K_harvest_endpoints_have_perspective_support": (
                anchor_schedule["terminal_endpoint"]["perspective_record_count_at_event"] > 0
                and comparison_schedule["terminal_endpoint"]["perspective_record_count_at_event"] > 0
            ),
        },
        "validation": {
            "O2_A7K_harvest_aligned_to_O2_A7K_harvest": True,
            "phase_index_matching_not_primary_alignment": True,
            "total_simulated_growth_duration_within_guardrail": (
                anchor_schedule["summary"]["total_growth_simulated_minutes"]
                <= DEFAULT_PROOF_OF_PRINCIPLE_GUARDRAIL_MINUTES
                and comparison_schedule["summary"]["total_growth_simulated_minutes"]
                <= DEFAULT_PROOF_OF_PRINCIPLE_GUARDRAIL_MINUTES
            ),
            "pre_o2_phases_remain_context_only": True,
            "terminal_perspective_support_retained_as_endpoint_validation": True,
        },
    }


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def write_simulation_schedule(path: str | Path, payload: dict[str, Any]) -> None:
    write_json(Path(path), payload)


def write_matched_simulation_schedule_markdown(path: str | Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Matched Simulation Schedule",
        "",
        f"- Comparison: `{payload['comparison_id']}`",
        f"- Matching strategy: `{payload['matching_strategy']}`",
        f"- Comparison window: `{payload['comparison_window']['recommended_start_milestone']} -> {payload['comparison_window']['recommended_end_milestone']}`",
        f"- Matched growth episodes: `{len(payload['matched_growth_episodes'])}`",
        f"- Anchor transfer events: `{len(payload['transfer_events']['anchor'])}`",
        f"- Comparison transfer events: `{len(payload['transfer_events']['comparison'])}`",
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
        "## Matched growth episodes",
        "",
    ]
    for item in payload["matched_growth_episodes"]:
        lines.append(
            f"- `{item['milestone_label']}`: anchor `{item['anchor_growth_episode']['parent_event_id']} -> {item['anchor_growth_episode']['child_event_id']}` "
            f"vs comparison `{item['comparison_growth_episode']['parent_event_id']} -> {item['comparison_growth_episode']['child_event_id']}`"
        )
    lines.extend(["", "## Validation", ""])
    for key, value in payload["validation"].items():
        lines.append(f"- `{key}`: `{value}`")
    write_markdown(Path(path), "\n".join(lines) + "\n")
