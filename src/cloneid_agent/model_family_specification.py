"""Schedule-aware model-family specification artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .run_io import write_json, write_markdown


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def _schedule_summary(schedule: dict[str, Any]) -> dict[str, Any]:
    return {
        "branch_id": schedule["branch_id"],
        "branch_label": schedule["branch_label"],
        "initial_condition_event_id": schedule["initial_condition"]["event_id"],
        "growth_episode_count": schedule["summary"]["growth_episode_count"],
        "transfer_event_count": schedule["summary"]["transfer_event_count"],
        "total_growth_simulated_minutes": schedule["summary"]["total_growth_simulated_minutes"],
        "terminal_endpoint_event_id": schedule["terminal_endpoint"]["event_id"],
        "terminal_perspective_supported_event_count": schedule["terminal_endpoint"][
            "terminal_perspective_supported_event_count"
        ],
        "terminal_perspective_record_count": schedule["terminal_endpoint"]["terminal_perspective_record_count"],
    }


def build_schedule_aware_model_family_specification(
    *,
    anchor_schedule: dict[str, Any],
    comparison_schedule: dict[str, Any],
    matched_schedule: dict[str, Any],
) -> dict[str, Any]:
    shared_calibration = [
        "Passaging.cellCount",
        "Passaging.correctedCount",
        "Passaging.areaOccupied_um2",
    ]
    endpoint_validation = "Perspective.size"
    anchor_summary = _schedule_summary(anchor_schedule)
    comparison_summary = _schedule_summary(comparison_schedule)

    families = [
        {
            "family_id": "neutral_growth",
            "scientific_meaning": "Same growth rule for 2N and 4N branches; differences arise only from observed initial conditions and transfer bottlenecks.",
            "required_physicell_features": [
                "single shared cell rule for both branches",
                "episode-wise initialization from schedule initial_condition",
                "external handling of transfer_events as reseeding / bottleneck resets",
                "time-series export at growth-episode endpoints",
            ],
            "required_input_observables": shared_calibration + [endpoint_validation],
            "parameters_to_expose": [
                {"name": "shared_proliferation_rate", "scope": "shared", "placeholder_only": True},
                {"name": "shared_death_rate", "scope": "shared", "placeholder_only": True},
                {"name": "shared_initial_cell_area", "scope": "shared", "placeholder_only": True},
            ],
            "shared_vs_branch_specific": {
                "shared": ["shared_proliferation_rate", "shared_death_rate", "shared_initial_cell_area"],
                "branch_specific": [],
            },
            "transfer_event_handling": "Apply observed transfer_events as external bottleneck/reseeding updates between growth episodes; do not simulate transfer as growth time.",
            "growth_episode_handling": "Simulate each growth_episode for fixed 1440 minutes, using observed start counts / area as initialization and observed end values as calibration targets.",
            "outputs_compared_to_cloneid": [
                "episode-end total cell count",
                "episode-end derived correctedCount proxy",
                "episode-end occupied area / density proxy",
            ],
            "primary_calibration_target": "Passaging.cellCount",
            "secondary_validation_targets": [
                "Passaging.correctedCount",
                "Passaging.areaOccupied_um2",
                "Perspective.size",
            ],
            "terminal_perspective_usage": "Use terminal Perspective.size only as endpoint support / validation, not as a growth-episode calibration signal.",
            "win_condition": "One shared growth program explains both 2N and 4N seed-to-harvest trajectories after applying observed transfer bottlenecks.",
            "failure_condition": "Systematic branch-specific trajectory mismatch remains after shared-parameter fitting, especially if 2N and 4N diverge in consistent opposite directions.",
            "assumptions": [
                "2N and 4N differ only in observed initialization and transfer history, not intrinsic growth law.",
                "Derived correctedCount and areaOccupied are acceptable event-linked phenotype targets.",
            ],
            "limitations": [
                "Cannot explain persistent ploidy-specific trajectory differences except through initial conditions.",
                "Perspective.size is only an endpoint check, so mid-course molecular divergence is ignored.",
            ],
        },
        {
            "family_id": "fixed_state_fitness",
            "scientific_meaning": "2N and 4N branches may require different intrinsic proliferation / death balance under otherwise matched O2 schedule structure.",
            "required_physicell_features": [
                "branch-specific cell rule parameters or cell definitions",
                "episode-wise initialization from schedule initial_condition",
                "external transfer-event reseeding between episodes",
                "time-series export at growth-episode endpoints",
            ],
            "required_input_observables": shared_calibration + [endpoint_validation],
            "parameters_to_expose": [
                {"name": "proliferation_rate_2N", "scope": "branch_specific", "branch": "2N", "placeholder_only": True},
                {"name": "proliferation_rate_4N", "scope": "branch_specific", "branch": "4N", "placeholder_only": True},
                {"name": "death_rate_2N", "scope": "branch_specific", "branch": "2N", "placeholder_only": True},
                {"name": "death_rate_4N", "scope": "branch_specific", "branch": "4N", "placeholder_only": True},
                {"name": "shared_initial_cell_area", "scope": "shared", "placeholder_only": True},
            ],
            "shared_vs_branch_specific": {
                "shared": ["shared_initial_cell_area"],
                "branch_specific": [
                    "proliferation_rate_2N",
                    "proliferation_rate_4N",
                    "death_rate_2N",
                    "death_rate_4N",
                ],
            },
            "transfer_event_handling": "Same as neutral_growth: apply observed transfer_events as non-growth bottleneck/reseeding resets between growth episodes.",
            "growth_episode_handling": "Simulate fixed 1440-minute growth episodes, but allow 2N and 4N branches to use different intrinsic fitness parameters across the whole matched window.",
            "outputs_compared_to_cloneid": [
                "episode-end total cell count",
                "episode-end derived correctedCount proxy",
                "episode-end occupied area / density proxy",
            ],
            "primary_calibration_target": "Passaging.correctedCount",
            "secondary_validation_targets": [
                "Passaging.cellCount",
                "Passaging.areaOccupied_um2",
                "Perspective.size",
            ],
            "terminal_perspective_usage": "Use terminal Perspective.size as endpoint support to judge whether branch-specific fitness differences remain biologically consistent at harvest.",
            "win_condition": "Branch-specific intrinsic parameters materially improve joint fit across matched episodes relative to neutral_growth.",
            "failure_condition": "Branch-specific parameters do not improve fit enough to justify extra degrees of freedom.",
            "assumptions": [
                "A stable ploidy-associated fitness difference can be represented by fixed branch-specific parameters.",
                "Transfer events do not themselves require branch-specific mechanistic modeling beyond the observed bottleneck.",
            ],
            "limitations": [
                "Branch labels stand in for biological state without modeling a dynamic switch mechanism.",
                "Could overfit if schedule differences are actually density- or environment-driven.",
            ],
        },
        {
            "family_id": "density_dependent_growth",
            "scientific_meaning": "Growth depends on density / confluence proxy, with areaOccupied_um2 used as the preferred schedule-aware crowding signal.",
            "required_physicell_features": [
                "density- or volume-fraction-dependent proliferation control",
                "episode-wise initialization from schedule initial_condition",
                "external transfer-event reseeding between episodes",
                "time-series export of cell count and occupancy-like outputs at growth-episode endpoints",
            ],
            "required_input_observables": shared_calibration + [endpoint_validation],
            "parameters_to_expose": [
                {"name": "shared_density_response_threshold", "scope": "shared", "placeholder_only": True},
                {"name": "shared_density_response_slope", "scope": "shared", "placeholder_only": True},
                {"name": "shared_baseline_proliferation_rate", "scope": "shared", "placeholder_only": True},
                {
                    "name": "optional_branch_specific_density_thresholds",
                    "scope": "optional_branch_specific",
                    "placeholder_only": True,
                },
            ],
            "shared_vs_branch_specific": {
                "shared": [
                    "shared_density_response_threshold",
                    "shared_density_response_slope",
                    "shared_baseline_proliferation_rate",
                ],
                "branch_specific": ["optional_branch_specific_density_thresholds"],
            },
            "transfer_event_handling": "Apply observed transfer_events as explicit reductions / resets in seeded cell burden and occupancy before the next growth episode.",
            "growth_episode_handling": "Simulate each 1440-minute growth episode with density-sensitive growth, comparing whether occupied area better explains the seed-to-harvest trajectory than fixed-rate growth.",
            "outputs_compared_to_cloneid": [
                "episode-end total cell count",
                "episode-end occupied area / density proxy",
                "episode-end derived correctedCount proxy",
            ],
            "primary_calibration_target": "Passaging.areaOccupied_um2",
            "secondary_validation_targets": [
                "Passaging.cellCount",
                "Passaging.correctedCount",
                "Perspective.size",
            ],
            "terminal_perspective_usage": "Use terminal Perspective.size only as endpoint support, not as the driver of the density response.",
            "win_condition": "Density-sensitive growth explains both cell-count and area trajectories better than fixed-rate models across the matched episodes.",
            "failure_condition": "Adding density dependence does not improve the joint count/area fit or only explains one branch.",
            "assumptions": [
                "areaOccupied_um2 is a useful proxy for crowding / density limitation in the matched O2 schedule.",
                "Density effects operate within each growth episode and transfer events reset occupancy between episodes.",
            ],
            "limitations": [
                "areaOccupied_um2 is derived and may not map perfectly onto the PhysiCell crowding variable.",
                "Branch-specific density response remains optional until justified by fit improvement.",
            ],
        },
    ]

    differentiation_checklist = [
        {
            "config_or_rule_surface": "cell phenotype proliferation / death rules",
            "neutral_growth": "shared parameters across 2N and 4N",
            "fixed_state_fitness": "branch-specific proliferation / death balance",
            "density_dependent_growth": "density-responsive proliferation with optional branch-specific thresholds",
        },
        {
            "config_or_rule_surface": "crowding / density response rule",
            "neutral_growth": "not required beyond baseline PhysiCell defaults",
            "fixed_state_fitness": "not primary driver",
            "density_dependent_growth": "must be explicitly enabled and parameterized",
        },
        {
            "config_or_rule_surface": "episode initialization inputs",
            "neutral_growth": "schedule initial_condition and transfer resets",
            "fixed_state_fitness": "same schedule inputs plus branch label",
            "density_dependent_growth": "same schedule inputs plus occupancy-sensitive initialization use",
        },
        {
            "config_or_rule_surface": "transfer-event handling",
            "neutral_growth": "external bottleneck / reseeding update",
            "fixed_state_fitness": "same external transfer update",
            "density_dependent_growth": "same external transfer update with occupancy reset preserved",
        },
        {
            "config_or_rule_surface": "primary calibration observable",
            "neutral_growth": "Passaging.cellCount",
            "fixed_state_fitness": "Passaging.correctedCount",
            "density_dependent_growth": "Passaging.areaOccupied_um2",
        },
    ]

    return {
        "specification_version": "schedule_aware_model_family_specification_v1",
        "comparison_id": matched_schedule["comparison_id"],
        "schedule_sources": {
            "anchor_schedule": anchor_summary,
            "comparison_schedule": comparison_summary,
            "matched_growth_episode_count": len(matched_schedule["matched_growth_episodes"]),
        },
        "observable_policy": {
            "joint_calibration_targets": shared_calibration,
            "terminal_endpoint_support": endpoint_validation,
            "identity_role": "secondary_inferred_support_only",
        },
        "families": families,
        "candidate_differentiation_checklist": differentiation_checklist,
        "recommended_next_step": "Use this memo to define family-specific XML/config/rules differences before any parameter fitting.",
        "no_fitted_parameter_values_yet": True,
    }


def write_schedule_aware_model_family_specification_json(path: str | Path, payload: dict[str, Any]) -> None:
    write_json(Path(path), payload)


def write_schedule_aware_model_family_specification_markdown(path: str | Path, payload: dict[str, Any]) -> None:
    lines = [
        "# Schedule-Aware Model Family Specification",
        "",
        f"- Comparison: `{payload['comparison_id']}`",
        f"- Anchor branch: `{payload['schedule_sources']['anchor_schedule']['branch_id']}`",
        f"- Comparison branch: `{payload['schedule_sources']['comparison_schedule']['branch_id']}`",
        f"- Matched growth episodes: `{payload['schedule_sources']['matched_growth_episode_count']}`",
        f"- No fitted parameter values yet: `{payload['no_fitted_parameter_values_yet']}`",
        "",
    ]
    for family in payload["families"]:
        lines.extend(
            [
                f"## {family['family_id']}",
                "",
                f"- Meaning: {family['scientific_meaning']}",
                f"- Primary calibration target: `{family['primary_calibration_target']}`",
                f"- Secondary validation targets: `{', '.join(family['secondary_validation_targets'])}`",
                f"- Transfer events: {family['transfer_event_handling']}",
                f"- Growth episodes: {family['growth_episode_handling']}",
                f"- Terminal Perspective.size: {family['terminal_perspective_usage']}",
                "",
                "### Exposed parameters",
                "",
            ]
        )
        for param in family["parameters_to_expose"]:
            scope = param["scope"]
            branch = param.get("branch")
            if branch:
                lines.append(f"- `{param['name']}` ({scope}, `{branch}`, placeholder)")
            else:
                lines.append(f"- `{param['name']}` ({scope}, placeholder)")
        lines.extend(
            [
                "",
                f"- Win condition: {family['win_condition']}",
                f"- Failure condition: {family['failure_condition']}",
                "",
            ]
        )
    lines.extend(["## Candidate Differentiation Checklist", ""])
    for item in payload["candidate_differentiation_checklist"]:
        lines.append(f"- `{item['config_or_rule_surface']}`")
        lines.append(f"  - neutral_growth: {item['neutral_growth']}")
        lines.append(f"  - fixed_state_fitness: {item['fixed_state_fitness']}")
        lines.append(f"  - density_dependent_growth: {item['density_dependent_growth']}")
    write_markdown(Path(path), "\n".join(lines) + "\n")
