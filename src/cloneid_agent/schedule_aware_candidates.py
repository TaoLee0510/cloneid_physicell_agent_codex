"""Generate schedule-aware family-specific PhysiCell candidate folders without fitting parameters."""

from __future__ import annotations

import json
from copy import deepcopy
import hashlib
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

from .model_candidate import DEFAULT_PHYSICELL_ROOT
from .run_io import write_json, write_markdown

DEFAULT_SCHEDULE_AWARE_CANDIDATE_DIR = "model_candidates_schedule_aware"

SHARED_EVALUATION_OBJECTIVE = {
    "primary_shared_objective": {
        "description": "Passaging.cellCount and Passaging.correctedCount seed-to-harvest fold changes across all matched growth episodes in both 2N and 4N branches.",
        "fit_targets": [
            "Passaging.cellCount.seed_to_harvest_fold_change",
            "Passaging.correctedCount.seed_to_harvest_fold_change",
        ],
    },
    "secondary_objective": {
        "description": "Passaging.areaOccupied_um2 / confluence-like trajectory agreement across matched growth episodes.",
        "validation_targets": [
            "Passaging.areaOccupied_um2.episode_end_value",
            "Passaging.areaOccupied_um2.seed_to_harvest_fold_change",
        ],
    },
    "endpoint_validation": {
        "description": "Perspective.size at O2_A7K_harvest only; validation only, not fitting.",
        "validation_targets": ["Perspective.size"],
        "fitting_targets": [],
    },
}


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def _load_base_config(physicell_root: str | Path) -> ET.ElementTree:
    config_path = Path(physicell_root) / "config" / "PhysiCell_settings.xml"
    if not config_path.exists():
        raise FileNotFoundError(f"PhysiCell config not found: {config_path}")
    return ET.parse(config_path)


def _ensure_user_parameters(root: ET.Element) -> ET.Element:
    node = root.find("./user_parameters")
    if node is None:
        node = ET.SubElement(root, "user_parameters")
    for child in list(node):
        node.remove(child)
    return node


def _set_or_create_text(root: ET.Element, path: str, text: str) -> None:
    node = root.find(path)
    if node is None:
        parts = [part for part in path.strip("./").split("/") if part]
        cursor = root
        for part in parts:
            next_node = cursor.find(part)
            if next_node is None:
                next_node = ET.SubElement(cursor, part)
            cursor = next_node
        node = cursor
    node.text = text


def _parameter_element(parent: ET.Element, name: str, value: str, units: str, description: str) -> None:
    node = ET.SubElement(parent, name)
    node.set("units", units)
    node.set("description", description)
    node.text = value


def _family_parameter_payloads() -> dict[str, dict[str, Any]]:
    return {
        "neutral_growth": {
            "family_rule_mode": "shared_growth_rules_across_branches",
            "placeholder_parameters": {
                "shared_proliferation_rate": {"value": "UNFITTED_PLACEHOLDER", "units": "1/min"},
                "shared_death_rate": {"value": "UNFITTED_PLACEHOLDER", "units": "1/min"},
                "shared_initial_cell_area": {"value": "UNFITTED_PLACEHOLDER", "units": "micron^2"},
            },
            "rules": [
                "Use identical proliferation/death rule structure for 2N and 4N branches.",
                "Apply observed transfer-event bottlenecks externally between episodes.",
            ],
        },
        "fixed_state_fitness": {
            "family_rule_mode": "branch_specific_fitness_parameters",
            "placeholder_parameters": {
                "proliferation_rate_2N": {"value": "UNFITTED_PLACEHOLDER", "units": "1/min"},
                "proliferation_rate_4N": {"value": "UNFITTED_PLACEHOLDER", "units": "1/min"},
                "death_rate_2N": {"value": "UNFITTED_PLACEHOLDER", "units": "1/min"},
                "death_rate_4N": {"value": "UNFITTED_PLACEHOLDER", "units": "1/min"},
                "shared_initial_cell_area": {"value": "UNFITTED_PLACEHOLDER", "units": "micron^2"},
            },
            "rules": [
                "Use branch-specific proliferation/death placeholders for 2N and 4N.",
                "Do not introduce density dependence as the main mechanism.",
                "Apply observed transfer-event bottlenecks externally between episodes.",
            ],
        },
        "density_dependent_growth": {
            "family_rule_mode": "shared_density_dependent_growth",
            "placeholder_parameters": {
                "shared_baseline_proliferation_rate": {"value": "UNFITTED_PLACEHOLDER", "units": "1/min"},
                "shared_death_rate": {"value": "UNFITTED_PLACEHOLDER", "units": "1/min"},
                "density_response_threshold": {"value": "UNFITTED_PLACEHOLDER", "units": "relative_area_proxy"},
                "density_response_slope": {"value": "UNFITTED_PLACEHOLDER", "units": "1/relative_area_proxy"},
                "area_proxy_mode": {"value": "areaOccupied_um2", "units": "label"},
            },
            "rules": [
                "Use density/confluence-linked growth modulation informed by areaOccupied_um2.",
                "Avoid branch-specific density parameters initially.",
                "Apply observed transfer-event bottlenecks externally between episodes.",
            ],
        },
    }


