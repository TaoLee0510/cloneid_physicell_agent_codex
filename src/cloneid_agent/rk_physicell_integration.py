"""PhysiCell-facing r/K benchmark input generation and comparison."""

from __future__ import annotations

import csv
import math
from pathlib import Path
import shutil
import subprocess
from typing import Any
import xml.etree.ElementTree as ET

from .rk_density_models import MANUSCRIPT_MODEL_FAMILIES
from .run_io import write_json, write_markdown


PHYSICELL_DATA_FIELDS = (
    "branch_labels",
    "growth_rate_or_count_targets",
    "event_linked_seed_harvest_episodes",
    "transfer_reset_semantics",
    "elapsed_time_per_episode",
    "event_linked_confluence_or_area",
    "carrying_capacity_or_density_prior",
    "raw_image_or_segmentation_provenance",
    "endpoint_perspective_anchor",
)

FIELD_WEIGHTS = {
    "branch_labels": 1,
    "growth_rate_or_count_targets": 2,
    "event_linked_seed_harvest_episodes": 3,
    "transfer_reset_semantics": 3,
    "elapsed_time_per_episode": 2,
    "event_linked_confluence_or_area": 4,
    "carrying_capacity_or_density_prior": 2,
    "raw_image_or_segmentation_provenance": 2,
    "endpoint_perspective_anchor": 1,
}

FAMILY_REQUIREMENTS = {
    "neutral_growth": {
        "required": ("growth_rate_or_count_targets",),
        "preferred": ("event_linked_seed_harvest_episodes", "elapsed_time_per_episode"),
        "physicell_rule_surface": "shared proliferation/death rule; no branch advantage; no density-history term",
    },
    "fixed_state_fitness": {
        "required": ("branch_labels", "growth_rate_or_count_targets"),
        "preferred": ("event_linked_seed_harvest_episodes", "elapsed_time_per_episode"),
        "physicell_rule_surface": "r/K branch-specific proliferation/death parameters; no density-history term",
    },
    "density_dependent_growth": {
        "required": (
            "event_linked_seed_harvest_episodes",
            "transfer_reset_semantics",
            "elapsed_time_per_episode",
            "event_linked_confluence_or_area",
        ),
        "preferred": ("raw_image_or_segmentation_provenance", "endpoint_perspective_anchor"),
        "physicell_rule_surface": "growth modulated by event-linked confluence/area history with transfer resets",
    },
}

PHYSICELL_ROOT_CANDIDATES = (
    "/Users/4482173/Documents/PhysiCell",
    "/Users/4482173/Downloads/PhysiCell-1.14.2",
    "/Users/4470246/Downloads/PhysiCell-1.14.2",
)

PHYSICELL_EXECUTABLE_CANDIDATES = (
    "heterogeneity",
    "ode_energy",
    "project",
)

PHYSICELL_SOURCE_CONFIG_CANDIDATES = (
    ("sample_projects", "{executable}", "config", "PhysiCell_settings.xml"),
    ("sample_projects_intracellular", "ode", "{executable}", "config", "PhysiCell_settings.xml"),
    ("sample_projects_intracellular", "fba", "{executable}", "config", "PhysiCell_settings.xml"),
    ("config", "PhysiCell_settings.xml"),
)


def _format_list(values: list[str] | tuple[str, ...] | None) -> str:
    return ", ".join(values or ["none"])


def _safe_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _ceil_agent_count(cell_count: Any, cells_per_agent: int) -> int | None:
    numeric = _safe_float(cell_count)
    if numeric is None:
        return None
    return max(1, int(math.ceil(numeric / float(cells_per_agent))))


def _estimate_runtime_tumor_radius(initial_agent_count: int) -> float:
    """Choose a small executable 2D tumor radius from the CLONEID-derived agent count."""

    estimated = math.sqrt(max(initial_agent_count, 1)) * 8.5
    return round(min(120.0, max(30.0, estimated)), 3)


