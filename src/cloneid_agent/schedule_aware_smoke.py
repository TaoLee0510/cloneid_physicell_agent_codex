"""One-episode real PhysiCell smoke harness for schedule-aware candidates."""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
from typing import Any
import xml.etree.ElementTree as ET

from .run_io import write_json, write_markdown

EXPECTED_SMOKE_OUTPUT_FILES = (
    "initial.xml",
    "final.xml",
    "initial.svg",
    "final.svg",
)


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text())


def _episode_lookup(branch_schedule: dict[str, Any], milestone_label: str) -> dict[str, Any]:
    for episode in branch_schedule.get("growth_episodes", []):
        if episode["milestone_label"] == milestone_label:
            return episode
    raise KeyError(f"Growth episode not found for milestone label: {milestone_label}")


def _stage_name(family: str, branch_id: str, milestone_label: str) -> str:
    return f"{family}__{branch_id}__{milestone_label}"


def _copy_and_rewrite_config(
    *,
    source_config: Path,
    target_config: Path,
    output_folder: Path,
    simulated_duration_minutes: int,
    omp_threads: int,
) -> None:
    shutil.copy2(source_config, target_config)
    tree = ET.parse(target_config)
    root = tree.getroot()
    root.find("./overall/max_time").text = str(simulated_duration_minutes)
    root.find("./parallel/omp_num_threads").text = str(omp_threads)
    root.find("./save/folder").text = str(output_folder)
    full_data_interval = root.find("./save/full_data/interval")
    if full_data_interval is not None:
        full_data_interval.text = str(simulated_duration_minutes)
    svg_interval = root.find("./save/SVG/interval")
    if svg_interval is not None:
        svg_interval.text = str(simulated_duration_minutes)
    tree.write(target_config, encoding="utf-8", xml_declaration=False)


def build_single_episode_smoke_plan(
    *,
    candidate_dir: str | Path,
    branch_schedule: dict[str, Any],
    family: str,
    episode_milestone_label: str,
    stage_root: str | Path,
    physicell_root: str | Path | None = None,
    omp_threads: int = 1,
) -> dict[str, Any]:
    candidate_dir = Path(candidate_dir)
    stage_root = Path(stage_root).resolve()
    manifest = _load_json(candidate_dir / "candidate_manifest.json")
    evaluation_plan = _load_json(candidate_dir / "evaluation_plan.json")
    episode = _episode_lookup(branch_schedule, episode_milestone_label)
    stage_dir = stage_root / _stage_name(family, branch_schedule["branch_id"], episode_milestone_label)
    staged_config = (stage_dir / "config" / "PhysiCell_settings.xml").resolve()
    output_folder = (stage_dir / "simulation_output").resolve()
    executable_path = Path(
        manifest["physicell_executable"]
        if physicell_root is None
        else Path(physicell_root) / "heterogeneity"
    )
    return {
        "plan_version": "single_episode_smoke_plan_v1",
        "family": family,
        "branch_id": branch_schedule["branch_id"],
        "branch_label": branch_schedule["branch_label"],
        "candidate_dir": str(candidate_dir.resolve()),
        "candidate_config_path": str((candidate_dir / "config" / "PhysiCell_settings.xml").resolve()),
        "stage_dir": str(stage_dir),
        "staged_config_path": str(staged_config),
        "output_folder": str(output_folder),
        "physicell_executable": str(executable_path),
        "episode": {
            "milestone_label": episode_milestone_label,
            "parent_event_id": episode["parent_event_id"],
            "child_event_id": episode["child_event_id"],
            "window_label": f"{episode['parent_event_id']} -> {episode['child_event_id']}",
            "simulated_duration_minutes": int(episode["simulated_duration_minutes"]),
            "real_elapsed_minutes": episode["real_elapsed_minutes"],
            "observables": episode["observables"],
        },
        "initial_condition": branch_schedule["initial_condition"],
        "shared_evaluation_objective": {
            "primary_shared_objective": evaluation_plan["primary_shared_objective"],
            "secondary_objective": evaluation_plan["secondary_objective"],
            "endpoint_validation": evaluation_plan["endpoint_validation"],
        },
        "execution_invariants": {
            "prehistory_context_excluded_from_runtime": True,
            "transfer_events_not_simulated_as_growth": True,
            "perspective_size_validation_only": True,
            "not_fitted": True,
            "no_model_comparison": True,
        },
        "runtime": {
            "omp_threads": int(omp_threads),
            "expected_output_files": list(EXPECTED_SMOKE_OUTPUT_FILES),
        },
    }