def _branch_schedule_summary(schedule: dict[str, Any]) -> dict[str, Any]:
    return {
        "branch_id": schedule["branch_id"],
        "branch_label": schedule["branch_label"],
        "initial_condition": schedule["initial_condition"],
        "growth_episode_count": schedule["summary"]["growth_episode_count"],
        "transfer_event_count": schedule["summary"]["transfer_event_count"],
        "terminal_endpoint": schedule["terminal_endpoint"],
    }


def _build_schedule_mapping(
    *,
    anchor_schedule: dict[str, Any],
    comparison_schedule: dict[str, Any],
    matched_schedule: dict[str, Any],
) -> dict[str, Any]:
    return {
        "comparison_id": matched_schedule["comparison_id"],
        "prehistory_context_policy": {
            "simulation_role": "context_only_not_simulated",
            "excluded_from_primary_runtime": True,
        },
        "branches": {
            "anchor": _branch_schedule_summary(anchor_schedule),
            "comparison": _branch_schedule_summary(comparison_schedule),
        },
        "matched_growth_episode_labels": [
            item["milestone_label"] for item in matched_schedule["matched_growth_episodes"]
        ],
        "transfer_event_policy": {
            "simulation_role": "explicit_reset_or_bottleneck",
            "simulated_duration_minutes": 0,
            "use_observed_bottleneck_ratios_when_available": True,
        },
    }


def _build_evaluation_plan(family: str, matched_schedule: dict[str, Any]) -> dict[str, Any]:
    plan = deepcopy(SHARED_EVALUATION_OBJECTIVE)
    plan["family_id"] = family
    plan["matched_growth_episode_labels"] = [
        item["milestone_label"] for item in matched_schedule["matched_growth_episodes"]
    ]
    plan["required_outputs"] = [
        "simulated episode-end cell count",
        "simulated seed-to-harvest fold change",
        "simulated area/density proxy where available",
        "branch-level residuals for 2N and 4N",
        "matched-episode residuals",
        "terminal endpoint validation against Perspective.size metadata only",
    ]
    plan["not_yet_fitted"] = True
    return plan


def _build_manifest(
    *,
    family: str,
    family_spec: dict[str, Any],
    candidate_dir: Path,
    config_path: Path,
    schedule_mapping_path: Path,
    evaluation_plan_path: Path,
    parameter_placeholders_path: Path,
    physicell_root: Path,
) -> dict[str, Any]:
    return {
        "candidate_id": family,
        "family": family,
        "mechanistic_hypothesis": family_spec["scientific_meaning"],
        "family_rule_mode": family_spec["family_rule_mode"],
        "shared_evaluation_objective": deepcopy(SHARED_EVALUATION_OBJECTIVE),
        "schedule_mapping_path": str(schedule_mapping_path),
        "evaluation_plan_path": str(evaluation_plan_path),
        "parameter_placeholders_path": str(parameter_placeholders_path),
        "config_path": str(config_path),
        "candidate_dir": str(candidate_dir),
        "physicell_root": str(physicell_root),
        "physicell_executable": str(physicell_root / "heterogeneity"),
        "prehistory_context_executable": False,
        "transfer_events_simulated_as_growth": False,
        "perspective_size_used_for_fitting": False,
        "not_yet_fitted": True,
        "runnable_status": "config_ready_placeholder_parameters_only",
    }


def _update_config_tree(
    tree: ET.ElementTree,
    *,
    family: str,
    candidate_output_dir: Path,
    total_runtime_minutes: int,
    family_spec: dict[str, Any],
) -> ET.ElementTree:
    root = tree.getroot()
    _set_or_create_text(root, "./overall/max_time", str(total_runtime_minutes))
    _set_or_create_text(root, "./parallel/omp_num_threads", "1")
    _set_or_create_text(root, "./save/folder", str(candidate_output_dir / "simulation_output"))
    user_parameters = _ensure_user_parameters(root)
    _parameter_element(
        user_parameters,
        "candidate_family",
        family,
        "dimensionless",
        "Schedule-aware family identifier.",
    )
    _parameter_element(
        user_parameters,
        "family_rule_mode",
        family_spec["family_rule_mode"],
        "dimensionless",
        "Placeholder rule mode; not yet fitted.",
    )
    _parameter_element(
        user_parameters,
        "transfer_event_mode",
        "explicit_bottleneck_reset_not_growth",
        "dimensionless",
        "Transfer events are not simulated as growth time.",
    )
    _parameter_element(
        user_parameters,
        "shared_evaluation_objective_id",
        "shared_seed_to_harvest_fold_change_objective",
        "dimensionless",
        "All families share the same evaluation objective vector.",
    )
    for name, spec in family_spec["placeholder_parameters"].items():
        _parameter_element(
            user_parameters,
            name,
            spec["value"],
            spec["units"],
            "UNFITTED placeholder parameter.",
        )
    return tree