def _resolve_path_against_root(path: str | Path | None, root: Path | None) -> Path | None:
    if path is None:
        return None
    candidate = Path(path)
    if not candidate.is_absolute() and root is not None:
        candidate = root / candidate
    return candidate if candidate.exists() else None


def _resolve_physicell_executable(
    physicell_root: Path | None,
    executable: str | Path | None = None,
) -> Path | None:
    explicit = _resolve_path_against_root(executable, physicell_root)
    if explicit is not None:
        return explicit
    if physicell_root is None:
        return None
    for name in PHYSICELL_EXECUTABLE_CANDIDATES:
        candidate = physicell_root / name
        if candidate.exists():
            return candidate
    return None


def _resolve_physicell_source_config(
    physicell_root: Path | None,
    executable: Path | None,
    source_config: str | Path | None = None,
) -> Path | None:
    explicit = _resolve_path_against_root(source_config, physicell_root)
    if explicit is not None:
        return explicit
    if physicell_root is None:
        return None
    executable_name = executable.name if executable is not None else "heterogeneity"
    for parts in PHYSICELL_SOURCE_CONFIG_CANDIDATES:
        candidate = physicell_root.joinpath(*(part.format(executable=executable_name) for part in parts))
        if candidate.exists():
            return candidate
    return None


def resolve_physicell_root(physicell_root: str | Path | None) -> Path | None:
    """Resolve an optional local PhysiCell root without requiring it."""

    candidates = [Path(physicell_root)] if physicell_root else []
    candidates.extend(Path(item) for item in PHYSICELL_ROOT_CANDIDATES)
    for candidate in candidates:
        executable = _resolve_physicell_executable(candidate)
        source_config = _resolve_physicell_source_config(candidate, executable)
        if executable is not None and source_config is not None:
            return candidate
    return None


def _full_history_schedule(
    growth_episodes: list[dict[str, Any]],
    event_schedule: dict[str, Any],
    perspective_table: list[dict[str, Any]],
    *,
    cells_per_agent: int,
) -> dict[str, Any]:
    episodes = []
    for row in growth_episodes:
        seed_count = row.get("seed_corrected_count", row.get("seeded_cell_count"))
        harvest_count = row.get("harvest_corrected_count", row.get("harvested_cell_count"))
        episodes.append(
            {
                "episode_id": row["episode_id"],
                "seed_event_id": row["seed_event_id"],
                "harvest_event_id": row["harvest_event_id"],
                "branch_label": row["branch_label"],
                "passage_number": row["passage_number"],
                "duration_hours": row["duration_hours"],
                "initial_agent_count": _ceil_agent_count(seed_count, cells_per_agent),
                "target_harvest_agent_count": _ceil_agent_count(harvest_count, cells_per_agent),
                "observed_seed_count": seed_count,
                "observed_harvest_count": harvest_count,
                "seed_confluence_proxy": row.get("seed_confluence_proxy"),
                "harvest_confluence_proxy": row.get("harvest_confluence_proxy"),
                "seed_areaOccupied_um2": row.get("seed_areaOccupied_um2"),
                "harvest_areaOccupied_um2": row.get("harvest_areaOccupied_um2"),
                "growth_rate_per_hour": row.get("growth_rate_per_hour"),
                "simulation_role": "growth_episode",
            }
        )
    transfer_events = [
        {
            "event_id": row["event_id"],
            "parent_event_id": row.get("parent_event_id"),
            "branch_label": row.get("branch_label"),
            "cellCount": row.get("cellCount"),
            "correctedCount": row.get("correctedCount"),
            "confluence_proxy": row.get("confluence_proxy"),
            "simulation_role": "transfer_reset_not_growth",
        }
        for row in event_schedule.get("events", [])
        if row.get("schedule_classification") == "transfer_or_bottleneck"
    ]
    return {
        "schedule_version": "rk_physicell_full_history_schedule_v1",
        "regime_id": "snu668_full_history",
        "cells_per_agent": cells_per_agent,
        "episode_resolution": "event_linked_seed_harvest_growth_episodes",
        "growth_episodes": episodes,
        "transfer_events": transfer_events,
        "endpoint_perspective_support": perspective_table,
        "guardrails": [
            "Transfer events are reset/bottleneck records, not growth intervals.",
            "Endpoint Perspective is validation/support only, not a fitting target.",
        ],
    }


