"""Observability profile across NSR, CLONEID full, and CLONEID downsampled regimes."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .run_io import write_json, write_markdown


OBSERVABILITY_DIMENSIONS = (
    "event_linked_history",
    "parent_child_event_graph",
    "seed_harvest_transfer_classification",
    "continuous_density_history",
    "image_derived_phenotype",
    "confluence_proxy",
    "endpoint_perspective_support",
    "molecular_assay_event_linkage",
    "exact_time_series_points",
    "raw_image_or_segmentation_provenance",
    "agent_ready_schedule",
    "physiCell_mapping_possible",
    "auditability_grade",
    "identifiability_grade",
)

REGIMES = (
    "NSR_publication_level_reconstructed_record",
    "CLONEID_full_native_record",
    "CLONEID_publication_level_downsampled_record",
)


def _grade(row: dict[str, Any]) -> tuple[str, str]:
    positive_values = {"available", "structured_numeric_table", "event_linked", "agent_ready", "direct"}
    score = sum(1 for key in OBSERVABILITY_DIMENSIONS[:-2] if row.get(key) in positive_values)
    if score >= 10:
        return "A", "strong"
    if score >= 7:
        return "B", "moderate"
    if score >= 4:
        return "C", "limited"
    return "D", "poor"


def build_observability_profile(
    *,
    nsr_record: dict[str, Any],
    history_covariates: dict[str, Any],
    compressed_view: dict[str, Any],
) -> dict[str, Any]:
    history_summary = history_covariates.get("summary", {})
    table_outputs = nsr_record.get("table_outputs", {})
    model_records = nsr_record.get("model_records", {})
    nsr_has_table5 = "supplementary_table_5_growth_rate_samples.csv" in table_outputs
    nsr_has_fig_records = bool(model_records.get("growth_model_fit_statistics") or model_records.get("carrying_capacity_logistic_formulas"))

    rows = [
        {
            "dataset_regime": "NSR_publication_level_reconstructed_record",
            "event_linked_history": "not_event_linked",
            "parent_child_event_graph": "not_available_in_archive",
            "seed_harvest_transfer_classification": "not_event_linked",
            "continuous_density_history": "not_agent_ready_without_manual_reconstruction",
            "image_derived_phenotype": "embedded_plot_or_representative_image",
            "confluence_proxy": "not_agent_ready_without_manual_reconstruction",
            "endpoint_perspective_support": "structured_numeric_table" if nsr_has_table5 else "method_text_only",
            "molecular_assay_event_linkage": "not_event_linked",
            "exact_time_series_points": "embedded_plot_or_representative_image" if nsr_has_fig_records else "not_available_in_archive",
            "raw_image_or_segmentation_provenance": "not_available_in_archive",
            "agent_ready_schedule": "not_agent_ready_without_manual_reconstruction",
            "physiCell_mapping_possible": "not_agent_ready_without_manual_reconstruction",
            "missing_data_warnings": "no native event ledger; plot-only mixed trajectories require deterministic digitization",
            "unsupported_assumptions": "do not infer event-level density history from captions or embedded plots",
            "low_cost_fields_that_would_rescue_identifiability": "event ledger; seed/harvest counts; transfer ratios; event-linked confluence; image provenance",
        },
        {
            "dataset_regime": "CLONEID_full_native_record",
            "event_linked_history": "available",
            "parent_child_event_graph": "available",
            "seed_harvest_transfer_classification": "available",
            "continuous_density_history": "available"
            if history_summary.get("has_cumulative_density_history_proxy")
            else "not_available_in_archive",
            "image_derived_phenotype": "structured_numeric_table",
            "confluence_proxy": "structured_numeric_table",
            "endpoint_perspective_support": "available",
            "molecular_assay_event_linkage": "available",
            "exact_time_series_points": "available",
            "raw_image_or_segmentation_provenance": "available",
            "agent_ready_schedule": "agent_ready",
            "physiCell_mapping_possible": "available",
            "missing_data_warnings": "mock mode uses deterministic schema fixture values",
            "unsupported_assumptions": "manuscript numerical interpretation requires live or frozen CLONEID SNU-668 data",
            "low_cost_fields_that_would_rescue_identifiability": "",
        },
        {
            "dataset_regime": "CLONEID_publication_level_downsampled_record",
            "event_linked_history": "not_event_linked",
            "parent_child_event_graph": "not_available_in_archive",
            "seed_harvest_transfer_classification": "not_event_linked",
            "continuous_density_history": "not_available_in_archive",
            "image_derived_phenotype": "method_text_only",
            "confluence_proxy": "not_available_in_archive",
            "endpoint_perspective_support": "method_text_only",
            "molecular_assay_event_linkage": "not_event_linked",
            "exact_time_series_points": "method_text_only",
            "raw_image_or_segmentation_provenance": "not_available_in_archive",
            "agent_ready_schedule": "not_agent_ready_without_manual_reconstruction",
            "physiCell_mapping_possible": "not_agent_ready_without_manual_reconstruction",
            "missing_data_warnings": "; ".join(compressed_view.get("removed_or_collapsed_information", [])),
            "unsupported_assumptions": "cannot test continuous density/confluence terms after event graph removal",
            "low_cost_fields_that_would_rescue_identifiability": "retain event IDs; preserve seed/harvest/transfer rows; keep event-linked confluence and Perspective linkage",
        },
    ]
    for row in rows:
        row["auditability_grade"], row["identifiability_grade"] = _grade(row)
    return {
        "observability_schema_version": "cloneid_lte_observability_profile_v2",
        "regimes_compared": list(REGIMES),
        "dimensions": list(OBSERVABILITY_DIMENSIONS),
        "observability_matrix": rows,
        "interpretation": "CLONEID full native history preserves the low-cost fields needed to audit density-history models; publication-level records support reconstruction but lose agent-ready linkage.",
    }


def render_observability_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Observability Profile", "", payload["interpretation"], ""]
    for row in payload["observability_matrix"]:
        lines.append(f"## {row['dataset_regime']}")
        lines.append(f"- Auditability grade: `{row['auditability_grade']}`")
        lines.append(f"- Identifiability grade: `{row['identifiability_grade']}`")
        lines.append(f"- Missing data warnings: {row['missing_data_warnings'] or 'none'}")
        lines.append(f"- Low-cost rescue fields: {row['low_cost_fields_that_would_rescue_identifiability'] or 'none'}")
        lines.append("")
    return "\n".join(lines)


def write_observability_profile(output_dir: str | Path, payload: dict[str, Any]) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    rows = payload["observability_matrix"]
    csv_path = output / "observability_profile.csv"
    fieldnames = ["dataset_regime", *OBSERVABILITY_DIMENSIONS, "missing_data_warnings", "unsupported_assumptions", "low_cost_fields_that_would_rescue_identifiability"]
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return {
        "json": write_json(output / "observability_profile.json", payload),
        "csv": csv_path,
        "md": write_markdown(output / "observability_profile.md", render_observability_markdown(payload)),
    }
