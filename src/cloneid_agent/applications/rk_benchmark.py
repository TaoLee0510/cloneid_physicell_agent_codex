"""CLONEID-LTE r/K benchmark application."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..cloneid_lte_standard import write_cloneid_lte_standard
from ..rk_benchmark_figures import generate_rk_benchmark_figures
from ..rk_benchmark_report import write_rk_benchmark_reports
from ..rk_density_models import (
    build_model_comparison_rows,
    build_model_family_specification,
    fit_cloneid_coarse_models,
    fit_cloneid_full_models,
    fit_nsr_reconstructed_models,
    model_family_specification_markdown,
    write_model_comparison_csv,
)
from ..rk_downsampling import (
    build_event_graph,
    build_event_schedule,
    build_growth_episode_table,
    build_mock_cloneid_full_record,
    build_perspective_endpoint_table,
    build_spatial_phenotype_table,
    downsample_cloneid_record,
    write_csv_rows,
)
from ..rk_modelability_audit import build_modelability_audit_rows, write_modelability_audit_csv
from ..rk_publication_record_extraction import extract_nwaa124_publication_record
from ..run_io import write_json, write_markdown


RK_BENCHMARK_SUBDIRS = (
    "external_comparator",
    "cloneid_full",
    "cloneid_downsampled",
    "modeling",
    "standards",
    "figures",
)


def _ensure_subdirs(output: Path) -> dict[str, Path]:
    output.mkdir(parents=True, exist_ok=True)
    subdirs = {}
    for name in RK_BENCHMARK_SUBDIRS:
        subdir = output / name
        subdir.mkdir(parents=True, exist_ok=True)
        subdirs[name] = subdir
    return subdirs


def _write_cloneid_full_artifacts(full_record: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    event_graph = build_event_graph(full_record["passaging_records"])
    event_schedule = build_event_schedule(full_record["passaging_records"])
    growth_episodes = build_growth_episode_table(full_record["passaging_records"])
    spatial_table = build_spatial_phenotype_table(full_record["passaging_records"])
    perspective_table = build_perspective_endpoint_table(full_record["perspective_records"])

    write_json(output_dir / "subtree_records.json", full_record)
    write_json(output_dir / "event_graph.json", event_graph)
    write_json(output_dir / "event_schedule.json", event_schedule)
    write_csv_rows(output_dir / "growth_episode_table.csv", growth_episodes)
    write_csv_rows(output_dir / "spatial_phenotype_table.csv", spatial_table)
    write_csv_rows(output_dir / "perspective_endpoint_table.csv", perspective_table)

    return {
        "event_graph": event_graph,
        "event_schedule": event_schedule,
        "growth_episodes": growth_episodes,
        "spatial_phenotype_table": spatial_table,
        "perspective_endpoint_table": perspective_table,
    }


def _write_downsampled_artifacts(coarse_record: dict[str, Any], output_dir: Path) -> None:
    write_json(output_dir / "publication_level_coarse_record.json", coarse_record)
    write_csv_rows(output_dir / "coarse_growth_summary.csv", coarse_record["coarse_growth_summary"])
    write_json(output_dir / "coarse_missingness_profile.json", coarse_record["missingness_profile"])


def _write_modeling_artifacts(
    output_dir: Path,
    *,
    nsr_fits: dict[str, Any],
    cloneid_full_fits: dict[str, Any],
    cloneid_coarse_fits: dict[str, Any],
    comparison_rows: list[dict[str, Any]],
) -> dict[str, Path]:
    specification = build_model_family_specification()
    return {
        "model_family_specification_json": write_json(
            output_dir / "model_family_specification.json",
            specification,
        ),
        "model_family_specification_md": write_markdown(
            output_dir / "model_family_specification.md",
            model_family_specification_markdown(specification),
        ),
        "nsr_reconstructed_model_fits": write_json(
            output_dir / "nsr_reconstructed_model_fits.json",
            nsr_fits,
        ),
        "cloneid_full_model_fits": write_json(
            output_dir / "cloneid_full_model_fits.json",
            cloneid_full_fits,
        ),
        "cloneid_coarse_model_fits": write_json(
            output_dir / "cloneid_coarse_model_fits.json",
            cloneid_coarse_fits,
        ),
        "model_comparison_csv": write_model_comparison_csv(
            output_dir / "model_comparison_publication_vs_cloneid.csv",
            comparison_rows,
        ),
        "model_comparison_json": write_json(
            output_dir / "model_comparison_publication_vs_cloneid.json",
            comparison_rows,
        ),
    }


def run_rk_benchmark(
    *,
    external_zip: str | None,
    cloneid_root_id: str | None = "auto",
    mode: str = "mock",
    output: str | Path = "runs/rk_benchmark_v1",
    fit: bool = False,
    make_figures: bool = False,
) -> Path:
    """Run the benchmark and write all required artifacts."""

    output_dir = Path(output)
    subdirs = _ensure_subdirs(output_dir)

    external_record = extract_nwaa124_publication_record(external_zip, subdirs["external_comparator"])
    audit_rows = build_modelability_audit_rows()
    write_modelability_audit_csv(subdirs["external_comparator"] / "nwaa124_modelability_audit.csv", audit_rows)

    live_status = "mock_mode_requested"
    if mode in {"auto", "live"}:
        live_status = "live_access_not_configured_fell_back_to_deterministic_mock"
    full_record = build_mock_cloneid_full_record(cloneid_root_id)
    full_record["requested_mode"] = mode
    full_record["live_access_status"] = live_status
    full_artifacts = _write_cloneid_full_artifacts(full_record, subdirs["cloneid_full"])

    coarse_record = downsample_cloneid_record(full_record)
    _write_downsampled_artifacts(coarse_record, subdirs["cloneid_downsampled"])

    if fit:
        nsr_fits = fit_nsr_reconstructed_models(external_record)
        cloneid_full_fits = fit_cloneid_full_models(full_artifacts["growth_episodes"])
        cloneid_coarse_fits = fit_cloneid_coarse_models(coarse_record)
    else:
        nsr_fits = {"models": [], "fit_status": "not_run"}
        cloneid_full_fits = {"models": [], "fit_status": "not_run"}
        cloneid_coarse_fits = {"models": [], "fit_status": "not_run"}

    comparison_rows = build_model_comparison_rows(
        nsr_fits=nsr_fits,
        cloneid_full_fits=cloneid_full_fits,
        cloneid_coarse_fits=cloneid_coarse_fits,
    )
    modeling_paths = _write_modeling_artifacts(
        subdirs["modeling"],
        nsr_fits=nsr_fits,
        cloneid_full_fits=cloneid_full_fits,
        cloneid_coarse_fits=cloneid_coarse_fits,
        comparison_rows=comparison_rows,
    )

    standards_paths = write_cloneid_lte_standard(subdirs["standards"])
    figure_paths = {}
    if make_figures:
        figure_paths = generate_rk_benchmark_figures(
            output_dir=subdirs["figures"],
            audit_rows=audit_rows,
            figure_index=external_record["figure_index"],
            model_records=external_record["model_records"],
            event_graph=full_artifacts["event_graph"],
            growth_episodes=full_artifacts["growth_episodes"],
            coarse_record=coarse_record,
            comparison_rows=comparison_rows,
        )

    reports = write_rk_benchmark_reports(
        output_dir,
        nsr_fits=nsr_fits,
        cloneid_full_fits=cloneid_full_fits,
        cloneid_coarse_fits=cloneid_coarse_fits,
        comparison_rows=comparison_rows,
    )

    manifest = {
        "application": "CLONEID-LTE r/K benchmark",
        "scientific_objective": "from publication-level r/K records to event-linked, agent-ready model inputs",
        "central_question": "Can r/K density adaptation be explained by proliferation-rate differences alone, or does it require density/confluence/spatial interaction terms?",
        "external_comparator": "Li et al. National Science Review 2021 nwaa124",
        "mode": mode,
        "live_access_status": live_status,
        "fit": fit,
        "make_figures": make_figures,
        "artifact_roots": {name: str(path) for name, path in subdirs.items()},
        "external_file_count": external_record["inventory"]["file_count"],
        "modeling_paths": {key: str(path) for key, path in modeling_paths.items()},
        "standards_paths": {key: str(path) for key, path in standards_paths.items()},
        "figure_paths": {key: str(path) for key, path in figure_paths.items()},
        "report_paths": {key: str(path) for key, path in reports.items()},
        "overclaim_guardrails": [
            "NSR is treated as a strong biological comparator.",
            "Plot-only evidence is not fitted as raw data.",
            "Transfer/passaging events are not biological growth episodes.",
            "Endpoint Perspective is validation/support only.",
        ],
    }
    write_json(output_dir / "application_manifest.json", manifest)
    return output_dir


def audit_nwaa124_comparator(*, external_zip: str | None, output_dir: str | Path) -> Path:
    output = Path(output_dir)
    extract_nwaa124_publication_record(external_zip, output)
    write_modelability_audit_csv(output / "nwaa124_modelability_audit.csv")
    return output
