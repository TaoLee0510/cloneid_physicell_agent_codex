"""CLONEID-LTE r/K benchmark application."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..cloneid_lte_standard import write_cloneid_lte_standard
from ..cloneid_live_rk_extraction import load_live_cloneid_rk_record, parse_cloneid_root_ids
from ..comparative_identifiability import (
    build_comparative_identifiability,
    write_comparative_identifiability,
)
from ..compressed_view import build_published_like_compressed_view, write_compressed_view
from ..family_comparison import build_family_comparison, write_family_comparison
from ..history_ablation import build_history_ablation, write_history_ablation
from ..history_covariates import build_history_covariates, write_history_covariates
from ..observability_profile import build_observability_profile, write_observability_profile
from ..rejection_logging import write_rejection_report
from ..external_comparators.nwaa124 import create_minimal_mock_supplement_fixture
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
from ..rk_physicell_integration import build_physicell_analysis, write_physicell_analysis
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
    "figure_data",
    "physicell",
)


def _ensure_subdirs(output: Path) -> dict[str, Path]:
    output.mkdir(parents=True, exist_ok=True)
    subdirs = {}
    for name in RK_BENCHMARK_SUBDIRS:
        subdir = output / name
        subdir.mkdir(parents=True, exist_ok=True)
        subdirs[name] = subdir
    return subdirs


def _load_optional_config(config_path: str | Path | None) -> dict[str, Any]:
    if not config_path:
        return {}
    path = Path(config_path)
    text = path.read_text()
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{path} must be JSON-compatible YAML because PyYAML is not a project dependency"
        ) from exc
    payload["_config_path"] = str(path)
    return payload


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


def _copy_text_file(source: Path, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text())
    return target


def _write_paper_facing_aliases(
    output_dir: Path,
    *,
    subdirs: dict[str, Path],
    paths: dict[str, Any],
) -> dict[str, Path]:
    """Write root-level aliases for the manuscript-facing artifact contract."""

    aliases: dict[str, Path] = {}
    root_aliases = {
        "observability_matrix_json": (subdirs["modeling"] / "observability_matrix.json", output_dir / "observability_matrix.json"),
        "observability_matrix_csv": (subdirs["modeling"] / "observability_matrix.csv", output_dir / "observability_matrix.csv"),
        "dataset_missingness_md": (subdirs["modeling"] / "dataset_missingness.md", output_dir / "dataset_missingness.md"),
        "family_comparison_json": (subdirs["modeling"] / "family_comparison.json", output_dir / "family_comparison.json"),
        "family_comparison_csv": (subdirs["modeling"] / "family_comparison.csv", output_dir / "family_comparison.csv"),
        "comparative_identifiability_report_md": (
            subdirs["modeling"] / "comparative_identifiability_report.md",
            output_dir / "comparative_identifiability_report.md",
        ),
        "rejection_report_md": (subdirs["modeling"] / "rejection_report.md", output_dir / "rejection_report.md"),
        "history_covariates_json": (subdirs["cloneid_full"] / "history_covariates.json", output_dir / "history_covariates.json"),
        "history_covariates_md": (subdirs["cloneid_full"] / "history_covariates.md", output_dir / "history_covariates.md"),
        "history_ablation_json": (subdirs["cloneid_downsampled"] / "history_ablation.json", output_dir / "history_ablation.json"),
        "history_ablation_md": (subdirs["cloneid_downsampled"] / "history_ablation.md", output_dir / "history_ablation.md"),
        "minimum_longitudinal_evolution_record": (
            Path(__file__).resolve().parents[3] / "docs/standards/minimum_longitudinal_evolution_record.md",
            output_dir / "minimum_longitudinal_evolution_record.md",
        ),
    }
    for key, (source, target) in root_aliases.items():
        if source.exists():
            aliases[key] = _copy_text_file(source, target)

    figure_data_sources = {
        "observability_matrix_csv": subdirs["modeling"] / "observability_matrix.csv",
        "family_comparison_csv": subdirs["modeling"] / "family_comparison.csv",
        "model_comparison_publication_vs_cloneid_csv": subdirs["modeling"] / "model_comparison_publication_vs_cloneid.csv",
        "history_covariates_csv": subdirs["cloneid_full"] / "history_covariates.csv",
        "coarse_growth_summary_csv": subdirs["cloneid_downsampled"] / "coarse_growth_summary.csv",
        "history_ablation_json": subdirs["cloneid_downsampled"] / "history_ablation.json",
    }
    for key, source in figure_data_sources.items():
        if source.exists():
            target = subdirs["figure_data"] / source.name
            aliases[f"figure_data_{key}"] = _copy_text_file(source, target)
    aliases.update({key: value for key, value in paths.items() if isinstance(value, Path)})
    return aliases


def run_rk_benchmark(
    *,
    external_zip: str | None,
    cloneid_root_id: str | None = "auto",
    mode: str = "mock",
    output: str | Path = "runs/rk_benchmark_v1",
    fit: bool = False,
    make_figures: bool = False,
    config_path: str | Path | None = None,
    run_physicell: bool = False,
    physicell_root: str | Path | None = None,
    execute_physicell: bool = False,
    physicell_runtime_max_time: int = 60,
) -> Path:
    """Run the benchmark and write all required artifacts."""

    config = _load_optional_config(config_path)
    if not external_zip:
        external_zip = config.get("external_zip") or config.get("external_comparator", {}).get("source_root_preferred")
    if cloneid_root_id in (None, "auto"):
        cloneid_root_id = config.get("cloneid_root_id", cloneid_root_id)
    run_physicell = run_physicell or bool(config.get("run_physicell", False))
    physicell_config = config.get("physicell", {})
    if physicell_root is None:
        physicell_root = config.get("physicell_root") or physicell_config.get("root")
    physicell_executable = config.get("physicell_executable") or physicell_config.get("executable")
    physicell_source_config = config.get("physicell_source_config") or physicell_config.get("source_config")
    execute_physicell = execute_physicell or bool(
        config.get("execute_physicell", False) or physicell_config.get("execute", False)
    )
    if physicell_runtime_max_time == 60:
        physicell_runtime_max_time = int(
            config.get(
                "physicell_runtime_max_time",
                physicell_config.get("runtime_max_time", physicell_runtime_max_time),
            )
        )

    output_dir = Path(output)
    subdirs = _ensure_subdirs(output_dir)

    external_fixture_warning = None
    try:
        external_record = extract_nwaa124_publication_record(external_zip, subdirs["external_comparator"])
    except FileNotFoundError:
        if mode != "mock":
            raise
        fallback_external = create_minimal_mock_supplement_fixture(subdirs["external_comparator"])
        external_fixture_warning = (
            f"Requested external archive was unavailable; mock mode used a minimal extraction fixture at {fallback_external}. "
            "Manuscript comparator interpretation requires the real NSR supplement archive or directory."
        )
        external_record = extract_nwaa124_publication_record(fallback_external, subdirs["external_comparator"])
    audit_rows = build_modelability_audit_rows()
    write_modelability_audit_csv(subdirs["external_comparator"] / "nwaa124_modelability_audit.csv", audit_rows)

    live_status = "mock_mode_requested"
    live_extraction_error = None
    requested_root_ids = parse_cloneid_root_ids(cloneid_root_id)
    if mode in {"auto", "live"} and requested_root_ids:
        try:
            full_record = load_live_cloneid_rk_record(
                root_ids=requested_root_ids,
                output_dir=subdirs["cloneid_full"],
            )
            live_status = "live_read_only_cloneid_extraction_succeeded"
        except Exception as exc:
            live_extraction_error = str(exc)
            if mode == "live":
                raise
            live_status = "live_access_failed_auto_fell_back_to_deterministic_mock"
            full_record = build_mock_cloneid_full_record(cloneid_root_id)
    elif mode == "live":
        raise ValueError("--mode live requires --cloneid-root-id with one or more event IDs")
    else:
        full_record = build_mock_cloneid_full_record(cloneid_root_id)

    full_record["dataset_regime"] = "snu668_full_history"
    full_record.setdefault("dataset_id", "snu668_rk_density_history_mock_fixture")
    full_record.setdefault("data_status", "deterministic_mock_schema_fixture_not_observed_cloneid_data")
    full_record["requested_mode"] = mode
    full_record["requested_root_ids"] = requested_root_ids
    full_record["live_access_status"] = live_status
    if live_extraction_error:
        full_record["live_extraction_error"] = live_extraction_error
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

    history_covariates = build_history_covariates(full_record)
    history_paths = write_history_covariates(subdirs["cloneid_full"], history_covariates)
    compressed_view = build_published_like_compressed_view(full_record, history_covariates, coarse_record)
    compressed_paths = write_compressed_view(subdirs["cloneid_downsampled"], compressed_view)
    history_ablation = build_history_ablation(
        history_covariates,
        compressed_view,
        cloneid_full_fits=cloneid_full_fits,
        cloneid_coarse_fits=cloneid_coarse_fits,
    )
    history_ablation_downsampled_paths = write_history_ablation(subdirs["cloneid_downsampled"], history_ablation)
    history_ablation_modeling_paths = write_history_ablation(subdirs["modeling"], history_ablation)
    observability_profile = build_observability_profile(
        nsr_record=external_record,
        history_covariates=history_covariates,
        compressed_view=compressed_view,
    )
    observability_paths = write_observability_profile(subdirs["modeling"], observability_profile)
    family_comparison = build_family_comparison(
        observability_profile=observability_profile,
        nsr_fits=nsr_fits,
        cloneid_full_fits=cloneid_full_fits,
        cloneid_coarse_fits=cloneid_coarse_fits,
    )
    family_comparison_paths = write_family_comparison(subdirs["modeling"], family_comparison)
    rejection_report_path = write_rejection_report(subdirs["modeling"], family_comparison)
    comparative_identifiability = build_comparative_identifiability(
        observability_profile=observability_profile,
        family_comparison=family_comparison,
        history_ablation=history_ablation,
    )
    comparative_identifiability_paths = write_comparative_identifiability(
        subdirs["modeling"],
        comparative_identifiability,
    )

    modeling_paths = _write_modeling_artifacts(
        subdirs["modeling"],
        nsr_fits=nsr_fits,
        cloneid_full_fits=cloneid_full_fits,
        cloneid_coarse_fits=cloneid_coarse_fits,
        comparison_rows=comparison_rows,
    )
    modeling_paths.update(
        {
            "observability_profile_json": observability_paths["json"],
            "observability_profile_csv": observability_paths["csv"],
            "observability_matrix_json": observability_paths["matrix_json"],
            "observability_matrix_csv": observability_paths["matrix_csv"],
            "dataset_missingness_md": observability_paths["dataset_missingness"],
            "history_ablation_json": history_ablation_modeling_paths["json"],
            "history_ablation_md": history_ablation_modeling_paths["md"],
            "family_comparison_json": family_comparison_paths["json"],
            "family_comparison_csv": family_comparison_paths["csv"],
            "rejection_report_md": rejection_report_path,
            "comparative_identifiability_report_json": comparative_identifiability_paths["json"],
            "comparative_identifiability_report_md": comparative_identifiability_paths["md"],
        }
    )

    physicell_analysis = None
    physicell_paths: dict[str, Path] = {}
    if run_physicell:
        physicell_analysis = build_physicell_analysis(
            growth_episodes=full_artifacts["growth_episodes"],
            event_schedule=full_artifacts["event_schedule"],
            perspective_table=full_artifacts["perspective_endpoint_table"],
            coarse_record=coarse_record,
            external_record=external_record,
            physicell_root=physicell_root,
            physicell_executable=physicell_executable,
            physicell_source_config=physicell_source_config,
            execute_physicell=execute_physicell,
            runtime_max_time=physicell_runtime_max_time,
        )
        physicell_paths = write_physicell_analysis(subdirs["physicell"], physicell_analysis)

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
            physicell_analysis=physicell_analysis,
        )

    reports = write_rk_benchmark_reports(
        output_dir,
        nsr_fits=nsr_fits,
        cloneid_full_fits=cloneid_full_fits,
        cloneid_coarse_fits=cloneid_coarse_fits,
        comparison_rows=comparison_rows,
        observability_profile=observability_profile,
        history_ablation=history_ablation,
        family_comparison=family_comparison,
        comparative_identifiability=comparative_identifiability,
        physicell_analysis=physicell_analysis,
        config=config,
    )

    paper_alias_paths = _write_paper_facing_aliases(
        output_dir,
        subdirs=subdirs,
        paths={
            "model_selection_report": reports["model_selection_report"],
            "required_data_by_question": reports["required_data_by_question"],
            "manuscript_facing_summary": reports["manuscript_facing_summary"],
            "family_discrimination_summary": reports["family_discrimination_summary"],
        },
    )

    manifest = {
        "application": "SNU-668 density-history proof-of-principle",
        "scientific_objective": "event-linked density-history model discrimination with publication-level observability comparators",
        "central_question": "In long-term r/K density selection, can late growth advantage be explained by fixed fitness alone, or is continuous event-linked crowding/confluence history required?",
        "external_comparator": "Li et al. National Science Review 2021 nwaa124",
        "comparison_regimes": [
            "snu668_full_history",
            "snu668_published_like_compressed",
            "nwaa124_curated_external",
        ],
        "manuscript_model_families": [
            "neutral_growth",
            "fixed_state_fitness",
            "density_dependent_growth",
        ],
        "mode": mode,
        "live_access_status": live_status,
        "live_extraction_error": live_extraction_error,
        "cloneid_requested_root_ids": requested_root_ids,
        "fit": fit,
        "make_figures": make_figures,
        "run_physicell": run_physicell,
        "physicell_root_requested": None if physicell_root is None else str(physicell_root),
        "physicell_executable_requested": None if physicell_executable is None else str(physicell_executable),
        "physicell_source_config_requested": None if physicell_source_config is None else str(physicell_source_config),
        "execute_physicell": execute_physicell,
        "config_path": config.get("_config_path"),
        "artifact_roots": {name: str(path) for name, path in subdirs.items()},
        "external_file_count": external_record["inventory"]["file_count"],
        "external_fixture_warning": external_fixture_warning,
        "history_covariate_paths": {key: str(path) for key, path in history_paths.items()},
        "compressed_view_paths": {key: str(path) for key, path in compressed_paths.items()},
        "history_ablation_paths": {key: str(path) for key, path in history_ablation_downsampled_paths.items()},
        "modeling_paths": {key: str(path) for key, path in modeling_paths.items()},
        "standards_paths": {key: str(path) for key, path in standards_paths.items()},
        "physicell_paths": {key: str(path) for key, path in physicell_paths.items()},
        "figure_paths": {key: str(path) for key, path in figure_paths.items()},
        "report_paths": {key: str(path) for key, path in reports.items()},
        "paper_facing_alias_paths": {key: str(path) for key, path in paper_alias_paths.items()},
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