def generate_schedule_aware_model_candidates(
    *,
    anchor_schedule: dict[str, Any],
    comparison_schedule: dict[str, Any],
    matched_schedule: dict[str, Any],
    specification_payload: dict[str, Any],
    output_dir: str | Path,
    physicell_root: str | Path | None = None,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    candidate_root = output_dir / DEFAULT_SCHEDULE_AWARE_CANDIDATE_DIR
    candidate_root.mkdir(parents=True, exist_ok=True)
    physicell_root = Path(DEFAULT_PHYSICELL_ROOT if physicell_root is None else physicell_root)
    executable = physicell_root / "heterogeneity"
    if not executable.exists():
        raise FileNotFoundError(f"PhysiCell executable not found: {executable}")

    prehistory_entries = anchor_schedule["prehistory_context"] + comparison_schedule["prehistory_context"]
    if any(item.get("simulated_duration_minutes") not in (None,) for item in prehistory_entries):
        raise ValueError("prehistory_context must not have executable simulated duration")
    if any(item.get("excluded_from_primary_runtime") is not True for item in prehistory_entries):
        raise ValueError("prehistory_context must be excluded from primary runtime")
    if any(item.get("simulation_role") != "context_only_not_simulated" for item in prehistory_entries):
        raise ValueError("prehistory_context must be marked context_only_not_simulated")

    family_specs = {item["family_id"]: item for item in specification_payload["families"]}
    total_runtime_minutes = max(
        int(anchor_schedule["summary"]["total_growth_simulated_minutes"]),
        int(comparison_schedule["summary"]["total_growth_simulated_minutes"]),
    )

    candidates: list[dict[str, Any]] = []
    for family in ("neutral_growth", "fixed_state_fitness", "density_dependent_growth"):
        family_spec = family_specs[family]
        family_dir = candidate_root / family
        config_dir = family_dir / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "PhysiCell_settings.xml"
        tree = _load_base_config(physicell_root)
        _update_config_tree(
            tree,
            family=family,
            candidate_output_dir=family_dir,
            total_runtime_minutes=total_runtime_minutes,
            family_spec=family_spec,
        )
        tree.write(config_path, encoding="utf-8", xml_declaration=False)

        schedule_mapping = _build_schedule_mapping(
            anchor_schedule=anchor_schedule,
            comparison_schedule=comparison_schedule,
            matched_schedule=matched_schedule,
        )
        evaluation_plan = _build_evaluation_plan(family, matched_schedule)
        parameter_placeholders = {
            "family_id": family,
            "family_rule_mode": family_spec["family_rule_mode"],
            "placeholder_parameters": family_spec["placeholder_parameters"],
            "not_yet_fitted": True,
        }

        schedule_mapping_path = family_dir / "schedule_mapping.json"
        evaluation_plan_path = family_dir / "evaluation_plan.json"
        parameter_placeholders_path = family_dir / "parameter_placeholders.json"
        write_json(schedule_mapping_path, schedule_mapping)
        write_json(evaluation_plan_path, evaluation_plan)
        write_json(parameter_placeholders_path, parameter_placeholders)

        manifest = _build_manifest(
            family=family,
            family_spec=family_spec,
            candidate_dir=family_dir,
            config_path=config_path,
            schedule_mapping_path=schedule_mapping_path,
            evaluation_plan_path=evaluation_plan_path,
            parameter_placeholders_path=parameter_placeholders_path,
            physicell_root=physicell_root,
        )
        write_json(family_dir / "candidate_manifest.json", manifest)
        readme_lines = [
            f"# {family}",
            "",
            f"- Mechanistic hypothesis: {family_spec['scientific_meaning']}",
            f"- Family rule mode: `{family_spec['family_rule_mode']}`",
            "- Parameter values are placeholders only.",
            "- Transfer events are explicit resets, not growth.",
            "- Perspective.size is endpoint validation only.",
            "- Model comparison is not yet fitted.",
        ]
        write_markdown(family_dir / "README.md", "\n".join(readme_lines) + "\n")
        candidates.append(manifest)

    report = build_candidate_differentiation_report(
        candidate_root=candidate_root,
        candidates=candidates,
        specification_payload=specification_payload,
    )
    write_json(candidate_root / "candidate_differentiation_report.json", report)
    write_markdown(candidate_root / "candidate_differentiation_report.md", render_candidate_differentiation_report(report))

    return {
        "candidate_root": str(candidate_root),
        "candidates": candidates,
        "candidate_differentiation_report": report,
        "not_yet_fitted": True,
    }


def build_candidate_differentiation_report(
    *,
    candidate_root: Path,
    candidates: list[dict[str, Any]],
    specification_payload: dict[str, Any],
) -> dict[str, Any]:
    family_specs = {item["family_id"]: item for item in specification_payload["families"]}
    family_parameters = {
        family: sorted(list(family_specs[family]["placeholder_parameters"].keys()))
        for family in family_specs
    }
    family_rules = {family: family_specs[family]["rules"] for family in family_specs}
    shared_eval = deepcopy(SHARED_EVALUATION_OBJECTIVE)
    runnable = all(Path(item["config_path"]).exists() for item in candidates)
    relative_files = [
        "config/PhysiCell_settings.xml",
        "candidate_manifest.json",
        "README.md",
        "schedule_mapping.json",
        "evaluation_plan.json",
        "parameter_placeholders.json",
    ]
    file_differences: dict[str, dict[str, Any]] = {}
    for rel in relative_files:
        hashes = {}
        for item in candidates:
            family = item["family"]
            data = (candidate_root / family / rel).read_bytes()
            hashes[family] = hashlib.sha256(data).hexdigest()
        unique_hashes = sorted(set(hashes.values()))
        file_differences[rel] = {
            "differs_across_candidates": len(unique_hashes) > 1,
            "hashes_by_family": hashes,
        }
    return {
        "candidate_root": str(candidate_root),
        "files_present_per_candidate": {
            item["family"]: [
                "config/PhysiCell_settings.xml",
                "candidate_manifest.json",
                "README.md",
                "schedule_mapping.json",
                "evaluation_plan.json",
                "parameter_placeholders.json",
            ]
            for item in candidates
        },
        "parameters_by_family": family_parameters,
        "rules_by_family": family_rules,
        "placeholder_parameters_by_family": family_parameters,
        "file_differences": file_differences,
        "shared_evaluation_objective": shared_eval,
        "perspective_size_used_for_fitting": False,
        "not_yet_fitted": True,
        "runnable": runnable,
        "what_remains_before_biological_interpretation_is_legitimate": [
            "Implement family-specific XML/config/rules execution semantics beyond placeholders.",
            "Add parameter search or fitting on the shared objective vector.",
            "Run the candidates and compute matched-episode residuals.",
            "Verify that terminal Perspective.size remains validation-only.",
        ],
    }


def render_candidate_differentiation_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Candidate Differentiation Report",
        "",
        f"- Candidate root: `{payload['candidate_root']}`",
        f"- Runnable: `{payload['runnable']}`",
        f"- Model comparison still not yet fitted: `{payload['not_yet_fitted']}`",
        f"- Perspective.size used for fitting: `{payload['perspective_size_used_for_fitting']}`",
        "",
        "## Parameters by family",
        "",
    ]
    for family, params in payload["parameters_by_family"].items():
        lines.append(f"- `{family}`: `{', '.join(params)}`")
    lines.extend(["", "## File differences", ""])
    for rel, details in payload["file_differences"].items():
        lines.append(f"- `{rel}` differs across candidates: `{details['differs_across_candidates']}`")
    lines.extend(["", "## Rules by family", ""])
    for family, rules in payload["rules_by_family"].items():
        lines.append(f"- `{family}`")
        for rule in rules:
            lines.append(f"  - {rule}")
    lines.extend(["", "## Shared evaluation objective", ""])
    lines.append(
        f"- Primary: `{', '.join(payload['shared_evaluation_objective']['primary_shared_objective']['fit_targets'])}`"
    )
    lines.append(
        f"- Secondary: `{', '.join(payload['shared_evaluation_objective']['secondary_objective']['validation_targets'])}`"
    )
    lines.append(
        f"- Endpoint validation only: `{', '.join(payload['shared_evaluation_objective']['endpoint_validation']['validation_targets'])}`"
    )
    lines.extend(["", "## Remaining before biological interpretation", ""])
    for item in payload["what_remains_before_biological_interpretation_is_legitimate"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def generate_schedule_aware_model_candidates_from_files(
    *,
    anchor_schedule_path: str | Path,
    comparison_schedule_path: str | Path,
    matched_schedule_path: str | Path,
    specification_path: str | Path,
    output_dir: str | Path,
    physicell_root: str | Path | None = None,
) -> dict[str, Any]:
    return generate_schedule_aware_model_candidates(
        anchor_schedule=_load_json(anchor_schedule_path),
        comparison_schedule=_load_json(comparison_schedule_path),
        matched_schedule=_load_json(matched_schedule_path),
        specification_payload=_load_json(specification_path),
        output_dir=output_dir,
        physicell_root=physicell_root,
    )
