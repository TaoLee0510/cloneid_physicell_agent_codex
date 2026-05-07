"""One-command application orchestration for the SNU-668 density-history framework."""

from __future__ import annotations

from datetime import datetime, UTC
import json
import shutil
from pathlib import Path
from typing import Any

from .comparative_identifiability import (
    build_comparative_identifiability,
    write_comparative_identifiability,
)
from .compressed_view import build_published_like_compressed_view, write_compressed_view
from .external_curated_adapter import (
    load_external_curated_dataset,
    summarize_external_curated_dataset,
)
from .family_comparison import (
    build_family_comparison,
    build_model_family_library,
    write_family_comparison,
    write_model_family_candidates,
)
from .history_ablation import build_history_ablation, write_history_ablation
from .history_covariates import (
    build_dry_run_snu668_fixture,
    build_history_covariates,
    write_history_covariates,
)
from .observability_profile import build_observability_profile, write_observability_profile
from .rejection_logging import write_rejection_report
from .run_io import write_json, write_markdown


PIPELINE_STAGES = (
    "agent_plan",
    "database_inventory",
    "selected_dataset",
    "selected_lineage_object",
    "selected_observables",
    "history_covariates",
    "history_ablation",
    "compressed_view",
    "external_comparator",
    "physicell_mapping",
    "generated_model_candidates",
    "observability_matrix",
    "family_comparison",
    "rejection_report",
    "comparative_identifiability_report",
    "model_selection_report",
    "manuscript_facing_summary",
    "figure_data",
)


def load_application_config(path: str | Path) -> dict[str, Any]:
    """Load a dependency-free JSON-compatible YAML config."""
    text = Path(path).read_text()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{path} must be JSON-compatible YAML because PyYAML is not a project dependency"
        ) from exc


def _prepare_output_dir(output: str | Path, *, resume_from: str | None = None) -> Path:
    output_dir = Path(output)
    if output_dir.exists() and any(output_dir.iterdir()) and not resume_from:
        raise FileExistsError(
            f"Output directory already exists and is not empty: {output_dir}. Use --resume-from to continue intentionally."
        )
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "figure_data").mkdir(parents=True, exist_ok=True)
    return output_dir


def _maybe_stop(stage: str, stop_after: str | None) -> bool:
    return stop_after == stage


def _write_agent_plan(output_dir: Path, config: dict[str, Any], mode: str, strict_provenance: bool) -> dict[str, Any]:
    payload = {
        "agent_plan_schema_version": "snu668_density_history_plan_v1",
        "created_at": datetime.now(UTC).isoformat(),
        "mode": mode,
        "strict_provenance": strict_provenance,
        "scientific_question": config["scientific_question"],
        "comparison_regimes": config["comparison_regimes"],
        "model_families": config["model_families"],
        "pipeline_stages": list(PIPELINE_STAGES),
        "guardrails": config.get("guardrails", []),
        "database_policy": "read-only; no database writes; dry-run/mock uses a labeled fixture only",
    }
    write_json(output_dir / "agent_plan.json", payload)
    write_markdown(
        output_dir / "agent_plan.md",
        "\n".join(
            [
                "# Agent Plan",
                "",
                f"- Mode: `{mode}`",
                f"- Strict provenance: `{strict_provenance}`",
                f"- Scientific question: {config['scientific_question']}",
                f"- Regimes: `{', '.join(config['comparison_regimes'])}`",
                f"- Families: `{', '.join(config['model_families'])}`",
                "",
            ]
        ),
    )
    return payload


def _write_database_inventory(output_dir: Path, mode: str, external_accessible: bool) -> dict[str, Any]:
    payload = {
        "inventory_schema_version": "application_database_inventory_v1",
        "mode": mode,
        "live_snu668_access_attempted": False,
        "live_snu668_access_available": None,
        "database_write_attempted": False,
        "read_only_policy_preserved": True,
        "internal_dataset_source": "mock_schema_fixture_not_observed_cloneid_data" if mode in {"dry-run", "mock"} else "not_loaded",
        "external_supplement_path_accessible": external_accessible,
        "warnings": [
            "Dry-run/mock mode does not support biological interpretation of SNU-668 numeric fixture values.",
            "Use live read-only CLONEID extraction or an approved snapshot before manuscript numerical claims.",
        ],
    }
    write_json(output_dir / "database_inventory.json", payload)
    write_markdown(
        output_dir / "database_inventory.md",
        "\n".join(
            [
                "# Database Inventory",
                "",
                f"- Mode: `{mode}`",
                f"- Live SNU-668 access attempted: `{payload['live_snu668_access_attempted']}`",
                f"- Database write attempted: `{payload['database_write_attempted']}`",
                f"- External supplement path accessible: `{external_accessible}`",
                "",
            ]
        ),
    )
    return payload


