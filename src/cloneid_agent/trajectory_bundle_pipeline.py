"""Pipeline helpers for live or mock TrajectoryBundle discovery from ranked CandidateSegments."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from .db import repository_root
from .run_io import prepare_run_directory, write_json, write_markdown
from .trajectory_bundle_ranking import rank_trajectory_bundle_payloads, write_ranked_trajectory_bundles
from .trajectory_bundles import discover_trajectory_bundle_from_file, write_trajectory_bundle


def trajectory_bundle_records_script_path() -> Path:
    return repository_root() / "scripts" / "cloneid_trajectory_bundle_records.R"


def _sanitize_name(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value)


def select_seed_dataset_ids(
    ranked_candidates_payload: dict[str, Any],
    *,
    top_n: int,
) -> list[str]:
    ranked = ranked_candidates_payload.get("ranked_candidates", [])
    return [str(item["dataset_id"]) for item in ranked[:top_n]]


def export_seed_record_fixtures(
    *,
    seed_dataset_ids: list[str],
    output_dir: str | Path,
    mode: str = "live",
) -> list[Path]:
    script = trajectory_bundle_records_script_path()
    if not script.exists():
        raise FileNotFoundError(f"TrajectoryBundle record-export script not found: {script}")

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    cmd = ["Rscript", str(script), "--mode", mode, "--output", str(output_dir)]
    for seed_dataset_id in seed_dataset_ids:
        cmd.extend(["--seed-dataset-id", seed_dataset_id])
    result = subprocess.run(cmd, cwd=repository_root(), check=False)
    if result.returncode != 0:
        raise RuntimeError(f"TrajectoryBundle record export failed with exit code {result.returncode}")

    return [
        output_dir / f"{_sanitize_name(seed_dataset_id)}_records.json"
        for seed_dataset_id in seed_dataset_ids
    ]


def discover_and_rank_trajectory_bundles(
    *,
    ranked_candidates_path: str | Path,
    output: str | None = None,
    run_id: str | None = None,
    mode: str = "live",
    top_n: int = 5,
) -> Path:
    ranked_candidates_path = Path(ranked_candidates_path)
    ranked_candidates_payload = json.loads(ranked_candidates_path.read_text())
    seed_dataset_ids = select_seed_dataset_ids(ranked_candidates_payload, top_n=top_n)
    run_dir = Path(output) if output else prepare_run_directory("runs", run_id=run_id, prefix="trajectory_bundle")
    run_dir.mkdir(parents=True, exist_ok=True)

    fixtures_dir = run_dir / "seed_record_fixtures"
    bundle_dir = run_dir / "trajectory_bundles"
    fixtures_dir.mkdir(exist_ok=True)
    bundle_dir.mkdir(exist_ok=True)

    fixture_paths = export_seed_record_fixtures(
        seed_dataset_ids=seed_dataset_ids,
        output_dir=fixtures_dir,
        mode=mode,
    )

    bundle_payloads: list[dict[str, Any]] = []
    for seed_dataset_id, fixture_path in zip(seed_dataset_ids, fixture_paths):
        bundle = discover_trajectory_bundle_from_file(fixture_path, seed_dataset_id)
        bundle_output_dir = bundle_dir / _sanitize_name(seed_dataset_id)
        bundle_output_dir.mkdir(exist_ok=True)
        write_trajectory_bundle(bundle_output_dir, bundle)
        bundle_payloads.append(bundle)

    ranked_bundles = rank_trajectory_bundle_payloads(bundle_payloads)
    write_ranked_trajectory_bundles(run_dir, ranked_bundles)

    summary = {
        "source_ranked_candidates": str(ranked_candidates_path),
        "mode": mode,
        "top_n_requested": top_n,
        "seed_dataset_ids": seed_dataset_ids,
        "bundle_count": ranked_bundles["bundle_count"],
        "top_bundle_id": ranked_bundles["ranked_trajectory_bundles"][0]["bundle_id"] if ranked_bundles["ranked_trajectory_bundles"] else None,
    }
    write_json(run_dir / "trajectory_bundle_pipeline_summary.json", summary)
    write_markdown(
        run_dir / "trajectory_bundle_pipeline_summary.md",
        "\n".join(
            [
                "# Trajectory Bundle Pipeline Summary",
                "",
                f"- Source ranked candidates: `{ranked_candidates_path}`",
                f"- Mode: `{mode}`",
                f"- Top N requested: `{top_n}`",
                f"- Bundle count: `{ranked_bundles['bundle_count']}`",
                f"- Top bundle: `{summary['top_bundle_id']}`",
            ]
        )
        + "\n",
    )
    return run_dir
