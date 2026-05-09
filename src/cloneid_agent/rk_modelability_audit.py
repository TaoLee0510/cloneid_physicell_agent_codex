"""Modelability audit tables for the CLONEID-LTE r/K benchmark."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .external_comparators.nwaa124 import RECORD_STATUS_LABELS


AUDIT_DIMENSIONS = (
    "branch_label",
    "selection_protocol",
    "replicate_identity",
    "per_event_passaging",
    "parent_child_event_graph",
    "seed_harvest_transfer_classification",
    "growth_rate_distribution",
    "carrying_capacity_estimates",
    "competition_fraction_trajectory",
    "raw_images",
    "representative_images",
    "segmentation_features",
    "confluence_proxy",
    "migration_or_adhesion_phenotype",
    "molecular_assay",
    "molecular_assay_event_linkage",
    "agent_ready_schedule",
    "physicell_mapping",
    "overclaim_auditability",
)


def _validate_status(status: str) -> str:
    if status not in RECORD_STATUS_LABELS:
        raise ValueError(f"Unsupported record status label: {status}")
    return status


def build_modelability_audit_rows() -> list[dict[str, Any]]:
    """Compare NSR publication-level, CLONEID full, and downsampled records."""

    status_by_dimension = {
        "branch_label": (
            "method_text_only",
            "structured_numeric_table",
            "method_text_only",
        ),
        "selection_protocol": (
            "method_text_only",
            "structured_numeric_table",
            "method_text_only",
        ),
        "replicate_identity": (
            "structured_numeric_table",
            "structured_numeric_table",
            "structured_numeric_table",
        ),
        "per_event_passaging": (
            "not_event_linked",
            "structured_numeric_table",
            "not_event_linked",
        ),
        "parent_child_event_graph": (
            "not_available_in_archive",
            "structured_numeric_table",
            "not_available_in_archive",
        ),
        "seed_harvest_transfer_classification": (
            "not_event_linked",
            "structured_numeric_table",
            "not_event_linked",
        ),
        "growth_rate_distribution": (
            "structured_numeric_table",
            "structured_numeric_table",
            "structured_numeric_table",
        ),
        "carrying_capacity_estimates": (
            "model_formula_in_caption_or_methods",
            "structured_numeric_table",
            "not_agent_ready_without_manual_reconstruction",
        ),
        "competition_fraction_trajectory": (
            "embedded_plot_or_representative_image",
            "structured_numeric_table",
            "not_agent_ready_without_manual_reconstruction",
        ),
        "raw_images": (
            "not_available_in_archive",
            "structured_numeric_table",
            "not_available_in_archive",
        ),
        "representative_images": (
            "embedded_plot_or_representative_image",
            "structured_numeric_table",
            "embedded_plot_or_representative_image",
        ),
        "segmentation_features": (
            "not_available_in_archive",
            "structured_numeric_table",
            "not_available_in_archive",
        ),
        "confluence_proxy": (
            "not_agent_ready_without_manual_reconstruction",
            "structured_numeric_table",
            "not_available_in_archive",
        ),
        "migration_or_adhesion_phenotype": (
            "embedded_plot_or_representative_image",
            "structured_numeric_table",
            "method_text_only",
        ),
        "molecular_assay": (
            "structured_numeric_table",
            "structured_numeric_table",
            "method_text_only",
        ),
        "molecular_assay_event_linkage": (
            "not_event_linked",
            "structured_numeric_table",
            "not_event_linked",
        ),
        "agent_ready_schedule": (
            "not_agent_ready_without_manual_reconstruction",
            "structured_numeric_table",
            "not_agent_ready_without_manual_reconstruction",
        ),
        "physicell_mapping": (
            "not_agent_ready_without_manual_reconstruction",
            "structured_numeric_table",
            "not_agent_ready_without_manual_reconstruction",
        ),
        "overclaim_auditability": (
            "method_text_only",
            "structured_numeric_table",
            "method_text_only",
        ),
    }
    rows: list[dict[str, Any]] = []
    for dimension in AUDIT_DIMENSIONS:
        nsr, full, coarse = status_by_dimension[dimension]
        rows.append(
            {
                "dimension": dimension,
                "NSR_publication_level_reconstructed_record": _validate_status(nsr),
                "CLONEID_full_native_record": _validate_status(full),
                "CLONEID_publication_level_downsampled_record": _validate_status(coarse),
                "audit_note": _audit_note_for_dimension(dimension),
            }
        )
    return rows


def _audit_note_for_dimension(dimension: str) -> str:
    notes = {
        "per_event_passaging": "Transfer/passaging events must be separated from biological growth episodes.",
        "competition_fraction_trajectory": "NSR plot curves require deterministic digitization before trajectory fitting.",
        "confluence_proxy": "Event-level confluence is the key discriminator for density-dependent model identifiability.",
        "molecular_assay_event_linkage": "Endpoint Perspective is validation/support only and is not used for growth fitting.",
        "overclaim_auditability": "The benchmark asks which model families are identifiable under available records.",
    }
    return notes.get(dimension, "Record-status label uses the benchmark controlled vocabulary.")


def write_modelability_audit_csv(path: str | Path, rows: list[dict[str, Any]] | None = None) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = rows or build_modelability_audit_rows()
    fieldnames = [
        "dimension",
        "NSR_publication_level_reconstructed_record",
        "CLONEID_full_native_record",
        "CLONEID_publication_level_downsampled_record",
        "audit_note",
    ]
    with target.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(payload)
    return target