def parse_smoke_output_folder(
    output_folder: str | Path,
    *,
    plan: dict[str, Any],
) -> dict[str, Any]:
    output_folder = Path(output_folder)
    observed_files = sorted(path.name for path in output_folder.iterdir()) if output_folder.exists() else []
    missing_files = [name for name in EXPECTED_SMOKE_OUTPUT_FILES if name not in observed_files]
    present_files = [name for name in EXPECTED_SMOKE_OUTPUT_FILES if name in observed_files]
    xml_files = sorted(name for name in observed_files if name.endswith(".xml"))
    svg_files = sorted(name for name in observed_files if name.endswith(".svg"))
    mat_files = sorted(name for name in observed_files if name.endswith(".mat"))

    xml_parse_status = {}
    for name in xml_files:
        try:
            ET.parse(output_folder / name)
            xml_parse_status[name] = True
        except ET.ParseError:
            xml_parse_status[name] = False

    return {
        "parser_version": "schedule_aware_smoke_output_parser_v1",
        "family": plan["family"],
        "branch_id": plan["branch_id"],
        "episode_milestone_label": plan["episode"]["milestone_label"],
        "output_folder": str(output_folder),
        "observed_files": observed_files,
        "expected_files_present": present_files,
        "expected_files_missing": missing_files,
        "xml_files": xml_files,
        "svg_files": svg_files,
        "mat_files": mat_files,
        "xml_parse_status": xml_parse_status,
        "shared_evaluation_schema_mapping": {
            "mapping_status": "structural_scaffold_only",
            "primary_shared_objective": plan["shared_evaluation_objective"]["primary_shared_objective"],
            "secondary_objective": plan["shared_evaluation_objective"]["secondary_objective"],
            "endpoint_validation": plan["shared_evaluation_objective"]["endpoint_validation"],
            "episode_level_counts_available": False,
            "notes": [
                "Real PhysiCell output folder was parsed structurally only.",
                "No biological parameter fitting or model comparison is performed here.",
                "Perspective.size remains endpoint validation metadata only.",
            ],
        },
    }


def run_single_episode_smoke_test(
    *,
    candidate_dir: str | Path,
    branch_schedule_path: str | Path,
    family: str,
    episode_milestone_label: str,
    output_root: str | Path,
    physicell_root: str | Path | None = None,
    omp_threads: int = 1,
) -> dict[str, Any]:
    branch_schedule = _load_json(branch_schedule_path)
    plan = build_single_episode_smoke_plan(
        candidate_dir=candidate_dir,
        branch_schedule=branch_schedule,
        family=family,
        episode_milestone_label=episode_milestone_label,
        stage_root=output_root,
        physicell_root=physicell_root,
        omp_threads=omp_threads,
    )
    stage_dir = Path(plan["stage_dir"])
    staged_config = Path(plan["staged_config_path"])
    output_folder = Path(plan["output_folder"])
    stage_dir.mkdir(parents=True, exist_ok=True)
    (stage_dir / "config").mkdir(parents=True, exist_ok=True)
    _copy_and_rewrite_config(
        source_config=Path(plan["candidate_config_path"]),
        target_config=staged_config,
        output_folder=output_folder,
        simulated_duration_minutes=plan["episode"]["simulated_duration_minutes"],
        omp_threads=plan["runtime"]["omp_threads"],
    )

    command = [plan["physicell_executable"], str(staged_config.resolve())]
    result = subprocess.run(
        command,
        cwd=stage_dir,
        capture_output=True,
        text=True,
        check=False,
    )

    parser_payload = parse_smoke_output_folder(output_folder, plan=plan) if output_folder.exists() else None
    observed_files = [] if parser_payload is None else parser_payload["observed_files"]
    report = {
        "report_version": "single_episode_smoke_report_v1",
        "family": family,
        "branch_id": plan["branch_id"],
        "episode_milestone_label": episode_milestone_label,
        "command": command,
        "cwd": str(stage_dir),
        "return_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "expected_output_files": plan["runtime"]["expected_output_files"],
        "observed_output_files": observed_files,
        "output_folder": str(output_folder),
        "success": result.returncode == 0 and parser_payload is not None and not parser_payload["expected_files_missing"],
        "notes": [
            "This is a one-episode syntax/smoke execution only.",
            "No parameter fitting, biological interpretation, or model comparison is performed.",
        ],
    }
    return {
        "plan": plan,
        "report": report,
        "parsed_output": parser_payload,
    }