def _write_selected_dataset(output_dir: Path, dataset: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "selected_dataset_schema_version": "selected_dataset_v1",
        "dataset_regime": dataset["dataset_regime"],
        "dataset_id": dataset["dataset_id"],
        "cell_line": "SNU-668",
        "data_status": dataset["data_status"],
        "selection_reason": "application-pinned SNU-668 density-history proof-of-principle target",
        "provenance_policy": dataset["provenance_policy"],
    }
    write_json(output_dir / "selected_dataset.json", payload)
    write_markdown(
        output_dir / "selected_dataset.md",
        f"# Selected Dataset\n\n- Dataset id: `{payload['dataset_id']}`\n- Data status: `{payload['data_status']}`\n",
    )
    return payload


def _write_selected_lineage_object(output_dir: Path, dataset: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "selected_lineage_object_schema_version": "selected_lineage_object_v1",
        "selected_lineage_object_id": dataset["lineage_object_id"],
        "selected_lineage_object_type": dataset["lineage_object_type"],
        "dataset_regime": dataset["dataset_regime"],
        "data_status": dataset["data_status"],
        "root_event_id": dataset["passaging_records"][0]["id"],
        "endpoint_event_ids": [dataset["passaging_records"][-1]["id"]],
        "passaging_records": dataset["passaging_records"],
        "perspective_records": dataset["perspective_records"],
        "identity_records": dataset["identity_records"],
        "ontology_notes": [
            "Perspective is endpoint or assay-specific support, not longitudinal phenotype.",
            "Identity is inferred secondary support only.",
        ],
    }
    write_json(output_dir / "selected_lineage_object.json", payload)
    write_markdown(
        output_dir / "selected_lineage_object.md",
        f"# Selected Lineage Object\n\n- Id: `{payload['selected_lineage_object_id']}`\n- Type: `{payload['selected_lineage_object_type']}`\n- Events: `{len(dataset['passaging_records'])}`\n",
    )
    return payload


def _write_selected_observables(output_dir: Path, dataset: dict[str, Any]) -> dict[str, Any]:
    records = dataset.get("passaging_records", [])
    payload = {
        "selected_observables_schema_version": "snu668_density_observables_v1",
        "dataset_regime": dataset["dataset_regime"],
        "data_status": dataset["data_status"],
        "selected": [
            {
                "source": "Passaging.cellCount",
                "target": "longitudinal viable count proxy",
                "supporting_rows": sum(1 for row in records if row.get("cellCount") is not None),
                "evidence_class": "event_linked_phenotype",
                "allowed_uses": ["calibration", "comparison"],
            },
            {
                "source": "Passaging.correctedCount",
                "target": "derived longitudinal count proxy",
                "supporting_rows": sum(1 for row in records if row.get("correctedCount") is not None),
                "evidence_class": "derived_event_linked_phenotype",
                "allowed_uses": ["calibration", "sensitivity"],
            },
            {
                "source": "Passaging.areaOccupied_um2",
                "target": "crowding / confluence proxy",
                "supporting_rows": sum(1 for row in records if row.get("areaOccupied_um2") is not None),
                "evidence_class": "derived_event_linked_phenotype",
                "allowed_uses": ["density_history_covariate", "comparison"],
            },
            {
                "source": "event/episode duration",
                "target": "growth episode timing",
                "supporting_rows": len(records),
                "evidence_class": "event_context",
                "allowed_uses": ["schedule", "history_covariate"],
            },
            {
                "source": "Perspective.size",
                "target": "terminal endpoint support",
                "supporting_rows": len(dataset.get("perspective_records", [])),
                "evidence_class": "endpoint_support_only",
                "allowed_uses": ["validation"],
            },
        ],
        "optional_absent_features": [
            "compactness",
            "local packing proxy",
            "nearest-neighbor proxy",
            "edge expansion proxy",
        ],
    }
    write_json(output_dir / "selected_observables.json", payload)
    write_markdown(
        output_dir / "selected_observables.md",
        "\n".join(["# Selected Observables", ""] + [f"- `{item['source']}` -> {item['target']}" for item in payload["selected"]]) + "\n",
    )
    return payload