def _compressed_schedule(coarse_record: dict[str, Any], *, cells_per_agent: int) -> dict[str, Any]:
    pseudo_episodes = []
    for row in coarse_record.get("coarse_growth_summary", []):
        pseudo_episodes.append(
            {
                "branch_label": row.get("branch_label"),
                "episode_count": row.get("episode_count"),
                "mean_growth_rate_per_hour": row.get("mean_growth_rate_per_hour"),
                "mean_fold_change": row.get("mean_fold_change"),
                "simulation_role": "publication_like_summary_target",
                "event_ids_available": False,
                "density_history_available": False,
            }
        )
    return {
        "schedule_version": "rk_physicell_publication_like_compressed_schedule_v1",
        "regime_id": "snu668_published_like_compressed",
        "cells_per_agent": cells_per_agent,
        "episode_resolution": "branch_level_summary_only",
        "pseudo_episodes": pseudo_episodes,
        "missing_for_physicell": [
            "event-linked seed/harvest episodes",
            "transfer reset order",
            "elapsed time per episode",
            "event-linked confluence or area history",
            "Perspective-to-event linkage",
        ],
    }


def _nsr_schedule(external_record: dict[str, Any], *, cells_per_agent: int) -> dict[str, Any]:
    model_records = external_record.get("model_records", {})
    return {
        "schedule_version": "rk_physicell_nsr_publication_level_schedule_v1",
        "regime_id": "nwaa124_curated_external",
        "cells_per_agent": cells_per_agent,
        "episode_resolution": "publication_level_reconstruction",
        "growth_rate_distributions": external_record.get("growth_summary", []),
        "carrying_capacity_records": model_records.get("carrying_capacity_logistic_formulas", []),
        "growth_model_fit_statistics": model_records.get("growth_model_fit_statistics", []),
        "mixed_population_evidence": external_record.get("competition_inputs", []),
        "missing_for_physicell": [
            "native event ledger",
            "seed-to-harvest event pairs",
            "transfer reset order",
            "event-linked confluence history",
            "raw numeric mixed-population trajectories unless deterministic digitization is added",
        ],
        "guardrail": "NSR is a strong publication-level r/K comparator; plot-only evidence is not treated as raw PhysiCell calibration data.",
    }


def _availability_for_regime(regime_id: str, schedule: dict[str, Any]) -> dict[str, bool]:
    if regime_id == "snu668_full_history":
        episodes = schedule.get("growth_episodes", [])
        density_ready = bool(episodes) and all(
            row.get("seed_confluence_proxy") not in (None, "") for row in episodes
        )
        return {
            "branch_labels": bool({row.get("branch_label") for row in episodes}),
            "growth_rate_or_count_targets": bool(episodes),
            "event_linked_seed_harvest_episodes": bool(episodes),
            "transfer_reset_semantics": bool(schedule.get("transfer_events")),
            "elapsed_time_per_episode": bool(episodes) and all(row.get("duration_hours") for row in episodes),
            "event_linked_confluence_or_area": density_ready,
            "carrying_capacity_or_density_prior": density_ready,
            "raw_image_or_segmentation_provenance": True,
            "endpoint_perspective_anchor": bool(schedule.get("endpoint_perspective_support")),
        }
    if regime_id == "snu668_published_like_compressed":
        return {
            "branch_labels": True,
            "growth_rate_or_count_targets": bool(schedule.get("pseudo_episodes")),
            "event_linked_seed_harvest_episodes": False,
            "transfer_reset_semantics": False,
            "elapsed_time_per_episode": False,
            "event_linked_confluence_or_area": False,
            "carrying_capacity_or_density_prior": False,
            "raw_image_or_segmentation_provenance": False,
            "endpoint_perspective_anchor": False,
        }
    return {
        "branch_labels": bool(schedule.get("growth_rate_distributions")),
        "growth_rate_or_count_targets": bool(schedule.get("growth_rate_distributions")),
        "event_linked_seed_harvest_episodes": False,
        "transfer_reset_semantics": False,
        "elapsed_time_per_episode": False,
        "event_linked_confluence_or_area": False,
        "carrying_capacity_or_density_prior": bool(schedule.get("carrying_capacity_records")),
        "raw_image_or_segmentation_provenance": False,
        "endpoint_perspective_anchor": False,
    }


