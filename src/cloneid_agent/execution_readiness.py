"""Scaling contract and execution-readiness reporting for schedule-aware candidates."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

from .run_io import write_json, write_markdown

DEFAULT_AGENT_COUNT_GUARDRAIL = 5000


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def _growth_episodes(schedule: dict[str, Any]) -> list[dict[str, Any]]:
    return list(schedule.get("growth_episodes", []))


def _max_numeric(values: list[Any]) -> float | None:
    casted = []
    for value in values:
        try:
            if value is not None:
                casted.append(float(value))
        except (TypeError, ValueError):
            continue
    return max(casted) if casted else None


def _ceil_div(value: float | None, divisor: int) -> int | None:
    if value is None:
        return None
    return int(math.ceil(float(value) / float(divisor)))


def _build_density_proxy_contract(anchor_schedule: dict[str, Any], comparison_schedule: dict[str, Any]) -> dict[str, Any]:
    anchor_max = _max_numeric(
        [episode["observables"]["Passaging.areaOccupied_um2"]["end"] for episode in _growth_episodes(anchor_schedule)]
    )
    comparison_max = _max_numeric(
        [episode["observables"]["Passaging.areaOccupied_um2"]["end"] for episode in _growth_episodes(comparison_schedule)]
    )
    return {
        "area_proxy_source": "Passaging.areaOccupied_um2",
        "flask_area_known": False,
        "normalization_mode": "relative_branch_max_areaOccupied_um2",
        "branch_normalization_denominators_um2": {
            anchor_schedule["branch_label"]: anchor_max,
            comparison_schedule["branch_label"]: comparison_max,
        },
        "interpretation": "relative_or_normalized_within_branch_not_physical_domain_area",
        "warning": "Raw areaOccupied_um2 is not treated as direct physical vessel area because flask area is unavailable in the current schedule artifacts.",
    }


def build_model_to_data_scaling_contract(
    *,
    anchor_schedule: dict[str, Any],
    comparison_schedule: dict[str, Any],
    matched_schedule: dict[str, Any],
    evaluation_plans: dict[str, dict[str, Any]],
    parameter_placeholders: dict[str, dict[str, Any]],
    agent_count_guardrail: int = DEFAULT_AGENT_COUNT_GUARDRAIL,
) -> dict[str, Any]:
    seed_counts = []
    harvest_counts = []
    corrected_seed_counts = []
    corrected_harvest_counts = []
    for schedule in (anchor_schedule, comparison_schedule):
        for episode in _growth_episodes(schedule):
            seed_counts.append(episode["observables"]["Passaging.cellCount"]["start"])
            harvest_counts.append(episode["observables"]["Passaging.cellCount"]["end"])
            corrected_seed_counts.append(episode["observables"]["Passaging.correctedCount"]["start"])
            corrected_harvest_counts.append(episode["observables"]["Passaging.correctedCount"]["end"])

    max_seed = _max_numeric(seed_counts)
    max_harvest = _max_numeric(harvest_counts)
    max_count = _max_numeric([max_seed, max_harvest])
    if max_count is None:
        raise ValueError("Scaling contract requires at least one numeric cellCount observation")
    cells_per_agent = max(1, int(math.ceil(max_count / float(agent_count_guardrail))))
    max_initial_agents = _ceil_div(max_seed, cells_per_agent)
    max_end_agents = _ceil_div(max_harvest, cells_per_agent)

    density_proxy = _build_density_proxy_contract(anchor_schedule, comparison_schedule)

    return {
        "contract_version": "model_to_data_scaling_contract_v1",
        "comparison_id": matched_schedule["comparison_id"],
        "agent_count_guardrail": int(agent_count_guardrail),
        "cells_per_agent": int(cells_per_agent),
        "agent_count_initialization_mode": "episode_seed_counts_scaled_to_agents",
        "observed_count_to_agent_count_rule": "simulated_agents = ceil(observed_cell_count / cells_per_agent)",
        "agent_count_to_observed_count_rule": "observed_equivalent_cell_count = simulated_agents * cells_per_agent",
        "selection_basis": "conservative_max_observed_cellCount_across_seed_and_harvest_targets",
        "max_observed_seed_cellCount": max_seed,
        "max_observed_harvest_cellCount": max_harvest,
        "max_observed_seed_correctedCount": _max_numeric(corrected_seed_counts),
        "max_observed_harvest_correctedCount": _max_numeric(corrected_harvest_counts),
        "resulting_max_simulated_initial_agent_count": max_initial_agents,
        "resulting_max_simulated_end_target_agent_count": max_end_agents,
        "within_agent_count_guardrail": (max_initial_agents is not None and max_initial_agents <= agent_count_guardrail)
        and (max_end_agents is not None and max_end_agents <= agent_count_guardrail),
        "preserved_under_scaling": [
            "seed_to_harvest fold changes for cellCount",
            "seed_to_harvest fold changes for correctedCount",
            "relative branch comparison across matched growth episodes",
            "back-scaled absolute count comparisons in observed-count units",
        ],
        "approximate_or_lost_under_scaling": [
            "one-agent-equals-one-cell interpretation",
            "exact absolute single-cell neighborhood density",
            "direct physical domain occupancy from raw areaOccupied_um2",
        ],
        "density_proxy_contract": density_proxy,
        "shared_objective_reference": {
            family: {
                "primary_shared_objective": plan["primary_shared_objective"],
                "secondary_objective": plan["secondary_objective"],
                "endpoint_validation": plan["endpoint_validation"],
            }
            for family, plan in evaluation_plans.items()
        },
        "parameter_placeholder_presence": {
            family: sorted(list(payload.get("placeholder_parameters", {}).keys()))
            for family, payload in parameter_placeholders.items()
        },
        "not_biologically_fitted": True,
    }


def _parse_xml_ok(path: Path) -> bool:
    try:
        ET.parse(path)
        return True
    except ET.ParseError:
        return False


def build_execution_readiness_report(
    *,
    candidate_root: str | Path,
    scaling_contract: dict[str, Any],
) -> dict[str, Any]:
    candidate_root = Path(candidate_root)
    families = ["neutral_growth", "fixed_state_fitness", "density_dependent_growth"]
    evaluation_plans = {
        family: _load_json(candidate_root / family / "evaluation_plan.json") for family in families
    }
    schedule_mappings = {
        family: _load_json(candidate_root / family / "schedule_mapping.json") for family in families
    }
    manifests = {
        family: _load_json(candidate_root / family / "candidate_manifest.json") for family in families
    }
    parameter_payloads = {
        family: _load_json(candidate_root / family / "parameter_placeholders.json") for family in families
    }

    primary_target_sets = {family: tuple(evaluation_plans[family]["primary_shared_objective"]["fit_targets"]) for family in families}
    primary_weight_sets = {
        family: evaluation_plans[family]["primary_shared_objective"]["fit_target_weights"] for family in families
    }
    primary_targets_identical = len({primary_target_sets[family] for family in families}) == 1
    primary_weights_identical = len({tuple(sorted(primary_weight_sets[family].items())) for family in families}) == 1
    perspective_not_fit = all(
        not evaluation_plans[family]["endpoint_validation"]["fitting_targets"] for family in families
    )
    schedule_mapping_hash = {
        family: json.dumps(schedule_mappings[family], sort_keys=True) for family in families
    }
    schedule_mapping_identical = len(set(schedule_mapping_hash.values())) == 1
    prehistory_non_executable = all(
        schedule_mappings[family]["prehistory_context_policy"]["excluded_from_primary_runtime"]
        and schedule_mappings[family]["prehistory_context_policy"]["simulation_role"] == "context_only_not_simulated"
        for family in families
    )
    transfer_zero_duration = all(
        schedule_mappings[family]["transfer_event_policy"]["simulated_duration_minutes"] == 0
        for family in families
    )

    family_reports = {}
    for family in families:
        family_dir = candidate_root / family
        config_path = family_dir / "config" / "PhysiCell_settings.xml"
        params = set(parameter_payloads[family]["placeholder_parameters"].keys())
        if family == "neutral_growth":
            family_specific_params_present = not any("_2N" in p or "_4N" in p for p in params)
            density_proxy_handling_specified = False
        elif family == "fixed_state_fitness":
            family_specific_params_present = any("_2N" in p or "_4N" in p for p in params)
            density_proxy_handling_specified = False
        else:
            family_specific_params_present = any("density" in p or "area_proxy" in p for p in params)
            density_proxy_handling_specified = True

        family_reports[family] = {
            "config_files_present": config_path.exists(),
            "config_xml_parse_ok": _parse_xml_ok(config_path),
            "parameter_placeholders_present": bool(params),
            "family_specific_parameters_present": family_specific_params_present,
            "shared_objective_present": primary_targets_identical and primary_weights_identical,
            "scaling_contract_available": True,
            "schedule_mapping_available": (family_dir / "schedule_mapping.json").exists(),
            "transfer_event_handling_specified": schedule_mappings[family]["transfer_event_policy"]["simulated_duration_minutes"] == 0,
            "density_proxy_handling_specified": density_proxy_handling_specified,
            "ready_for_syntax_dry_run": config_path.exists() and _parse_xml_ok(config_path),
            "ready_for_biological_simulation": False,
        }

    return {
        "report_version": "execution_readiness_report_v1",
        "candidate_root": str(candidate_root),
        "shared_objective_invariants": {
            "primary_fit_targets_identical_across_families": primary_targets_identical,
            "primary_fit_target_weights_identical_across_families": primary_weights_identical,
            "endpoint_perspective_size_not_used_for_fitting": perspective_not_fit,
            "density_dependent_growth_uses_same_primary_objective": (
                primary_target_sets["density_dependent_growth"] == primary_target_sets["neutral_growth"]
                == primary_target_sets["fixed_state_fitness"]
            ),
            "schedule_mapping_identical_across_candidates": schedule_mapping_identical,
            "prehistory_context_non_executable": prehistory_non_executable,
            "transfer_events_have_non_positive_simulated_duration": transfer_zero_duration,
        },
        "scaling_summary": {
            "max_observed_seed_cellCount": scaling_contract["max_observed_seed_cellCount"],
            "max_observed_harvest_cellCount": scaling_contract["max_observed_harvest_cellCount"],
            "proposed_cells_per_agent": scaling_contract["cells_per_agent"],
            "resulting_max_simulated_initial_agent_count": scaling_contract["resulting_max_simulated_initial_agent_count"],
            "resulting_max_simulated_end_target_agent_count": scaling_contract["resulting_max_simulated_end_target_agent_count"],
            "within_agent_count_guardrail": scaling_contract["within_agent_count_guardrail"],
            "preserved_under_scaling": scaling_contract["preserved_under_scaling"],
            "approximate_or_lost_under_scaling": scaling_contract["approximate_or_lost_under_scaling"],
        },
        "family_readiness": family_reports,
        "ready_for_biological_simulation": False,
        "static_validation_only": True,
    }


def write_model_to_data_scaling_contract(path: str | Path, payload: dict[str, Any]) -> None:
    write_json(Path(path), payload)
    lines = [
        "# Model-to-Data Scaling Contract",
        "",
        f"- Comparison: `{payload['comparison_id']}`",
        f"- Cells per agent: `{payload['cells_per_agent']}`",
        f"- Agent-count guardrail: `{payload['agent_count_guardrail']}`",
        f"- Max observed seed cellCount: `{payload['max_observed_seed_cellCount']}`",
        f"- Max observed harvest cellCount: `{payload['max_observed_harvest_cellCount']}`",
        f"- Max simulated initial agent count: `{payload['resulting_max_simulated_initial_agent_count']}`",
        f"- Max simulated end target agent count: `{payload['resulting_max_simulated_end_target_agent_count']}`",
        f"- Within guardrail: `{payload['within_agent_count_guardrail']}`",
        "",
        "## Density proxy",
        "",
        f"- Source: `{payload['density_proxy_contract']['area_proxy_source']}`",
        f"- Normalization mode: `{payload['density_proxy_contract']['normalization_mode']}`",
        f"- Interpretation: `{payload['density_proxy_contract']['interpretation']}`",
    ]
    write_markdown(Path(path).with_suffix(".md"), "\n".join(lines) + "\n")


def write_execution_readiness_report(path: str | Path, payload: dict[str, Any]) -> None:
    write_json(Path(path), payload)
    lines = [
        "# Execution Readiness Report",
        "",
        f"- Candidate root: `{payload['candidate_root']}`",
        f"- Ready for biological simulation: `{payload['ready_for_biological_simulation']}`",
        f"- Static validation only: `{payload['static_validation_only']}`",
        "",
        "## Shared objective invariants",
        "",
    ]
    for key, value in payload["shared_objective_invariants"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Family readiness", ""])
    for family, details in payload["family_readiness"].items():
        lines.append(f"- `{family}`")
        for key, value in details.items():
            lines.append(f"  - `{key}`: `{value}`")
    write_markdown(Path(path).with_suffix(".md"), "\n".join(lines) + "\n")


def generate_execution_readiness_artifacts(
    *,
    anchor_schedule_path: str | Path,
    comparison_schedule_path: str | Path,
    matched_schedule_path: str | Path,
    candidate_root: str | Path,
    scaling_contract_json_path: str | Path,
    execution_readiness_json_path: str | Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    candidate_root = Path(candidate_root)
    families = ["neutral_growth", "fixed_state_fitness", "density_dependent_growth"]
    evaluation_plans = {
        family: _load_json(candidate_root / family / "evaluation_plan.json") for family in families
    }
    parameter_payloads = {
        family: _load_json(candidate_root / family / "parameter_placeholders.json") for family in families
    }
    scaling_contract = build_model_to_data_scaling_contract(
        anchor_schedule=_load_json(anchor_schedule_path),
        comparison_schedule=_load_json(comparison_schedule_path),
        matched_schedule=_load_json(matched_schedule_path),
        evaluation_plans=evaluation_plans,
        parameter_placeholders=parameter_payloads,
    )
    write_model_to_data_scaling_contract(scaling_contract_json_path, scaling_contract)
    readiness_report = build_execution_readiness_report(
        candidate_root=candidate_root,
        scaling_contract=scaling_contract,
    )
    write_execution_readiness_report(execution_readiness_json_path, readiness_report)
    return scaling_contract, readiness_report
