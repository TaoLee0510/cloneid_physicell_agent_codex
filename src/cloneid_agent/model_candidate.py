"""Generate first-pass repository-owned PhysiCell model candidate folders."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

from .physicell_mapping import DEFAULT_MAX_PROOF_OF_PRINCIPLE_MIN
from .run_io import write_json, write_markdown


DEFAULT_PHYSICELL_ROOT = Path("/Users/4482173/Documents/PhysiCell")


def _load_base_config(physicell_root: str | Path) -> ET.ElementTree:
    physicell_root = Path(physicell_root)
    config_path = physicell_root / "config" / "PhysiCell_settings.xml"
    if not config_path.exists():
        raise FileNotFoundError(f"PhysiCell config not found: {config_path}")
    return ET.parse(config_path)


def _update_config_tree(
    tree: ET.ElementTree,
    *,
    output_folder: str,
    max_time_min: int,
    omp_threads: int,
) -> ET.ElementTree:
    root = tree.getroot()
    max_time_node = root.find("./overall/max_time")
    omp_node = root.find("./parallel/omp_num_threads")
    save_folder_node = root.find("./save/folder")
    if max_time_node is None or omp_node is None or save_folder_node is None:
        raise ValueError("Base PhysiCell config is missing one of: overall/max_time, parallel/omp_num_threads, save/folder")
    max_time_node.text = str(max_time_min)
    omp_node.text = str(omp_threads)
    save_folder_node.text = output_folder
    return tree


def _candidate_readme_lines(candidate: dict[str, Any]) -> list[str]:
    return [
        f"# {candidate['candidate_id']}",
        "",
        f"- Family: `{candidate['family']}`",
        f"- Selected lineage object: `{candidate['selected_lineage_object_id']}`",
        f"- Selected lineage object type: `{candidate['selected_lineage_object_type']}`",
        f"- Base PhysiCell root: `{candidate['physicell_root']}`",
        f"- Config path: `{candidate['config_path']}`",
        f"- Planned max time (min): `{candidate['planned_max_time_min']}`",
        f"- Planned output folder: `{candidate['planned_output_folder']}`",
        "",
        "## Status",
        "",
        "- This is a deterministic first-pass generated model candidate.",
        "- It preserves CLONEID lineage-object provenance and mapping metadata.",
        "- It does not yet encode family-specific calibrated biology beyond the shared runtime-ready scaffold.",
    ]


def generate_model_candidates(
    *,
    selected_lineage_object_payload: dict[str, Any],
    selected_observables_payload: dict[str, Any],
    mapping_payload: dict[str, Any],
    output_dir: str | Path,
    physicell_root: str | Path | None = DEFAULT_PHYSICELL_ROOT,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    candidate_root = output_dir / "model_candidates"
    candidate_root.mkdir(parents=True, exist_ok=True)
    physicell_root = Path(DEFAULT_PHYSICELL_ROOT if physicell_root is None else physicell_root)
    executable_path = physicell_root / "heterogeneity"
    if not executable_path.exists():
        raise FileNotFoundError(f"PhysiCell executable not found: {executable_path}")

    model_families = mapping_payload.get("recommended_model_families", [])
    planned_max_time_min = int(
        mapping_payload.get("timeline", {}).get("planned_max_time_min", 1440)
    )
    max_proof_of_principle_minutes = int(
        mapping_payload.get("timeline", {}).get(
            "max_proof_of_principle_minutes",
            DEFAULT_MAX_PROOF_OF_PRINCIPLE_MIN,
        )
    )
    within_guardrail = bool(
        mapping_payload.get("timeline", {}).get("within_proof_of_principle_guardrail", True)
    )
    if not within_guardrail:
        raise ValueError(
            f"Planned max time {planned_max_time_min} exceeds proof-of-principle guardrail {max_proof_of_principle_minutes} minutes; select a smaller bounded lineage object or add an explicit override."
        )
    selected_lineage_object_id = mapping_payload.get(
        "selected_lineage_object_id",
        selected_lineage_object_payload.get("selected_lineage_object_id"),
    )
    selected_lineage_object_type = mapping_payload.get(
        "selected_lineage_object_type",
        selected_lineage_object_payload.get("selected_lineage_object_type"),
    )
    runtime_eligible = bool(selected_lineage_object_payload.get("runtime_eligible", False))
    if not runtime_eligible:
        raise ValueError(
            "Default candidate generation requires a runtime-eligible selected lineage object; use selected_runtime_lineage_object.json or add an explicit runtime override."
        )

    candidates: list[dict[str, Any]] = []
    for family in model_families:
        candidate_id = f"{family}__{selected_lineage_object_id.split('::', 1)[-1]}"
        family_dir = candidate_root / family
        config_dir = family_dir / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        simulation_output_dir = family_dir / "simulation_output"
        tree = _load_base_config(physicell_root)
        _update_config_tree(
            tree,
            output_folder=str(simulation_output_dir),
            max_time_min=planned_max_time_min,
            omp_threads=1,
        )
        config_path = config_dir / "PhysiCell_settings.xml"
        tree.write(config_path, encoding="utf-8", xml_declaration=False)

        candidate = {
            "candidate_id": candidate_id,
            "family": family,
            "selected_lineage_object_id": selected_lineage_object_id,
            "selected_lineage_object_type": selected_lineage_object_type,
            "physicell_root": str(physicell_root),
            "physicell_executable": str(executable_path),
            "config_path": str(config_path),
            "candidate_dir": str(family_dir),
            "planned_output_folder": str(simulation_output_dir),
            "planned_max_time_min": planned_max_time_min,
            "selected_observable_sources": [item["source"] for item in selected_observables_payload.get("selected", [])],
            "mapping_version": mapping_payload.get("mapping_version"),
            "traversal_policy": mapping_payload.get("traversal_policy", {}),
            "max_proof_of_principle_minutes": max_proof_of_principle_minutes,
            "generation_policy": "first_pass_shared_physicell_runtime_scaffold",
        }
        write_json(family_dir / "candidate_manifest.json", candidate)
        write_markdown(family_dir / "README.md", "\n".join(_candidate_readme_lines(candidate)) + "\n")
        candidates.append(candidate)

    payload = {
        "selected_lineage_object_id": selected_lineage_object_id,
        "selected_lineage_object_type": selected_lineage_object_type,
        "physicell_root": str(physicell_root),
        "model_candidates": candidates,
        "generation_policy": "Generate one first-pass runtime-ready candidate folder per recommended PhysiCell family without adding family-specific calibrated biology yet.",
    }
    return payload


def generate_model_candidates_from_files(
    *,
    selected_lineage_object_path: str | Path,
    selected_observables_path: str | Path,
    mapping_path: str | Path,
    output_dir: str | Path,
    physicell_root: str | Path | None = DEFAULT_PHYSICELL_ROOT,
) -> dict[str, Any]:
    return generate_model_candidates(
        selected_lineage_object_payload=json.loads(Path(selected_lineage_object_path).read_text()),
        selected_observables_payload=json.loads(Path(selected_observables_path).read_text()),
        mapping_payload=json.loads(Path(mapping_path).read_text()),
        output_dir=output_dir,
        physicell_root=physicell_root,
    )


def write_model_candidates(output_dir: str | Path, payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    write_json(output_dir / "generated_model_candidates.json", payload)
    lines = [
        "# Generated Model Candidates",
        "",
        f"- Selected lineage object: `{payload.get('selected_lineage_object_id')}`",
        f"- Selected lineage object type: `{payload.get('selected_lineage_object_type')}`",
        f"- PhysiCell root: `{payload.get('physicell_root')}`",
        "",
        "## Candidates",
        "",
    ]
    for candidate in payload.get("model_candidates", []):
        lines.append(
            f"- `{candidate['family']}` -> `{candidate['candidate_dir']}`"
        )
    write_markdown(output_dir / "generated_model_candidates.md", "\n".join(lines) + "\n")