def _regime_score(availability: dict[str, bool]) -> int:
    return sum(FIELD_WEIGHTS[field] for field, present in availability.items() if present)


def _family_status(regime_id: str, family_id: str, availability: dict[str, bool]) -> dict[str, Any]:
    requirements = FAMILY_REQUIREMENTS[family_id]
    missing_required = [field for field in requirements["required"] if not availability.get(field, False)]
    missing_preferred = [field for field in requirements["preferred"] if not availability.get(field, False)]
    if not missing_required and regime_id == "snu668_full_history":
        status = "physicell_event_schedule_configurable"
        interpretation = "can be encoded as an event-linked PhysiCell candidate from native CLONEID records"
    elif not missing_required:
        status = "physicell_summary_or_prior_only"
        interpretation = "can inform coarse PhysiCell priors or summary targets, but not an event-level schedule"
    elif family_id == "density_dependent_growth":
        status = "not_identifiable_for_physicell_density_history"
        interpretation = "missing event-linked density/confluence history and transfer reset order"
    else:
        status = "underconstrained_for_physicell_calibration"
        interpretation = "missing inputs prevent auditable candidate calibration"
    return {
        "family_id": family_id,
        "physicell_rule_surface": requirements["physicell_rule_surface"],
        "encoding_status": status,
        "required_inputs_available": [field for field in requirements["required"] if availability.get(field, False)],
        "required_inputs_missing": missing_required,
        "preferred_inputs_missing": missing_preferred,
        "interpretation": interpretation,
    }


