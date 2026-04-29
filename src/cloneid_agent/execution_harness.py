"""Schedule-aware dry-run execution harness for PhysiCell candidate folders."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

from .run_io import write_json, write_markdown

FAMILIES = ("neutral_growth", "fixed_state_fitness", "density_dependent_growth")

EXPECTED_PRIMARY_TARGETS = [
    "Passaging.cellCount.seed_to_harvest_fold_change",
    "Passaging.correctedCount.seed_to_harvest_fold_change",
]

EXPECTED_PRIMARY_TARGET_WEIGHTS = {
    "Passaging.cellCount.seed_to_harvest_fold_change": 1.0,
    "Passaging.correctedCount.seed_to_harvest_fold_change": 1.0,
}


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _ceil_div(value: Any, divisor: int) -> int:
    numeric = _safe_float(value)
    if numeric is None:
        return 0
    return int(math.ceil(numeric / float(divisor)))


def _branch_key(branch_label: str) -> str:
    if branch_label == "4N":
        return "anchor"
    if branch_label == "2N":
        return "comparison"
    return branch_label.lower()


def _parse_xml_error(path: Path) -> str | None:
    try:
        ET.parse(path)
        return None
    except ET.ParseError as exc:
        return str(exc)


def _shared_objective(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "primary_shared_objective": plan["primary_shared_objective"],
        "secondary_objective": plan["secondary_objective"],
        "endpoint_validation": plan["endpoint_validation"],
    }


def _families_payload(candidate_root: Path) -> dict[str, dict[str, Any]]:
    payload: dict[str, dict[str, Any]] = {}
    for family in FAMILIES:
        family_dir = candidate_root / family
        payload[family] = {
            "candidate_dir": str(family_dir),
            "manifest": _load_json(family_dir / "candidate_manifest.json"),
            "evaluation_plan": _load_json(family_dir / "evaluation_plan.json"),
            "schedule_mapping": _load_json(family_dir / "schedule_mapping.json"),
            "parameter_placeholders": _load_json(family_dir / "parameter_placeholders.json"),
            "config_path": str(family_dir / "config" / "PhysiCell_settings.xml"),
        }
    return payload


def build_execution_harness_plan(
    *,
    candidate_root: str | Path,
    scaling_contract: dict[str, Any],
    execution_readiness_report: dict[str, Any],
    matched_schedule: dict[str, Any],
) -> dict[str, Any]:
    candidate_root = Path(candidate_root)
    families = _families_payload(candidate_root)
    manifest_sample = next(iter(families.values()))["manifest"]
    executable_path = Path(manifest_sample["physicell_executable"])
    physicell_root = Path(manifest_sample["physicell_root"])
    dry_run_physicell_status = (
        "available_not_executed_by_policy"
        if executable_path.exists() and physicell_root.exists()
        else "unavailable"
    )
    return {
        "plan_version": "execution_harness_plan_v1",
        "candidate_root": str(candidate_root),
        "comparison_id": matched_schedule["comparison_id"],
        "modes": {
            "dry_run_static": {
                "enabled": True,
                "description": "Validate XML/configs, schedules, scaling contract, expected paths, and shared evaluation objective invariants without executing PhysiCell.",
            },
            "dry_run_mock": {
                "enabled": True,
                "description": "Emit deterministic mock outputs and evaluation artifacts using the shared evaluation schema and the model-to-data scaling contract.",
            },
            "dry_run_physicell": {
                "enabled": dry_run_physicell_status != "unavailable",
                "status": dry_run_physicell_status,
                "reason": (
                    "PhysiCell install is present, but this work unit stops at syntax/dry-run harness generation."
                    if dry_run_physicell_status != "unavailable"
                    else "PhysiCell executable or install root not available from the candidate manifests."
                ),
                "physicell_root": str(physicell_root),
                "physicell_executable": str(executable_path),
            },
        },
        "shared_objective": _shared_objective(next(iter(families.values()))["evaluation_plan"]),
        "expected_mock_output_schema": {
            "episode_fields": [
                "episode_id",
                "milestone_label",
                "initial_agent_count",
                "final_agent_count",
                "back_scaled_initial_cellCount",
                "back_scaled_final_cellCount",
                "predicted_seed_to_harvest_fold_change",
                "observed_seed_to_harvest_fold_change",
                "residual",
                "notes",
            ],
            "branch_metadata": [
                "branch_id",
                "branch_label",
                "family_id",
                "output_mode",
                "shared_evaluation_objective",
            ],
        },
        "invariants": {
            "perspective_size_endpoint_validation_only": True,
            "prehistory_context_not_executable": True,
            "transfer_events_are_reset_or_bottleneck_not_growth": True,
            "shared_objective_identical_across_families": execution_readiness_report["shared_objective_invariants"][
                "primary_fit_targets_identical_across_families"
            ]
            and execution_readiness_report["shared_objective_invariants"][
                "primary_fit_target_weights_identical_across_families"
            ],
        },
        "scaling_summary": {
            "cells_per_agent": scaling_contract["cells_per_agent"],
            "agent_count_guardrail": scaling_contract["agent_count_guardrail"],
            "max_simulated_end_target_agent_count": scaling_contract[
                "resulting_max_simulated_end_target_agent_count"
            ],
        },
        "matched_growth_episode_count": len(matched_schedule["matched_growth_episodes"]),
        "families": {
            family: {
                "candidate_dir": payload["candidate_dir"],
                "config_path": payload["config_path"],
                "shared_objective_present": True,
            }
            for family, payload in families.items()
        },
    }


def _validate_shared_objective(
    families: dict[str, dict[str, Any]],
    issues: list[str],
) -> dict[str, Any]:
    primary_targets = {}
    primary_weights = {}
    endpoint_fitting_targets = {}
    for family, payload in families.items():
        plan = payload["evaluation_plan"]
        primary_targets[family] = list(plan["primary_shared_objective"]["fit_targets"])
        primary_weights[family] = dict(plan["primary_shared_objective"]["fit_target_weights"])
        endpoint_fitting_targets[family] = list(plan["endpoint_validation"]["fitting_targets"])

    targets_identical = len({tuple(primary_targets[family]) for family in FAMILIES}) == 1
    if not targets_identical:
        issues.append("Primary shared fit targets differ across candidate families.")
    weights_identical = len(
        {tuple(sorted(primary_weights[family].items())) for family in FAMILIES}
    ) == 1
    if not weights_identical:
        issues.append("Primary shared fit-target weights differ across candidate families.")
    if primary_targets[FAMILIES[0]] != EXPECTED_PRIMARY_TARGETS:
        issues.append("Primary shared fit targets do not match the approved objective vector.")
    if primary_weights[FAMILIES[0]] != EXPECTED_PRIMARY_TARGET_WEIGHTS:
        issues.append("Primary shared fit-target weights do not match the approved objective vector.")
    if any(endpoint_fitting_targets[family] for family in FAMILIES):
        issues.append("Perspective.size appears in fitting targets; endpoint validation must remain fit-free.")

    return {
        "primary_fit_targets_identical_across_families": targets_identical,
        "primary_fit_target_weights_identical_across_families": weights_identical,
        "approved_primary_targets_present": primary_targets[FAMILIES[0]] == EXPECTED_PRIMARY_TARGETS,
        "approved_primary_weights_present": primary_weights[FAMILIES[0]] == EXPECTED_PRIMARY_TARGET_WEIGHTS,
        "endpoint_perspective_size_not_used_for_fitting": all(
            not endpoint_fitting_targets[family] for family in FAMILIES
        ),
    }


def _validate_schedule_mapping(
    families: dict[str, dict[str, Any]],
    matched_schedule: dict[str, Any],
    issues: list[str],
) -> dict[str, Any]:
    schedule_mapping_hashes = {
        family: json.dumps(families[family]["schedule_mapping"], sort_keys=True) for family in FAMILIES
    }
    identical = len(set(schedule_mapping_hashes.values())) == 1
    if not identical:
        issues.append("schedule_mapping.json differs across candidates unexpectedly.")

    expected_labels = [item["milestone_label"] for item in matched_schedule["matched_growth_episodes"]]
    mapping = families[FAMILIES[0]]["schedule_mapping"]
    matched_labels = list(mapping["matched_growth_episode_labels"])
    if matched_labels != expected_labels:
        issues.append("schedule_mapping.json does not preserve the matched growth-episode milestone set.")

    prehistory_non_executable = all(
        families[family]["schedule_mapping"]["prehistory_context_policy"]["excluded_from_primary_runtime"]
        and families[family]["schedule_mapping"]["prehistory_context_policy"]["simulation_role"]
        == "context_only_not_simulated"
        for family in FAMILIES
    )
    if not prehistory_non_executable:
        issues.append("prehistory_context is marked executable in one or more schedule mappings.")

    transfer_non_growth = all(
        families[family]["schedule_mapping"]["transfer_event_policy"]["simulated_duration_minutes"] == 0
        for family in FAMILIES
    )
    if not transfer_non_growth:
        issues.append("transfer_event policy assigns positive simulated duration.")

    return {
        "schedule_mapping_identical_across_candidates": identical,
        "matched_growth_episode_labels_preserved": matched_labels == expected_labels,
        "prehistory_context_non_executable": prehistory_non_executable,
        "transfer_events_have_zero_duration_policy": transfer_non_growth,
    }


def _validate_branch_schedule(
    schedule: dict[str, Any],
    branch_role: str,
    issues: list[str],
) -> dict[str, Any]:
    prehistory_context = schedule.get("prehistory_context", [])
    prehistory_non_executable = all(
        item.get("excluded_from_primary_runtime") is True
        and item.get("simulation_role") == "context_only_not_simulated"
        and item.get("simulated_duration_minutes") is None
        for item in prehistory_context
    )
    if not prehistory_non_executable:
        issues.append(f"{branch_role} prehistory_context includes executable runtime state.")

    transfer_non_growth = all(
        int(item.get("simulated_duration_minutes", 0)) <= 0
        and item.get("episode_type") == "transfer_event"
        for item in schedule.get("transfer_events", [])
    )
    if not transfer_non_growth:
        issues.append(f"{branch_role} transfer_events include positive simulated duration.")

    growth_positive = all(
        int(item.get("simulated_duration_minutes", 0)) > 0
        and item.get("episode_type") == "growth_episode"
        for item in schedule.get("growth_episodes", [])
    )
    if not growth_positive:
        issues.append(f"{branch_role} growth_episodes include non-positive simulated duration.")

    return {
        "prehistory_context_non_executable": prehistory_non_executable,
        "transfer_events_non_growth": transfer_non_growth,
        "growth_episodes_positive_duration": growth_positive,
        "growth_episode_count": len(schedule.get("growth_episodes", [])),
        "transfer_event_count": len(schedule.get("transfer_events", [])),
    }


def build_dry_run_static_report(
    *,
    candidate_root: str | Path,
    scaling_contract: dict[str, Any],
    execution_readiness_report: dict[str, Any],
    anchor_schedule: dict[str, Any],
    comparison_schedule: dict[str, Any],
    matched_schedule: dict[str, Any],
) -> dict[str, Any]:
    candidate_root = Path(candidate_root)
    families = _families_payload(candidate_root)
    issues: list[str] = []

    family_reports = {}
    for family, payload in families.items():
        config_path = Path(payload["config_path"])
        xml_error = _parse_xml_error(config_path)
        manifest = payload["manifest"]
        family_reports[family] = {
            "config_exists": config_path.exists(),
            "config_xml_parse_ok": xml_error is None,
            "config_xml_error": xml_error,
            "physicell_root_exists": Path(manifest["physicell_root"]).exists(),
            "physicell_executable_exists": Path(manifest["physicell_executable"]).exists(),
            "schedule_mapping_exists": (Path(payload["candidate_dir"]) / "schedule_mapping.json").exists(),
            "evaluation_plan_exists": (Path(payload["candidate_dir"]) / "evaluation_plan.json").exists(),
            "parameter_placeholders_exist": (Path(payload["candidate_dir"]) / "parameter_placeholders.json").exists(),
        }
        if xml_error is not None:
            issues.append(f"{family} has malformed PhysiCell_settings.xml: {xml_error}")

    shared_objective = _validate_shared_objective(families, issues)
    schedule_mapping = _validate_schedule_mapping(families, matched_schedule, issues)
    branch_validation = {
        "anchor": _validate_branch_schedule(anchor_schedule, "anchor", issues),
        "comparison": _validate_branch_schedule(comparison_schedule, "comparison", issues),
    }

    physicell_available = all(
        family_reports[family]["physicell_executable_exists"] and family_reports[family]["physicell_root_exists"]
        for family in FAMILIES
    )
    dry_run_physicell_status = (
        "available_not_executed_by_policy" if physicell_available else "unavailable"
    )

    passed = not issues
    return {
        "report_version": "dry_run_static_report_v1",
        "candidate_root": str(candidate_root),
        "passed": passed,
        "issues": issues,
        "shared_objective_invariants": shared_objective,
        "schedule_mapping_invariants": schedule_mapping,
        "branch_schedule_validation": branch_validation,
        "family_validation": family_reports,
        "scaling_contract_summary": {
            "cells_per_agent": scaling_contract["cells_per_agent"],
            "agent_count_guardrail": scaling_contract["agent_count_guardrail"],
            "within_agent_count_guardrail": scaling_contract["within_agent_count_guardrail"],
        },
        "execution_readiness_reference": {
            "ready_for_syntax_dry_run": all(
                execution_readiness_report["family_readiness"][family]["ready_for_syntax_dry_run"]
                for family in FAMILIES
            ),
            "ready_for_biological_simulation": execution_readiness_report["ready_for_biological_simulation"],
        },
        "dry_run_modes": {
            "dry_run_static": "passed" if passed else "failed",
            "dry_run_mock": "not_yet_run",
            "dry_run_physicell": dry_run_physicell_status,
        },
    }


def _family_mock_multiplier(family: str, branch_label: str, area_fold_change: float | None) -> float:
    if family == "neutral_growth":
        return 1.0
    if family == "fixed_state_fitness":
        return 1.05 if branch_label == "4N" else 0.95
    density_modifier = 1.0
    if area_fold_change is not None:
        density_modifier = max(0.75, min(1.0, 1.0 - 0.03 * max(0.0, area_fold_change - 1.0)))
    return density_modifier


def _episode_fold_change(observable: dict[str, Any]) -> float | None:
    start = _safe_float(observable.get("start"))
    end = _safe_float(observable.get("end"))
    if start in (None, 0.0) or end is None:
        return None
    return end / start


def _mock_branch_payload(
    *,
    family: str,
    branch_schedule: dict[str, Any],
    cells_per_agent: int,
    shared_objective: dict[str, Any],
) -> dict[str, Any]:
    episodes = []
    for episode in branch_schedule["growth_episodes"]:
        cell_fc = _episode_fold_change(episode["observables"]["Passaging.cellCount"])
        corrected_fc = _episode_fold_change(episode["observables"]["Passaging.correctedCount"])
        area_fc = _episode_fold_change(episode["observables"]["Passaging.areaOccupied_um2"])
        initial_agent_count = _ceil_div(
            episode["observables"]["Passaging.cellCount"]["start"],
            cells_per_agent,
        )
        mock_multiplier = _family_mock_multiplier(family, branch_schedule["branch_label"], area_fc)
        predicted_cell_fc = (cell_fc or 1.0) * mock_multiplier
        final_agent_count = max(1, int(round(initial_agent_count * predicted_cell_fc)))
        back_scaled_initial = initial_agent_count * cells_per_agent
        back_scaled_final = final_agent_count * cells_per_agent
        episodes.append(
            {
                "episode_id": episode["phase_id"],
                "milestone_label": episode["milestone_label"],
                "initial_agent_count": initial_agent_count,
                "final_agent_count": final_agent_count,
                "back_scaled_initial_cellCount": back_scaled_initial,
                "back_scaled_final_cellCount": back_scaled_final,
                "predicted_seed_to_harvest_fold_change": back_scaled_final / back_scaled_initial
                if back_scaled_initial
                else None,
                "observed_seed_to_harvest_fold_change": cell_fc,
                "residual": (
                    (back_scaled_final / back_scaled_initial) - cell_fc if cell_fc is not None and back_scaled_initial else None
                ),
                "objective_vector": {
                    "Passaging.cellCount.seed_to_harvest_fold_change": {
                        "predicted": back_scaled_final / back_scaled_initial if back_scaled_initial else None,
                        "observed": cell_fc,
                        "residual": (
                            (back_scaled_final / back_scaled_initial) - cell_fc
                            if cell_fc is not None and back_scaled_initial
                            else None
                        ),
                    },
                    "Passaging.correctedCount.seed_to_harvest_fold_change": {
                        "predicted": (corrected_fc or 1.0) * mock_multiplier if corrected_fc is not None else None,
                        "observed": corrected_fc,
                        "residual": (
                            ((corrected_fc or 1.0) * mock_multiplier) - corrected_fc
                            if corrected_fc is not None
                            else None
                        ),
                    },
                    "Passaging.areaOccupied_um2.seed_to_harvest_fold_change": {
                        "predicted": area_fc,
                        "observed": area_fc,
                        "residual": 0.0 if area_fc is not None else None,
                    },
                },
                "notes": "Deterministic mock output only. Not biological, not fitted, and not suitable for interpretation.",
            }
        )

    return {
        "family_id": family,
        "branch_id": branch_schedule["branch_id"],
        "branch_label": branch_schedule["branch_label"],
        "output_mode": "dry_run_mock",
        "shared_evaluation_objective": shared_objective,
        "prehistory_context_excluded_from_runtime": True,
        "transfer_events_non_growth": True,
        "perspective_size_fitting_target": False,
        "episodes": episodes,
    }


def build_dry_run_mock_outputs(
    *,
    candidate_root: str | Path,
    scaling_contract: dict[str, Any],
    anchor_schedule: dict[str, Any],
    comparison_schedule: dict[str, Any],
    matched_schedule: dict[str, Any],
    output_dir: str | Path,
) -> dict[str, Any]:
    candidate_root = Path(candidate_root)
    output_dir = Path(output_dir)
    families = _families_payload(candidate_root)
    cells_per_agent = int(scaling_contract["cells_per_agent"])

    shared_objective = _shared_objective(next(iter(families.values()))["evaluation_plan"])

    index: dict[str, Any] = {
        "output_version": "dry_run_mock_outputs_v1",
        "comparison_id": matched_schedule["comparison_id"],
        "families": {},
    }
    for family in FAMILIES:
        family_dir = output_dir / family
        family_dir.mkdir(parents=True, exist_ok=True)
        anchor_payload = _mock_branch_payload(
            family=family,
            branch_schedule=anchor_schedule,
            cells_per_agent=cells_per_agent,
            shared_objective=shared_objective,
        )
        comparison_payload = _mock_branch_payload(
            family=family,
            branch_schedule=comparison_schedule,
            cells_per_agent=cells_per_agent,
            shared_objective=shared_objective,
        )
        anchor_path = write_json(family_dir / f"{anchor_schedule['branch_id']}.json", anchor_payload)
        comparison_path = write_json(family_dir / f"{comparison_schedule['branch_id']}.json", comparison_payload)
        index["families"][family] = {
            "anchor_branch_output": str(anchor_path),
            "comparison_branch_output": str(comparison_path),
        }
    write_json(output_dir / "index.json", index)
    return index


def build_dry_run_mock_evaluation_report(
    *,
    candidate_root: str | Path,
    matched_schedule: dict[str, Any],
    mock_output_dir: str | Path,
) -> dict[str, Any]:
    candidate_root = Path(candidate_root)
    mock_output_dir = Path(mock_output_dir)
    families = _families_payload(candidate_root)

    report_families = {}
    issues: list[str] = []
    matched_labels = [item["milestone_label"] for item in matched_schedule["matched_growth_episodes"]]

    for family in FAMILIES:
        anchor_output = _load_json(mock_output_dir / family / "SUM159_4N_O2.json")
        comparison_output = _load_json(mock_output_dir / family / "SUM159_2N_O2.json")
        plan = families[family]["evaluation_plan"]

        if plan["endpoint_validation"]["fitting_targets"]:
            issues.append(f"{family} mock evaluation plan uses Perspective.size as a fitting target.")

        all_labels = [
            *[item["milestone_label"] for item in anchor_output["episodes"]],
            *[item["milestone_label"] for item in comparison_output["episodes"]],
        ]
        for label in matched_labels:
            if all_labels.count(label) < 2:
                issues.append(f"{family} mock output omits matched growth episode {label}.")

        branch_reports = {}
        for payload in (anchor_output, comparison_output):
            branch_key = _branch_key(payload["branch_label"])
            cell_residuals = [
                item["objective_vector"]["Passaging.cellCount.seed_to_harvest_fold_change"]["residual"]
                for item in payload["episodes"]
                if item["objective_vector"]["Passaging.cellCount.seed_to_harvest_fold_change"]["residual"] is not None
            ]
            corrected_residuals = [
                item["objective_vector"]["Passaging.correctedCount.seed_to_harvest_fold_change"]["residual"]
                for item in payload["episodes"]
                if item["objective_vector"]["Passaging.correctedCount.seed_to_harvest_fold_change"]["residual"] is not None
            ]
            branch_reports[branch_key] = {
                "branch_id": payload["branch_id"],
                "branch_label": payload["branch_label"],
                "episode_count": len(payload["episodes"]),
                "mean_cellCount_fold_change_residual": (
                    sum(cell_residuals) / len(cell_residuals) if cell_residuals else None
                ),
                "mean_correctedCount_fold_change_residual": (
                    sum(corrected_residuals) / len(corrected_residuals) if corrected_residuals else None
                ),
            }

        report_families[family] = {
            "shared_objective": _shared_objective(plan),
            "branch_level_residuals": branch_reports,
            "matched_episode_labels": matched_labels,
            "endpoint_validation": {
                "Perspective.size": "validation_only_not_fitted",
            },
            "not_biological": True,
        }

    return {
        "report_version": "dry_run_mock_evaluation_report_v1",
        "comparison_id": matched_schedule["comparison_id"],
        "shared_objective_vector": _shared_objective(
            next(iter(families.values()))["evaluation_plan"]
        ),
        "families": report_families,
        "issues": issues,
        "passed": not issues,
        "notes": [
            "All outputs are deterministic mock artifacts only.",
            "Perspective.size remains endpoint validation only and is not used for fitting.",
            "prehistory_context remains excluded from executable runtime.",
            "transfer_events remain explicit reset or bottleneck events with zero growth duration.",
        ],
    }


def _markdown_static(payload: dict[str, Any]) -> str:
    lines = [
        "# Dry-Run Static Report",
        "",
        f"- Passed: `{payload['passed']}`",
        f"- Candidate root: `{payload['candidate_root']}`",
        f"- dry_run_physicell status: `{payload['dry_run_modes']['dry_run_physicell']}`",
        "",
        "## Shared objective",
        "",
    ]
    for key, value in payload["shared_objective_invariants"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Families", ""])
    for family, report in payload["family_validation"].items():
        lines.append(f"- `{family}` XML parse ok: `{report['config_xml_parse_ok']}`")
    if payload["issues"]:
        lines.extend(["", "## Issues", ""])
        for issue in payload["issues"]:
            lines.append(f"- {issue}")
    return "\n".join(lines) + "\n"


def _markdown_plan(payload: dict[str, Any]) -> str:
    lines = [
        "# Execution Harness Plan",
        "",
        f"- Comparison: `{payload['comparison_id']}`",
        f"- Candidate root: `{payload['candidate_root']}`",
        f"- Matched growth episodes: `{payload['matched_growth_episode_count']}`",
        "",
        "## Modes",
        "",
    ]
    for mode, spec in payload["modes"].items():
        lines.append(f"- `{mode}`: `{spec['status'] if 'status' in spec else spec['enabled']}`")
    lines.extend(
        [
            "",
            "## Invariants",
            "",
            f"- Perspective.size endpoint validation only: `{payload['invariants']['perspective_size_endpoint_validation_only']}`",
            f"- prehistory_context not executable: `{payload['invariants']['prehistory_context_not_executable']}`",
            f"- transfer_events not growth: `{payload['invariants']['transfer_events_are_reset_or_bottleneck_not_growth']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def _markdown_mock_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Dry-Run Mock Evaluation Report",
        "",
        f"- Passed: `{payload['passed']}`",
        f"- Comparison: `{payload['comparison_id']}`",
        f"- Families evaluated: `{', '.join(FAMILIES)}`",
        "",
        "## Family summaries",
        "",
    ]
    for family, report in payload["families"].items():
        lines.append(f"- `{family}` matched episodes: `{len(report['matched_episode_labels'])}`")
    if payload["issues"]:
        lines.extend(["", "## Issues", ""])
        for issue in payload["issues"]:
            lines.append(f"- {issue}")
    return "\n".join(lines) + "\n"


def generate_execution_harness_artifacts(
    *,
    anchor_schedule_path: str | Path,
    comparison_schedule_path: str | Path,
    matched_schedule_path: str | Path,
    candidate_root: str | Path,
    scaling_contract_path: str | Path,
    execution_readiness_path: str | Path,
    output_dir: str | Path,
) -> dict[str, Any]:
    anchor_schedule = _load_json(anchor_schedule_path)
    comparison_schedule = _load_json(comparison_schedule_path)
    matched_schedule = _load_json(matched_schedule_path)
    scaling_contract = _load_json(scaling_contract_path)
    execution_readiness_report = _load_json(execution_readiness_path)
    output_dir = Path(output_dir)

    plan = build_execution_harness_plan(
        candidate_root=candidate_root,
        scaling_contract=scaling_contract,
        execution_readiness_report=execution_readiness_report,
        matched_schedule=matched_schedule,
    )
    static_report = build_dry_run_static_report(
        candidate_root=candidate_root,
        scaling_contract=scaling_contract,
        execution_readiness_report=execution_readiness_report,
        anchor_schedule=anchor_schedule,
        comparison_schedule=comparison_schedule,
        matched_schedule=matched_schedule,
    )
    mock_index = build_dry_run_mock_outputs(
        candidate_root=candidate_root,
        scaling_contract=scaling_contract,
        anchor_schedule=anchor_schedule,
        comparison_schedule=comparison_schedule,
        matched_schedule=matched_schedule,
        output_dir=output_dir / "dry_run_mock_outputs",
    )
    mock_report = build_dry_run_mock_evaluation_report(
        candidate_root=candidate_root,
        matched_schedule=matched_schedule,
        mock_output_dir=output_dir / "dry_run_mock_outputs",
    )

    write_json(output_dir / "execution_harness_plan.json", plan)
    write_markdown(output_dir / "execution_harness_plan.md", _markdown_plan(plan))
    write_json(output_dir / "dry_run_static_report.json", static_report)
    write_markdown(output_dir / "dry_run_static_report.md", _markdown_static(static_report))
    write_json(output_dir / "dry_run_mock_evaluation_report.json", mock_report)
    write_markdown(output_dir / "dry_run_mock_evaluation_report.md", _markdown_mock_report(mock_report))

    return {
        "plan": plan,
        "static_report": static_report,
        "mock_index": mock_index,
        "mock_report": mock_report,
    }
