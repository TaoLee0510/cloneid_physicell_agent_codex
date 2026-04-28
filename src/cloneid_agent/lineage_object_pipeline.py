"""Pipeline helpers for global lineage-object discovery from full CLONEID-like fixtures."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from .db import repository_root
from .lineage_object_ranking import rank_lineage_object_inventory, write_ranked_lineage_objects
from .lineage_object_selection import select_top_lineage_object, write_selected_lineage_object
from .lineage_objects import discover_global_lineage_objects_from_file, write_global_lineage_inventory
from .modeling_lineage_selection import (
    classify_lineage_objects_for_modeling,
    classify_modeling_candidates_for_smoke,
    select_modeling_lineage_object,
    select_smoke_lineage_object,
    write_modeling_candidate_artifacts,
    write_selected_smoke_lineage_object,
    write_selected_modeling_lineage_object,
    write_smoke_candidate_artifacts,
)
from .run_io import prepare_run_directory, write_json, write_markdown


def global_lineage_records_script_path() -> Path:
    return repository_root() / "scripts" / "cloneid_global_lineage_records.R"


def export_global_lineage_records(
    *,
    output_dir: str | Path,
    mode: str = "live",
) -> Path:
    script = global_lineage_records_script_path()
    if not script.exists():
        raise FileNotFoundError(f"Global lineage export script not found: {script}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "global_lineage_records.json"
    cmd = ["Rscript", str(script), "--mode", mode, "--output", str(output_path)]
    result = subprocess.run(cmd, cwd=repository_root(), check=False)
    if result.returncode != 0:
        raise RuntimeError(f"Global lineage record export failed with exit code {result.returncode}")
    return output_path


def discover_rank_and_select_lineage_objects(
    *,
    ranked_candidates_path: str | Path,
    output: str | None = None,
    run_id: str | None = None,
    mode: str = "live",
) -> Path:
    ranked_candidates_path = Path(ranked_candidates_path)
    ranked_candidates_payload = json.loads(ranked_candidates_path.read_text())
    run_dir = Path(output) if output else prepare_run_directory("runs", run_id=run_id, prefix="lineage_objects")
    run_dir.mkdir(parents=True, exist_ok=True)

    records_path = export_global_lineage_records(output_dir=run_dir, mode=mode)
    inventory = discover_global_lineage_objects_from_file(records_path, ranked_candidates_payload=ranked_candidates_payload)
    write_global_lineage_inventory(run_dir, inventory)

    ranked = rank_lineage_object_inventory(inventory)
    write_ranked_lineage_objects(run_dir, ranked)

    selection = select_top_lineage_object(ranked)
    write_selected_lineage_object(run_dir, selection)

    modeling_payload = classify_lineage_objects_for_modeling(ranked)
    write_modeling_candidate_artifacts(run_dir, modeling_payload)

    modeling_selection = select_modeling_lineage_object(modeling_payload)
    write_selected_modeling_lineage_object(run_dir, modeling_selection)

    smoke_payload = classify_modeling_candidates_for_smoke(modeling_payload)
    write_smoke_candidate_artifacts(run_dir, smoke_payload)
    smoke_selection = None
    if smoke_payload.get("smoke_eligible_modeling_candidate_count", 0) > 0:
        smoke_selection = select_smoke_lineage_object(smoke_payload)
        write_selected_smoke_lineage_object(run_dir, smoke_selection)

    summary = {
        "mode": mode,
        "ranked_candidates_source": str(ranked_candidates_path),
        "global_lineage_records": str(records_path),
        "discovered_object_counts": inventory.get("discovered_object_counts", {}),
        "selected_lineage_object_id": selection["selected_lineage_object_id"],
        "selected_lineage_object_type": selection["selected_lineage_object_type"],
        "selected_modeling_lineage_object_id": modeling_selection["selected_lineage_object_id"],
        "selected_modeling_lineage_object_type": modeling_selection["selected_lineage_object_type"],
        "smoke_eligible_modeling_candidate_count": smoke_payload.get("smoke_eligible_modeling_candidate_count", 0),
        "selected_smoke_lineage_object_id": None if smoke_selection is None else smoke_selection["selected_lineage_object_id"],
        "selected_smoke_lineage_object_type": None if smoke_selection is None else smoke_selection["selected_lineage_object_type"],
        "selection_starts_from_candidate_segment": False,
    }
    write_json(run_dir / "lineage_object_pipeline_summary.json", summary)
    write_markdown(
        run_dir / "lineage_object_pipeline_summary.md",
        "\n".join(
            [
                "# Lineage Object Pipeline Summary",
                "",
                f"- Mode: `{mode}`",
                f"- Ranked candidates source: `{ranked_candidates_path}`",
                f"- Selected global lineage object: `{selection['selected_lineage_object_id']}`",
                f"- Selected global type: `{selection['selected_lineage_object_type']}`",
                f"- Selected bounded modeling lineage object: `{modeling_selection['selected_lineage_object_id']}`",
                f"- Selected bounded type: `{modeling_selection['selected_lineage_object_type']}`",
                f"- Smoke-eligible modeling candidate count: `{smoke_payload.get('smoke_eligible_modeling_candidate_count', 0)}`",
                f"- Selected smoke lineage object: `{None if smoke_selection is None else smoke_selection['selected_lineage_object_id']}`",
                "- Selection starts from CandidateSegment: `false`",
            ]
        )
        + "\n",
    )
    return run_dir