def _write_csv(path: str | Path, rows: list[dict[str, Any]]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else ["dataset_regime"]
    with target.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return target


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


def _set_parameter(
    root: ET.Element,
    name: str,
    value: str,
    description: str,
    *,
    parameter_type: str = "string",
    units: str = "dimensionless",
) -> None:
    user_parameters = root.find("./user_parameters")
    if user_parameters is None:
        user_parameters = ET.SubElement(root, "user_parameters")
    existing = user_parameters.find(name)
    if existing is not None:
        user_parameters.remove(existing)
    node = ET.SubElement(user_parameters, name)
    node.set("type", parameter_type)
    node.set("units", units)
    node.set("description", description)
    node.text = value


def _ensure_cancer_cell_definition(root: ET.Element) -> None:
    cell_definitions = root.find("./cell_definitions")
    if cell_definitions is None:
        return
    if cell_definitions.find("./cell_definition[@name='cancer cell']") is not None:
        return
    default_definition = cell_definitions.find("./cell_definition[@name='default']")
    if default_definition is None:
        return
    cancer_definition = ET.fromstring(ET.tostring(default_definition, encoding="unicode"))
    cancer_definition.set("name", "cancer cell")
    cancer_definition.set("ID", "1")
    cell_definitions.append(cancer_definition)


def _write_candidate_config(
    *,
    family: dict[str, Any],
    regime_id: str,
    family_id: str,
    output_dir: Path,
    physicell_root: Path | None,
    physicell_executable: Path | None,
    physicell_source_config: Path | None,
    runtime_max_time: int,
    runtime_initial_agent_count: int,
) -> dict[str, Any]:
    family_dir = output_dir / "candidate_configs" / regime_id / family_id
    config_dir = family_dir / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "candidate_id": f"{regime_id}__{family_id}",
        "dataset_regime": regime_id,
        "family_id": family_id,
        "encoding_status": family["encoding_status"],
        "physicell_rule_surface": family["physicell_rule_surface"],
        "required_inputs_available": family["required_inputs_available"],
        "required_inputs_missing": family["required_inputs_missing"],
        "runnable_status": "manifest_only_no_physicell_root",
        "config_path": None,
        "source_config_path": None,
        "execution_guardrail": "Candidate configs encode input resolution and rule surfaces; biological conclusions require calibrated custom PhysiCell rules.",
    }
    if physicell_root is not None and physicell_executable is not None and physicell_source_config is not None:
        source_config = physicell_source_config
        target_config = config_dir / "PhysiCell_settings.xml"
        shutil.copy2(source_config, target_config)
        tree = ET.parse(target_config)
        root = tree.getroot()
        _ensure_cancer_cell_definition(root)
        runtime_tumor_radius = _estimate_runtime_tumor_radius(runtime_initial_agent_count)
        _set_or_create_text(root, "./overall/max_time", str(runtime_max_time))
        _set_or_create_text(root, "./parallel/omp_num_threads", "1")
        _set_or_create_text(root, "./save/folder", str((family_dir / "simulation_output").resolve()))
        _set_parameter(root, "cloneid_dataset_regime", regime_id, "Source data regime for this benchmark candidate.")
        _set_parameter(root, "cloneid_model_family", family_id, "Manuscript-facing model family.")
        _set_parameter(root, "cloneid_encoding_status", family["encoding_status"], "Data-to-PhysiCell encoding status.")
        _set_parameter(root, "cloneid_rule_surface", family["physicell_rule_surface"], "Mechanistic rule surface encoded by this candidate.")
        _set_parameter(
            root,
            "number_of_cells",
            str(runtime_initial_agent_count),
            "Initial agent count for direct runtime execution of this generated config.",
            parameter_type="int",
            units="none",
        )
        _set_parameter(
            root,
            "tumor_radius",
            str(runtime_tumor_radius),
            "Small executable tumor radius derived from the initial CLONEID agent count for runtime execution only.",
            parameter_type="double",
            units="micron",
        )
        _set_parameter(
            root,
            "oncoprotein_mean",
            "1",
            "Default heterogeneity executable parameter preserved for runtime compatibility.",
            parameter_type="double",
        )
        _set_parameter(
            root,
            "oncoprotein_sd",
            "0.25",
            "Default heterogeneity executable parameter preserved for runtime compatibility.",
            parameter_type="double",
        )
        _set_parameter(
            root,
            "oncoprotein_min",
            "0",
            "Default heterogeneity executable parameter preserved for runtime compatibility.",
            parameter_type="double",
        )
        _set_parameter(
            root,
            "oncoprotein_max",
            "2",
            "Default heterogeneity executable parameter preserved for runtime compatibility.",
            parameter_type="double",
        )
        tree.write(target_config, encoding="utf-8", xml_declaration=False)
        manifest.update(
            {
                "runnable_status": "physicell_xml_written_for_runtime_execution_or_custom_rule_implementation",
                "config_path": str(target_config.resolve()),
                "source_config_path": str(source_config.resolve()),
                "physicell_root": str(physicell_root),
                "physicell_executable": str(physicell_executable.resolve()),
                "runtime_max_time": runtime_max_time,
                "runtime_initial_agent_count": runtime_initial_agent_count,
                "runtime_tumor_radius_micron": runtime_tumor_radius,
            }
        )
    write_json(family_dir / "candidate_manifest.json", manifest)
    write_markdown(
        family_dir / "README.md",
        "\n".join(
            [
                f"# {regime_id} / {family_id}",
                "",
                f"- Encoding status: `{family['encoding_status']}`",
                f"- Rule surface: {family['physicell_rule_surface']}",
                f"- Missing required inputs: `{_format_list(family['required_inputs_missing'])}`",
                "- This candidate is an auditable input/configuration object. Runtime execution is not interpreted as calibrated biological evidence unless custom rules and live/frozen data are used.",
                "",
            ]
        ),
    )
    return manifest