def _write_physicell_mapping(output_dir: Path, selected_observables: dict[str, Any]) -> dict[str, Any]:
    payload = {
        "physicell_mapping_schema_version": "density_history_mapping_v1",
        "model_backend": "PhysiCell v1.14.2-compatible manifest placeholder",
        "recommended_model_families": ["neutral_growth", "fixed_state_fitness", "density_dependent_growth"],
        "observable_mapping": [
            {
                "cloneid_source": item["source"],
                "model_target": item["target"],
                "evidence_class": item["evidence_class"],
                "allowed_uses": item["allowed_uses"],
            }
            for item in selected_observables["selected"]
        ],
        "transfer_event_mapping": "explicit reset / bottleneck semantics for density_dependent_growth; initialization context only for fixed_state_fitness",
        "non_goals": [
            "no fitted parameters in dry-run/mock mode",
            "no Identity-as-phenotype mapping",
            "no Perspective-as-longitudinal-growth mapping",
        ],
    }
    write_json(output_dir / "physicell_mapping.json", payload)
    write_markdown(
        output_dir / "physicell_mapping.md",
        "# PhysiCell Mapping\n\nTransfer events are explicit reset/bottleneck context; Perspective is endpoint validation only.\n",
    )
    return payload


def _write_model_selection_report(
    output_dir: Path,
    *,
    selected_dataset: dict[str, Any],
    family_comparison: dict[str, Any],
    identifiability: dict[str, Any],
) -> None:
    selected_rows = [
        row for row in family_comparison["comparison_rows"] if row["selected_under_tested_assumptions"]
    ]
    lines = [
        "# Model Selection Report",
        "",
        "This is a proof of principle framework report. In dry-run/mock mode, internal SNU-668 numeric values are schema fixtures and are not biological observations.",
        "",
        "## Selected dataset / lineage object",
        "",
        f"- Dataset: `{selected_dataset['dataset_id']}`",
        f"- Regime: `{selected_dataset['dataset_regime']}`",
        f"- Data status: `{selected_dataset['data_status']}`",
        "",
        "## Compared model families",
        "",
        "- `neutral_growth`: constant birth/death with no advantage or density feedback.",
        "- `fixed_state_fitness`: constant branch/regime-specific proliferation or death advantage.",
        "- `density_dependent_growth`: crowding/confluence-history-dependent growth with transfer/reset semantics.",
        "",
        "## Compared data regimes",
        "",
        "- `snu668_full_history`",
        "- `snu668_published_like_compressed`",
        "- `nwaa124_curated_external`",
        "",
        "## Supported under tested assumptions",
        "",
    ]
    if selected_rows:
        for row in selected_rows:
            lines.append(f"- `{row['dataset_regime']}` supports `{row['family']}` under tested assumptions.")
    else:
        lines.append("- No family is selected under tested assumptions in this dry-run output.")
    lines.extend(
        [
            "",
            "## Rejected or unresolved under tested assumptions",
            "",
        ]
    )
    for row in family_comparison["comparison_rows"]:
        if not row["selected_under_tested_assumptions"]:
            lines.append(f"- `{row['dataset_regime']}` / `{row['family']}`: {row['rejection_reason']}")
    lines.extend(
        [
            "",
            "## What CLONEID uniquely preserves",
            "",
            "CLONEID preserves event order, parent-event linkage, transfer timing, event-linked derived phenotype, and terminal Perspective anchors. Those are the fields that make fixed-state versus density-history-dependent model families auditable.",
            "",
            "## Sparse-view limitations",
            "",
            "The compressed and external arms are about observability/identifiability loss. They do not establish that HeLa and SNU-668 biology are equivalent, do not challenge the external paper, and do not benchmark the external paper's simulator as ground truth.",
            "",
            "## Low-cost additional fields",
            "",
        ]
    )
    for item in identifiability["low_cost_fields_that_rescue_identifiability"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## Ontology guardrails",
            "",
            "- Terminal Perspective is endpoint validation/support only.",
            "- Identity is inferred secondary support only.",
            "- Derived count / area / confluence-like quantities require explicit processing provenance.",
        ]
    )
    write_markdown(output_dir / "model_selection_report.md", "\n".join(lines) + "\n")


def _write_manuscript_summary(output_dir: Path, family_comparison: dict[str, Any]) -> None:
    lines = [
        "# Manuscript-Facing Summary",
        "",
        "Proof of principle: full CLONEID event history enables auditable discrimination between fixed-state and density-history-dependent model families, whereas compressed or externally published sparse views leave this comparison partially unresolved.",
        "",
        "This statement is bounded to observability and tested assumptions. In dry-run/mock mode, the SNU-668 numerical fixture is for schema validation only. This is not a cross-cell-line biological truth claim, does not challenge the external paper, and does not use the external simulator as ground truth.",
        "",
        "## Key comparison",
        "",
    ]
    for row in family_comparison["comparison_rows"]:
        if row["family"] in {"fixed_state_fitness", "density_dependent_growth"}:
            lines.append(
                f"- `{row['dataset_regime']}` / `{row['family']}`: auditability `{row['auditability_grade']}`, identifiability `{row['identifiability_grade']}`, selected `{row['selected_under_tested_assumptions']}`."
            )
    write_markdown(output_dir / "manuscript_facing_summary.md", "\n".join(lines) + "\n")