def write_single_episode_smoke_artifacts(
    output_dir: str | Path,
    payload: dict[str, Any],
) -> None:
    output_dir = Path(output_dir)
    write_json(output_dir / "smoke_test_plan.json", payload["plan"])
    write_markdown(
        output_dir / "smoke_test_plan.md",
        "\n".join(
            [
                "# One-Episode Smoke Test Plan",
                "",
                f"- Family: `{payload['plan']['family']}`",
                f"- Branch: `{payload['plan']['branch_id']}`",
                f"- Episode: `{payload['plan']['episode']['window_label']}`",
                f"- Simulated duration: `{payload['plan']['episode']['simulated_duration_minutes']}` minutes",
                f"- Executable: `{payload['plan']['physicell_executable']}`",
                f"- Stage dir: `{payload['plan']['stage_dir']}`",
            ]
        )
        + "\n",
    )
    write_json(output_dir / "smoke_test_report.json", payload["report"])
    write_markdown(
        output_dir / "smoke_test_report.md",
        "\n".join(
            [
                "# One-Episode Smoke Test Report",
                "",
                f"- Success: `{payload['report']['success']}`",
                f"- Return code: `{payload['report']['return_code']}`",
                f"- Output folder: `{payload['report']['output_folder']}`",
                f"- Expected files: `{', '.join(payload['report']['expected_output_files'])}`",
                f"- Observed files: `{', '.join(payload['report']['observed_output_files'])}`",
                "",
                "## Notes",
                "",
                *[f"- {note}" for note in payload["report"]["notes"]],
            ]
        )
        + "\n",
    )
    if payload["parsed_output"] is not None:
        write_json(output_dir / "parsed_output_summary.json", payload["parsed_output"])
        write_markdown(
            output_dir / "parsed_output_summary.md",
            "\n".join(
                [
                    "# Parsed Smoke Output Summary",
                    "",
                    f"- Family: `{payload['parsed_output']['family']}`",
                    f"- Branch: `{payload['parsed_output']['branch_id']}`",
                    f"- Episode milestone: `{payload['parsed_output']['episode_milestone_label']}`",
                    f"- XML files: `{len(payload['parsed_output']['xml_files'])}`",
                    f"- SVG files: `{len(payload['parsed_output']['svg_files'])}`",
                    f"- MAT files: `{len(payload['parsed_output']['mat_files'])}`",
                    f"- Expected files missing: `{', '.join(payload['parsed_output']['expected_files_missing'])}`",
                    "",
                    "## Mapping status",
                    "",
                    f"- `{payload['parsed_output']['shared_evaluation_schema_mapping']['mapping_status']}`",
                ]
            )
            + "\n",
        )


def run_smoke_tests_for_families(
    *,
    candidate_root: str | Path,
    branch_schedule_path: str | Path,
    families: list[str],
    episode_milestone_label: str,
    output_root: str | Path,
    physicell_root: str | Path | None = None,
    omp_threads: int = 1,
) -> dict[str, Any]:
    candidate_root = Path(candidate_root)
    output_root = Path(output_root)
    payload = {
        "run_version": "schedule_aware_smoke_run_v1",
        "families": {},
    }
    for family in families:
        candidate_dir = candidate_root / family
        family_output_dir = output_root / family
        result = run_single_episode_smoke_test(
            candidate_dir=candidate_dir,
            branch_schedule_path=branch_schedule_path,
            family=family,
            episode_milestone_label=episode_milestone_label,
            output_root=family_output_dir,
            physicell_root=physicell_root,
            omp_threads=omp_threads,
        )
        write_single_episode_smoke_artifacts(family_output_dir, result)
        payload["families"][family] = {
            "success": result["report"]["success"],
            "report_path": str(family_output_dir / "smoke_test_report.json"),
            "parsed_output_path": (
                None if result["parsed_output"] is None else str(family_output_dir / "parsed_output_summary.json")
            ),
        }
    return payload