def _execute_physicell_candidate(candidate: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    if not candidate.get("config_path") or not candidate.get("physicell_executable"):
        return {
            "candidate_id": candidate["candidate_id"],
            "executed": False,
            "success": False,
            "reason": "missing PhysiCell executable or XML config",
        }
    family_output = output_dir / "runtime_execution" / candidate["dataset_regime"] / candidate["family_id"]
    family_output.mkdir(parents=True, exist_ok=True)
    command = [candidate["physicell_executable"], candidate["config_path"]]
    result = subprocess.run(
        command,
        cwd=family_output,
        capture_output=True,
        text=True,
        check=False,
    )
    output_folder = Path(candidate["config_path"]).parents[1] / "simulation_output"
    observed_files = sorted(path.name for path in output_folder.iterdir()) if output_folder.exists() else []
    payload = {
        "candidate_id": candidate["candidate_id"],
        "dataset_regime": candidate["dataset_regime"],
        "family_id": candidate["family_id"],
        "executed": True,
        "success": result.returncode == 0,
        "return_code": result.returncode,
        "command": command,
        "cwd": str(family_output),
        "stdout": result.stdout,
        "stderr": result.stderr,
        "output_folder": str(output_folder),
        "observed_output_files": observed_files,
        "interpretation": "runtime execution of generated candidate config; calibrated biological interpretation requires custom PhysiCell rules and live or frozen SNU-668 data",
    }
    write_json(family_output / "execution_report.json", payload)
    return payload


def build_physicell_analysis(
    *,
    growth_episodes: list[dict[str, Any]],
    event_schedule: dict[str, Any],
    perspective_table: list[dict[str, Any]],
    coarse_record: dict[str, Any],
    external_record: dict[str, Any],
    physicell_root: str | Path | None = None,
    physicell_executable: str | Path | None = None,
    physicell_source_config: str | Path | None = None,
    execute_physicell: bool = False,
    runtime_max_time: int = 60,
    cells_per_agent: int = 1000,
) -> dict[str, Any]:
    resolved_root = resolve_physicell_root(physicell_root)
    resolved_executable = _resolve_physicell_executable(resolved_root, physicell_executable)
    resolved_source_config = _resolve_physicell_source_config(
        resolved_root,
        resolved_executable,
        physicell_source_config,
    )
    schedules = {
        "snu668_full_history": _full_history_schedule(
            growth_episodes,
            event_schedule,
            perspective_table,
            cells_per_agent=cells_per_agent,
        ),
        "snu668_published_like_compressed": _compressed_schedule(coarse_record, cells_per_agent=cells_per_agent),
        "nwaa124_curated_external": _nsr_schedule(external_record, cells_per_agent=cells_per_agent),
    }
    regimes = []
    comparison_rows = []
    for regime_id, schedule in schedules.items():
        availability = _availability_for_regime(regime_id, schedule)
        family_statuses = [
            _family_status(regime_id, family_id, availability) for family_id in MANUSCRIPT_MODEL_FAMILIES
        ]
        regimes.append(
            {
                "dataset_regime": regime_id,
                "availability": availability,
                "physicell_input_score": _regime_score(availability),
                "schedule": schedule,
                "families": family_statuses,
            }
        )
        for family in family_statuses:
            comparison_rows.append(
                {
                    "dataset_regime": regime_id,
                    "family_id": family["family_id"],
                    "encoding_status": family["encoding_status"],
                    "required_inputs_available": ";".join(family["required_inputs_available"]),
                    "required_inputs_missing": ";".join(family["required_inputs_missing"]),
                    "preferred_inputs_missing": ";".join(family["preferred_inputs_missing"]),
                    "physicell_input_score": _regime_score(availability),
                    "interpretation": family["interpretation"],
                }
            )
    return {
        "analysis_version": "rk_physicell_integration_v1",
        "physicell_root_requested": None if physicell_root is None else str(physicell_root),
        "physicell_root_resolved": None if resolved_root is None else str(resolved_root),
        "physicell_executable_requested": None if physicell_executable is None else str(physicell_executable),
        "physicell_executable_resolved": None if resolved_executable is None else str(resolved_executable),
        "physicell_source_config_requested": None if physicell_source_config is None else str(physicell_source_config),
        "physicell_source_config_resolved": None if resolved_source_config is None else str(resolved_source_config),
        "execute_physicell_requested": bool(execute_physicell),
        "runtime_max_time": runtime_max_time,
        "cells_per_agent": cells_per_agent,
        "model_families": list(MANUSCRIPT_MODEL_FAMILIES),
        "field_weights": FIELD_WEIGHTS,
        "regimes": regimes,
        "comparison_rows": comparison_rows,
        "interpretation": [
            "CLONEID full history is the only regime that supplies event-linked seed-harvest episodes, transfer resets, elapsed time, and confluence/area history for density-aware PhysiCell candidates.",
            "Compressed CLONEID and NSR publication-level records can support summary priors or targets, but density-history PhysiCell analysis is underconstrained without event-linked density and reset semantics.",
            "Runtime execution runs generated PhysiCell configs directly; calibrated biological simulation still requires custom PhysiCell rule implementation and live or frozen SNU-668 data.",
        ],
    }


def render_physicell_summary(payload: dict[str, Any]) -> str:
    lines = [
        "# PhysiCell Integration Summary",
        "",
        "This stage compares what each data regime can provide to PhysiCell and can execute generated PhysiCell configs directly when requested.",
        "",
        f"- PhysiCell root resolved: `{payload.get('physicell_root_resolved')}`",
        f"- PhysiCell executable resolved: `{payload.get('physicell_executable_resolved')}`",
        f"- PhysiCell source config resolved: `{payload.get('physicell_source_config_resolved')}`",
        f"- Runtime execution requested: `{payload.get('execute_physicell_requested')}`",
        "",
        "## Regime-Level Input Resolution",
        "",
    ]
    for regime in payload.get("regimes", []):
        lines.extend(
            [
                f"### {regime['dataset_regime']}",
                "",
                f"- PhysiCell input score: `{regime['physicell_input_score']}`",
                f"- Schedule resolution: `{regime['schedule']['episode_resolution']}`",
            ]
        )
        available = [field for field, present in regime["availability"].items() if present]
        missing = [field for field, present in regime["availability"].items() if not present]
        lines.append(f"- Available fields: `{', '.join(available) or 'none'}`")
        lines.append(f"- Missing fields: `{', '.join(missing) or 'none'}`")
        for family in regime["families"]:
            lines.append(
                f"- `{family['family_id']}`: `{family['encoding_status']}`; missing `{_format_list(family['required_inputs_missing'])}`."
            )
        lines.append("")
    lines.extend(
        [
            "## Practical Conclusion",
            "",
            "The data most useful for PhysiCell are event-linked seed/harvest episodes, transfer/reset semantics, elapsed time, and confluence/area history. NSR contributes useful r/K publication-level growth and carrying-capacity evidence, but it does not provide a native event schedule for automatic density-history PhysiCell calibration.",
            "",
            "## Guardrails",
            "",
            "- Runtime execution is not interpreted as calibrated biological evidence unless custom rules and live/frozen SNU-668 data are used.",
            "- Plot-only NSR trajectories are not used as raw numeric PhysiCell calibration targets.",
            "- Endpoint Perspective is validation/support only.",
            "",
        ]
    )
    return "\n".join(lines)


def render_required_data_for_physicell(payload: dict[str, Any]) -> str:
    rows = [
        (
            "shared growth simulation",
            "branch labels; growth-rate or count targets",
            "CLONEID full, compressed CLONEID, and NSR can all provide at least summary targets",
        ),
        (
            "branch-specific fixed fitness",
            "branch labels; matched growth targets; preferably event-linked elapsed time",
            "summary records can suggest priors, but event linkage improves calibration and auditing",
        ),
        (
            "density-history simulation",
            "seed-harvest event pairs; transfer resets; confluence/area per event; elapsed time",
            "requires CLONEID full history in the current workflow",
        ),
        (
            "agent-ready schedule generation",
            "event IDs; parent-child graph; seed/harvest/transfer classification",
            "available natively from CLONEID; requires manual reconstruction from NSR publication-level records",
        ),
    ]
    lines = [
        "# Required Data For PhysiCell Analysis",
        "",
        "The necessary data depend on the PhysiCell question being asked. CLONEID-LTEE is useful because it keeps low-cost event-linked fields that determine whether a spatial/agent-based model can be generated and audited automatically.",
        "",
        "| PhysiCell question | Necessary data | Current comparison |",
        "|---|---|---|",
    ]
    lines.extend(f"| {question} | {needed} | {comparison} |" for question, needed, comparison in rows)
    lines.extend(
        [
            "",
            "## Highest-Value Low-Cost Fields",
            "",
        ]
    )
    for field, weight in sorted(FIELD_WEIGHTS.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- `{field}`: weight `{weight}`")
    lines.extend(
        [
            "",
            "## Regime Scores",
            "",
        ]
    )
    for regime in payload.get("regimes", []):
        lines.append(f"- `{regime['dataset_regime']}`: `{regime['physicell_input_score']}`")
    lines.append("")
    return "\n".join(lines)


def write_physicell_analysis(
    output_dir: str | Path,
    payload: dict[str, Any],
) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    resolved_root = Path(payload["physicell_root_resolved"]) if payload.get("physicell_root_resolved") else None
    resolved_executable = (
        Path(payload["physicell_executable_resolved"]) if payload.get("physicell_executable_resolved") else None
    )
    resolved_source_config = (
        Path(payload["physicell_source_config_resolved"]) if payload.get("physicell_source_config_resolved") else None
    )
    paths: dict[str, Path] = {
        "physicell_input_manifest": write_json(output / "physicell_input_manifest.json", payload),
        "model_family_physicell_comparison_json": write_json(
            output / "model_family_physicell_comparison.json",
            payload["comparison_rows"],
        ),
        "model_family_physicell_comparison_csv": _write_csv(
            output / "model_family_physicell_comparison.csv",
            payload["comparison_rows"],
        ),
        "physicell_summary": write_markdown(output / "physicell_summary.md", render_physicell_summary(payload)),
        "required_data_for_physicell": write_markdown(
            output / "required_data_for_physicell.md",
            render_required_data_for_physicell(payload),
        ),
    }
    candidate_manifests = []
    for regime in payload.get("regimes", []):
        regime_dir = output / regime["dataset_regime"]
        paths[f"{regime['dataset_regime']}_schedule"] = write_json(regime_dir / "physicell_schedule.json", regime["schedule"])
        growth_episodes = regime["schedule"].get("growth_episodes", [])
        runtime_initial_agent_count = int(
            growth_episodes[0].get("initial_agent_count") or 10
        ) if growth_episodes else 10
        for family in regime["families"]:
            candidate = _write_candidate_config(
                family=family,
                regime_id=regime["dataset_regime"],
                family_id=family["family_id"],
                output_dir=output,
                physicell_root=resolved_root,
                physicell_executable=resolved_executable,
                physicell_source_config=resolved_source_config,
                runtime_max_time=int(payload.get("runtime_max_time", 60)),
                runtime_initial_agent_count=runtime_initial_agent_count,
            )
            candidate_manifests.append(candidate)
    paths["candidate_manifest_index"] = write_json(output / "candidate_manifest_index.json", candidate_manifests)
    if payload.get("execute_physicell_requested"):
        execution_reports = [
            _execute_physicell_candidate(candidate, output)
            for candidate in candidate_manifests
            if candidate["dataset_regime"] == "snu668_full_history"
        ]
        paths["physicell_execution_report"] = write_json(output / "physicell_execution_report.json", execution_reports)
        payload["execution_reports"] = execution_reports
        write_json(output / "physicell_input_manifest.json", payload)
    return paths
