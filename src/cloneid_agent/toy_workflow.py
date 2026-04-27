"""Synthetic CLONEID-like toy fixture and dry-run round-trip generator."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .run_io import initialize_dry_run_tree, prepare_run_directory, write_json, write_markdown
from .trajectory_bundles import discover_trajectory_bundle


def build_toy_fixture() -> dict[str, Any]:
    """Return a small CLONEID-like synthetic dataset for offline development."""
    return {
        "cell_line": {
            "name": "TOY_A549",
            "doublingTime_hours": 28.0,
            "whichType": "cell_line",
            "source": "synthetic",
        },
        "flask": {
            "id": 1,
            "dishSurfaceArea_cm2": 25.0,
            "surface_treated_type": "tissue_culture_treated",
            "bottom_shape": "flat",
        },
        "media": {
            "id": 1,
            "base1": "RPMI",
            "FBS_pct": 10,
            "Stressor": None,
            "oxygen_pct": 21,
        },
        "passaging": [
            {
                "id": "toy_seed_001",
                "cellLine": "TOY_A549",
                "event": "seeding",
                "passaged_from_id1": None,
                "passaged_from_id2": None,
                "growthType": "adherent_2D",
                "passage": 1,
                "cellCount": 50000,
                "correctedCount": 50000,
                "date": "2026-01-01",
                "media": 1,
                "flask": 1,
                "areaOccupied_um2": 250000.0,
                "cellSize_um2": 950.0,
            },
            {
                "id": "toy_harvest_002",
                "cellLine": "TOY_A549",
                "event": "harvest",
                "passaged_from_id1": "toy_seed_001",
                "passaged_from_id2": None,
                "growthType": "adherent_2D",
                "passage": 1,
                "cellCount": 90000,
                "correctedCount": 88000,
                "date": "2026-01-03",
                "media": 1,
                "flask": 1,
                "areaOccupied_um2": 430000.0,
                "cellSize_um2": 975.0,
            },
            {
                "id": "toy_harvest_003",
                "cellLine": "TOY_A549",
                "event": "harvest",
                "passaged_from_id1": "toy_harvest_002",
                "passaged_from_id2": None,
                "growthType": "adherent_2D",
                "passage": 1,
                "cellCount": 160000,
                "correctedCount": 157000,
                "date": "2026-01-05",
                "media": 1,
                "flask": 1,
                "areaOccupied_um2": 760000.0,
                "cellSize_um2": 990.0,
            },
        ],
        "qupath": [
            {
                "id": "toy_harvest_002",
                "cellCount_standard": 87000,
                "cellCount_cellpose": 88500,
                "cellCount_QCmetrics": "pass",
            },
            {
                "id": "toy_harvest_003",
                "cellCount_standard": 155000,
                "cellCount_cellpose": 158500,
                "cellCount_QCmetrics": "pass",
            },
        ],
        "perspective": [
            {
                "cloneID": "toy_perspective_clone_1",
                "origin": "toy_harvest_003",
                "whichPerspective": "GenomePerspective",
                "size": 0.7,
                "state": "state_A",
                "sampleSource": "toy_harvest_003",
                "rootID": "toy_root_1",
            },
            {
                "cloneID": "toy_perspective_clone_2",
                "origin": "toy_harvest_003",
                "whichPerspective": "GenomePerspective",
                "size": 0.3,
                "state": "state_B",
                "sampleSource": "toy_harvest_003",
                "rootID": "toy_root_1",
            },
        ],
        "identity": [
            {
                "cloneID": "toy_identity_1",
                "whichPerspective": "GenomePerspective",
                "size": 0.7,
                "sampleSource": "toy_harvest_003",
                "rootID": "toy_root_1",
                "GenomePerspective": "toy_perspective_clone_1",
                "state": "state_A",
            },
            {
                "cloneID": "toy_identity_2",
                "whichPerspective": "GenomePerspective",
                "size": 0.3,
                "sampleSource": "toy_harvest_003",
                "rootID": "toy_root_1",
                "GenomePerspective": "toy_perspective_clone_2",
                "state": "state_B",
            },
        ],
    }


def _resolve_output_dir(output: str | None, run_id: str | None) -> Path:
    if output:
        path = Path(output)
        path.mkdir(parents=True, exist_ok=True)
        return path
    return prepare_run_directory("runs", run_id=run_id, prefix="toy")


def run_toy_round_trip(output: str | None = None, run_id: str | None = None) -> Path:
    """Write a minimal toy dry-run artifact set without real database access."""
    run_dir = _resolve_output_dir(output, run_id)
    subdirs = initialize_dry_run_tree(run_dir)

    fixture = build_toy_fixture()
    write_json(run_dir / "toy_fixture.json", fixture)

    database_inventory = {
        "source": "toy_fixture",
        "tables": {
            "Passaging": len(fixture["passaging"]),
            "QuPathEvaluation": len(fixture["qupath"]),
            "Perspective": len(fixture["perspective"]),
            "Identity": len(fixture["identity"]),
            "CellLinesAndPatients": 1,
            "Flask": 1,
            "Media": 1,
        },
    }
    write_json(run_dir / "database_inventory.json", database_inventory)

    selected_dataset = {
        "dataset_id": "toy_dataset_001",
        "cell_line": fixture["cell_line"]["name"],
        "event_ids": [row["id"] for row in fixture["passaging"]],
        "endpoint_event_id": "toy_harvest_003",
        "score": 5,
        "selection_reason": "Synthetic dataset with longitudinal phenotype, event lineage, context, and endpoint state fractions.",
    }
    write_json(run_dir / "selected_dataset.json", selected_dataset)

    trajectory_bundle = discover_trajectory_bundle(
        seed_dataset_id="TOY_A549__adherent_2D__1__1__1",
        passaging_records=fixture["passaging"],
        perspective_records=fixture["perspective"],
        identity_records=fixture["identity"],
        max_upstream_depth=4,
        max_downstream_depth=4,
    )
    write_json(run_dir / "trajectory_bundle.json", trajectory_bundle)

    observables = {
        "selected": [
            {"source": "Passaging.correctedCount", "target": "viable cell count"},
            {"source": "Passaging.areaOccupied_um2", "target": "area coverage"},
            {"source": "Perspective.size", "target": "endpoint state fraction"},
        ],
        "excluded": [
            {"source": "Identity.size", "reason": "inferred endpoint summary retained as secondary evidence only"}
        ],
    }
    write_json(run_dir / "observables.json", observables)

    agent_plan = {
        "run_id": run_dir.name,
        "mode": "toy-dry-run",
        "selected_dataset": selected_dataset["dataset_id"],
        "candidate_models": [
            {"model_id": "neutral_growth", "family": "neutral_growth"},
            {"model_id": "fixed_state_fitness", "family": "fixed_state_fitness"},
        ],
        "constraints": [
            "read-only synthetic fixture",
            "no live database access required",
            "no PhysiCell binary required",
        ],
        "mapping": {
            "initial_condition": "toy_seed_001",
            "longitudinal_observable": "Passaging.correctedCount",
            "endpoint_state_source": "Perspective",
        },
    }
    write_json(run_dir / "agent_plan.json", agent_plan)

    model_candidates = [
        {"model_id": "neutral_growth", "rmse": 0.18, "supports_data": False},
        {"model_id": "fixed_state_fitness", "rmse": 0.06, "supports_data": True},
    ]
    model_dir = subdirs["model_candidates"]
    for candidate in model_candidates:
        write_json(model_dir / f"{candidate['model_id']}.json", candidate)

    comparison_path = subdirs["evaluation"] / "model_comparison.csv"
    with comparison_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["model_id", "rmse", "supports_data"])
        writer.writeheader()
        writer.writerows(model_candidates)

    report = "\n".join(
        [
            "# Toy Model Selection Report",
            "",
            "## Executive Summary",
            "",
            "Synthetic CLONEID-like records were mapped into two candidate model families.",
            "The fixed-state-fitness toy model was sufficient to better recapitulate the synthetic trajectory than the neutral-growth toy model under the tested assumptions.",
            "",
            "## Selected Dataset",
            "",
            f"- Dataset ID: `{selected_dataset['dataset_id']}`",
            f"- Cell line: `{selected_dataset['cell_line']}`",
            "",
            "## Candidate Models",
            "",
            "- `neutral_growth`",
            "- `fixed_state_fitness`",
            "",
            "## Outcome",
            "",
            "- Supported under tested assumptions: `fixed_state_fitness`",
            "- Rejected under tested assumptions: `neutral_growth`",
            "",
        ]
    )
    write_markdown(run_dir / "model_selection_report.md", report)

    return run_dir
