"""CLONEID-LTE minimum standard artifacts."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .run_io import write_json, write_markdown


BRONZE_FIELDS = [
    "event_id",
    "parent_event_id",
    "event_type",
    "date_time",
    "cell_line",
    "root_id",
    "branch_label",
    "replicate_id",
    "passage_number",
    "selection_regime",
    "media",
    "flask_id",
    "flask_area_cm2",
    "seeded_cell_count",
    "harvested_cell_count",
    "split_ratio_or_bottleneck_ratio",
    "operator_or_batch",
    "notes",
]

SILVER_FIELDS = [
    "event_id",
    "image_uri",
    "field_position",
    "magnification",
    "segmentation_version",
    "cell_count_estimate",
    "areaOccupied_um2",
    "cellSize_um2",
    "confluence_proxy",
    "image_QC_flag",
]

GOLD_FIELDS = [
    "assay_event_id",
    "upstream_event_id",
    "pre_assay_confluence",
    "assay_type",
    "sample_source",
    "Perspective_id",
    "clone_or_state_weights",
    "feature_matrix_pointer",
    "raw_data_pointer",
    "QC_flag",
]

PLATINUM_ARTIFACTS = [
    "event_graph.json",
    "growth_episode_table.csv",
    "spatial_phenotype_table.csv",
    "perspective_endpoint_table.csv",
    "modelability_audit.json",
    "model_selection_report.md",
]


def build_cloneid_lte_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "CLONEID-LTE minimum standard",
        "type": "object",
        "properties": {
            "bronze": {"type": "object", "required": BRONZE_FIELDS},
            "silver": {"type": "object", "required": SILVER_FIELDS},
            "gold": {"type": "object", "required": GOLD_FIELDS},
            "platinum": {
                "type": "object",
                "required": PLATINUM_ARTIFACTS,
                "description": "Agent-ready linked benchmark artifact package.",
            },
        },
        "tiers": {
            "Bronze": BRONZE_FIELDS,
            "Silver": SILVER_FIELDS,
            "Gold": GOLD_FIELDS,
            "Platinum": PLATINUM_ARTIFACTS,
        },
    }


def build_standard_markdown() -> str:
    def section(title: str, fields: list[str]) -> list[str]:
        return [f"## {title}", ""] + [f"- `{field}`" for field in fields] + [""]

    rows = [
        "# CLONEID-LTE Minimum Standard",
        "",
        "CLONEID-LTE is a low-cost standard for making long-term evolution experiments modelable.",
        "It preserves event linkage, phenotype provenance, molecular endpoint support, and agent-ready schedules.",
        "",
    ]
    rows.extend(section("Bronze: Event Lineage", BRONZE_FIELDS))
    rows.extend(section("Silver: Image-Derived Phenotype", SILVER_FIELDS))
    rows.extend(section("Gold: Assay Provenance", GOLD_FIELDS))
    rows.extend(section("Platinum: Agent-Ready Package", PLATINUM_ARTIFACTS))
    rows.extend(
        [
            "## Rules",
            "",
            "- Transfer/passaging events are schedule resets, not biological growth episodes.",
            "- Endpoint Perspective is validation/support only, not fitting.",
            "- Identity is secondary inferred support only.",
            "",
        ]
    )
    return "\n".join(rows)


def build_metadata_checklist_markdown() -> str:
    rows = [
        "# Long-Term Evolution Minimal Metadata Checklist",
        "",
        "Use this checklist before publishing or archiving a long-term evolution experiment.",
        "",
        "- Bronze fields are complete for every seed, harvest, and transfer event.",
        "- Parent-child event links are valid and acyclic.",
        "- Transfer/bottleneck events are explicitly labeled.",
        "- Image-derived counts, occupied area, cell size, and confluence proxy are versioned.",
        "- Endpoint assays point back to upstream culture events.",
        "- Modelability audit labels use the controlled record-status vocabulary.",
        "- Reports state which model families are identifiable under available records.",
        "",
    ]
    return "\n".join(rows)


def write_event_template_csv(path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(dict.fromkeys(BRONZE_FIELDS + SILVER_FIELDS + GOLD_FIELDS))
    with target.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
    return target


def write_cloneid_lte_standard(output_dir: str | Path) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "standard_md": write_markdown(output / "CLONEID_LTE_minimum_standard.md", build_standard_markdown()),
        "schema_json": write_json(output / "CLONEID_LTE_schema.json", build_cloneid_lte_schema()),
        "event_template_csv": write_event_template_csv(output / "long_term_evolution_event_template.csv"),
        "metadata_checklist_md": write_markdown(
            output / "long_term_evolution_minimal_metadata_checklist.md",
            build_metadata_checklist_markdown(),
        ),
    }
    return paths