def _write_figure_data(output_dir: Path) -> None:
    figure_dir = output_dir / "figure_data"
    for name in (
        "observability_matrix.csv",
        "family_comparison.csv",
        "history_covariates.csv",
        "compressed_view.csv",
    ):
        source = output_dir / name
        if source.exists():
            shutil.copyfile(source, figure_dir / name)
    write_markdown(
        figure_dir / "README.md",
        "# Figure Data\n\nCSV files here are direct copies of auditable run outputs for manuscript figure drafting.\n",
    )


def run_application(
    *,
    config_path: str | Path,
    output: str | Path,
    mode: str = "dry-run",
    resume_from: str | None = None,
    stop_after: str | None = None,
    use_snapshot: str | None = None,
    strict_provenance: bool = False,
) -> dict[str, Any]:
    if mode not in {"dry-run", "mock", "live"}:
        raise ValueError(f"Unsupported mode: {mode}")
    if mode == "live" and not use_snapshot:
        raise ValueError("live mode requires --use-snapshot or a future read-only SNU-668 live extraction implementation")
    config = load_application_config(config_path)
    output_dir = _prepare_output_dir(output, resume_from=resume_from)
    external_root = Path(config["external_comparator"]["data_root"])
    external_accessible = external_root.exists()

    agent_plan = _write_agent_plan(output_dir, config, mode, strict_provenance)
    if _maybe_stop("agent_plan", stop_after):
        return {"output_dir": str(output_dir), "stopped_after": "agent_plan"}

    database_inventory = _write_database_inventory(output_dir, mode, external_accessible)
    if _maybe_stop("database_inventory", stop_after):
        return {"output_dir": str(output_dir), "stopped_after": "database_inventory"}

    dataset = build_dry_run_snu668_fixture()
    selected_dataset = _write_selected_dataset(output_dir, dataset)
    if _maybe_stop("selected_dataset", stop_after):
        return {"output_dir": str(output_dir), "stopped_after": "selected_dataset"}

    _write_selected_lineage_object(output_dir, dataset)
    selected_observables = _write_selected_observables(output_dir, dataset)
    history_covariates = build_history_covariates(dataset)
    write_history_covariates(output_dir, history_covariates)
    compressed = build_published_like_compressed_view(dataset, history_covariates)
    write_compressed_view(output_dir, compressed)
    history_ablation = build_history_ablation(history_covariates, compressed)
    write_history_ablation(output_dir, history_ablation)

    external_comparator = load_external_curated_dataset(external_root)
    write_json(output_dir / "external_comparator.json", external_comparator)
    write_markdown(output_dir / "external_comparator.md", summarize_external_curated_dataset(external_comparator))
    if _maybe_stop("external_comparator", stop_after):
        return {"output_dir": str(output_dir), "stopped_after": "external_comparator"}

    _write_physicell_mapping(output_dir, selected_observables)
    family_library = build_model_family_library()
    write_model_family_candidates(output_dir, family_library)

    observability = build_observability_profile(
        history_covariates=history_covariates,
        compressed_view=compressed,
        external_comparator=external_comparator,
    )
    write_observability_profile(output_dir, observability)

    family_comparison = build_family_comparison(
        observability_profile=observability,
        history_ablation=history_ablation,
    )
    write_family_comparison(output_dir, family_comparison)
    write_rejection_report(output_dir, family_comparison)

    identifiability = build_comparative_identifiability(
        observability_profile=observability,
        family_comparison=family_comparison,
        history_ablation=history_ablation,
    )
    write_comparative_identifiability(output_dir, identifiability)

    _write_model_selection_report(
        output_dir,
        selected_dataset=selected_dataset,
        family_comparison=family_comparison,
        identifiability=identifiability,
    )
    _write_manuscript_summary(output_dir, family_comparison)
    _write_figure_data(output_dir)

    return {
        "output_dir": str(output_dir),
        "mode": mode,
        "agent_plan": agent_plan,
        "database_inventory": database_inventory,
        "dry_run_mock_succeeded": mode in {"dry-run", "mock"},
    }
