"""Publication-level NSR r/K record reconstruction."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
import re
from statistics import mean, pstdev
from typing import Any

from .external_comparators.nwaa124 import (
    extract_all_docx_payloads,
    inventory_external_archive,
)
from .run_io import write_json, write_markdown


RELEVANT_MODEL_FIGURES = {1, 4, 5, 6, 9, 10, 11, 12, 13, 14, 15}
GROWTH_TABLE_COLUMNS = ("Samples", "IN_G", "IN_R", "G3K", "R1K", "G3r", "R1r")


def _clean_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _find_figures_docx(docx_payloads: list[dict[str, Any]]) -> dict[str, Any]:
    for payload in docx_payloads:
        if "Figures and Tables" in payload["docx_name"]:
            return payload
    for payload in docx_payloads:
        if any(text.startswith("Supplementary Figure 1") for text in payload["paragraphs"]):
            return payload
    raise ValueError("Could not find the Supplementary Figures and Tables docx payload")


def _find_methods_docx(docx_payloads: list[dict[str, Any]]) -> dict[str, Any] | None:
    for payload in docx_payloads:
        if "Materials and Methods" in payload["docx_name"] or "Materials" in payload["docx_name"]:
            return payload
    return None


def build_supplement_figure_index(paragraphs: list[str]) -> list[dict[str, Any]]:
    """Index figure titles and captions from supplementary docx paragraphs."""

    figures: list[dict[str, Any]] = []
    title_pattern = re.compile(r"^Supplementary Figure\s+(\d+)\s*\|\s*(.+)$")
    stop_pattern = re.compile(r"^Supplementary (Figure|Table)\s+\d+")
    index = 0
    while index < len(paragraphs):
        match = title_pattern.match(paragraphs[index])
        if not match:
            index += 1
            continue
        number = int(match.group(1))
        title = _clean_space(match.group(2))
        caption_parts: list[str] = []
        cursor = index + 1
        while cursor < len(paragraphs) and not stop_pattern.match(paragraphs[cursor]):
            caption_parts.append(paragraphs[cursor])
            cursor += 1
        caption = _clean_space(" ".join(caption_parts))
        status = "embedded_plot_or_representative_image"
        if number in {9, 10}:
            status = "model_formula_in_caption_or_methods"
        figures.append(
            {
                "figure_number": number,
                "label": f"Supplementary Figure {number}",
                "title": title,
                "caption": caption,
                "relevant_to_model_reconstruction": number in RELEVANT_MODEL_FIGURES,
                "record_status": status,
            }
        )
        index = cursor
    return figures


def parse_figure_9_growth_model_records(caption: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    normalized = _clean_space(caption).replace("R- Squared", "R-Squared")
    for family in ("Exponential", "Gompertz", "Logistic"):
        pattern = re.compile(
            rf"{family}\s*\(R-\s*Squared number\s*([0-9.]+);\s*p=([0-9.eE+-]+)\)",
            re.IGNORECASE,
        )
        match = pattern.search(normalized)
        if match:
            records.append(
                {
                    "source": "Supplementary Figure 9",
                    "model_family": family.lower(),
                    "reported_r_squared": float(match.group(1)),
                    "reported_p_value": match.group(2),
                    "record_status": "model_formula_in_caption_or_methods",
                    "interpretation": "published growth-model fit statistic from caption",
                }
            )
    return records


def parse_figure_10_logistic_records(caption: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    normalized = _clean_space(caption)
    pattern = re.compile(
        r"([0-9]+(?:\.[0-9]+)?)\s*/\s*\(1\+([0-9]+(?:\.[0-9]+)?)\s*exp\(-([0-9]+(?:\.[0-9]+)?)\s*x\)\)"
    )
    matches = pattern.findall(normalized)
    for label, values in zip(("r", "K"), matches):
        carrying_capacity, denominator_scale, rate = values
        records.append(
            {
                "source": "Supplementary Figure 10",
                "population": label,
                "formula": f"{carrying_capacity}/(1+{denominator_scale} exp(-{rate} x))",
                "carrying_capacity": float(carrying_capacity),
                "denominator_scale": float(denominator_scale),
                "growth_rate_parameter": float(rate),
                "record_status": "model_formula_in_caption_or_methods",
            }
        )
    return records


def parse_methods_model_records(methods_payload: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not methods_payload:
        return []
    text = _clean_space(" ".join(methods_payload["paragraphs"]))
    records: list[dict[str, Any]] = []
    alpha_beta = re.search(r"\(,\s*\)\s*=\s*\(([0-9.]+),\s*([0-9.]+)\)", text)
    if alpha_beta:
        records.append(
            {
                "source": "Supplementary data- Materials and Methods",
                "model_component": "Lotka-Volterra interaction grid-search",
                "alpha": float(alpha_beta.group(1)),
                "beta": float(alpha_beta.group(2)),
                "record_status": "model_formula_in_caption_or_methods",
                "note": "OpenXML text extraction loses the original Greek symbols, but preserves the reported numeric pair.",
            }
        )
    if "two-dimensional" in text and "grid" in text and "migration" in text:
        records.append(
            {
                "source": "Supplementary data- Materials and Methods",
                "model_component": "spatial computational model",
                "features": ["2D grid", "migration", "division", "density-dependent space"],
                "record_status": "method_text_only",
                "raw_spatial_data_status": "not_available_in_archive",
            }
        )
    return records


def _first_nonempty_row(rows: list[list[str]]) -> list[str]:
    for row in rows:
        if any(cell.strip() for cell in row):
            return [cell.strip() for cell in row]
    return []


def _table_target_filename(rows: list[list[str]]) -> str | None:
    header = _first_nonempty_row(rows)
    header_set = {cell.strip() for cell in header}
    if "Comparisons" in header_set and "Total DEGs number" in header_set:
        return "supplementary_table_1_deg_counts.csv"
    if "KEGG Pathway" in header_set and "P-Value" in header_set:
        return "supplementary_table_2_kegg_low_density.csv"
    if "Term" in header_set and "Fold Enrichment" in header_set:
        return "supplementary_table_3_kegg_crowded.csv"
    if set(GROWTH_TABLE_COLUMNS).issubset(header_set):
        return "supplementary_table_5_growth_rate_samples.csv"
    normalized = {cell.lower() for cell in header}
    if "pathway" in normalized and ("abbravation" in normalized or "abbreviation" in normalized):
        return "supplementary_table_6_kegg_abbreviations.csv"
    return None


def _trim_empty_leading_rows(rows: list[list[str]]) -> list[list[str]]:
    trimmed = list(rows)
    while trimmed and not any(cell.strip() for cell in trimmed[0]):
        trimmed.pop(0)
    return trimmed


def write_extracted_tables(figures_payload: dict[str, Any], output_dir: str | Path) -> dict[str, Any]:
    table_dir = Path(output_dir)
    table_dir.mkdir(parents=True, exist_ok=True)
    extracted: dict[str, Any] = {}
    for table in figures_payload["tables"]:
        rows = _trim_empty_leading_rows(table["rows"])
        target = _table_target_filename(rows)
        if not target:
            continue
        path = table_dir / target
        with path.open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerows(rows)
        extracted[target] = {
            "path": str(path),
            "table_index": table["table_index"],
            "row_count": len(rows),
            "column_count": max((len(row) for row in rows), default=0),
            "record_status": "structured_numeric_table",
        }
    return extracted


def read_growth_table(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open(newline="") as handle:
        return list(csv.DictReader(handle))


def build_reconstructed_growth_inputs(growth_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    branch_map = {
        "IN_G": "IN",
        "IN_R": "IN",
        "G3K": "K",
        "R1K": "K",
        "G3r": "r",
        "R1r": "r",
    }
    for row in growth_rows:
        sample = row.get("Samples", "")
        for column, branch in branch_map.items():
            value = row.get(column, "")
            try:
                growth_rate = float(value)
            except (TypeError, ValueError):
                continue
            records.append(
                {
                    "source": "Supplementary Table 5",
                    "sample": sample,
                    "source_column": column,
                    "branch_label": branch,
                    "growth_rate_sample": growth_rate,
                    "record_status": "structured_numeric_table",
                    "event_linkage_status": "not_event_linked",
                }
            )
    return records


def summarize_growth_inputs(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[float]] = {}
    for record in records:
        grouped.setdefault(record["branch_label"], []).append(float(record["growth_rate_sample"]))
    summaries: list[dict[str, Any]] = []
    for branch, values in sorted(grouped.items()):
        summaries.append(
            {
                "branch_label": branch,
                "n": len(values),
                "mean_growth_rate": mean(values),
                "sd_growth_rate": pstdev(values) if len(values) > 1 else 0.0,
                "min_growth_rate": min(values),
                "max_growth_rate": max(values),
                "record_status": "structured_numeric_table",
            }
        )
    return summaries


def write_reconstructed_growth_inputs(records: list[dict[str, Any]], path: str | Path) -> Path:
    fieldnames = [
        "source",
        "sample",
        "source_column",
        "branch_label",
        "growth_rate_sample",
        "record_status",
        "event_linkage_status",
    ]
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(records)
    return target


def build_reconstructed_competition_inputs(figure_index: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for number in (1, 4, 5, 11, 12):
        figure = next((item for item in figure_index if item["figure_number"] == number), None)
        if not figure:
            continue
        rows.append(
            {
                "source": figure["label"],
                "model_component": "mixed_population_fraction_trajectory",
                "evidence_role": "publication-level caption and embedded plot evidence",
                "record_status": "embedded_plot_or_representative_image",
                "fit_status": "embedded_plot_digitization_required",
                "overclaim_guardrail": "not treated as raw numeric trajectory without deterministic digitization",
            }
        )
    return rows


def write_reconstructed_competition_inputs(rows: list[dict[str, Any]], path: str | Path) -> Path:
    fieldnames = [
        "source",
        "model_component",
        "evidence_role",
        "record_status",
        "fit_status",
        "overclaim_guardrail",
    ]
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return target


def build_model_records(
    figure_index: list[dict[str, Any]],
    methods_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    figure_by_number = {figure["figure_number"]: figure for figure in figure_index}
    records: dict[str, Any] = {
        "growth_model_fit_statistics": parse_figure_9_growth_model_records(
            figure_by_number.get(9, {}).get("caption", "")
        ),
        "carrying_capacity_logistic_formulas": parse_figure_10_logistic_records(
            figure_by_number.get(10, {}).get("caption", "")
        ),
        "methods_model_records": parse_methods_model_records(methods_payload),
        "plot_only_limitations": [
            {
                "source": f"Supplementary Figure {number}",
                "status": "embedded_plot_digitization_required",
                "record_status": "embedded_plot_or_representative_image",
            }
            for number in (1, 4, 5, 11, 12)
            if number in figure_by_number
        ],
    }
    logistic = records["carrying_capacity_logistic_formulas"]
    if logistic:
        records["carrying_capacity_summary"] = {
            item["population"]: item["carrying_capacity"] for item in logistic
        }
    return records


def _write_csv_dicts(path: str | Path, rows: list[dict[str, Any]]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        target.write_text("")
        return target
    fieldnames = list(rows[0].keys())
    with target.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return target


def build_publication_level_markdown(
    *,
    inventory: dict[str, Any],
    figure_index: list[dict[str, Any]],
    table_outputs: dict[str, Any],
    model_records: dict[str, Any],
    growth_summary: list[dict[str, Any]],
) -> str:
    figure_labels = ", ".join(
        f"Supplementary Fig. {item['figure_number']}" for item in figure_index if item["relevant_to_model_reconstruction"]
    )
    table_names = ", ".join(sorted(table_outputs))
    growth_lines = [
        f"- `{row['branch_label']}`: n={row['n']}, mean={row['mean_growth_rate']:.4g}, sd={row['sd_growth_rate']:.4g}"
        for row in growth_summary
    ]
    fig9 = model_records.get("growth_model_fit_statistics", [])
    fig9_lines = [
        f"- `{row['model_family']}` R-squared={row['reported_r_squared']:.3f}, p={row['reported_p_value']}"
        for row in fig9
    ]
    return "\n".join(
        [
            "# NSR Publication-Level r/K Record",
            "",
            "Li et al. NSR 2021 is used as a strong biological comparator with publication-level experimental records.",
            "The supplement supports coarse model reconstruction, but record linkage must be reconstructed manually from captions, tables, and methods text.",
            "",
            "## Archive",
            "",
            f"- Files detected: `{inventory['file_count']}`",
            f"- Source type: `{inventory['source_type']}`",
            "",
            "## Model-Relevant Items",
            "",
            f"- Figure captions indexed: {figure_labels}",
            f"- Extracted structured tables: {table_names}",
            "",
            "## Growth-Rate Samples",
            "",
            *growth_lines,
            "",
            "## Published Growth-Model Fit Evidence",
            "",
            *fig9_lines,
            "",
            "## Guardrails",
            "",
            "- Embedded plots and representative images are not treated as raw numeric data.",
            "- Mixed-population curves are marked as requiring deterministic digitization before curve fitting.",
            "- The record is not event-linked and is not agent-ready without manual reconstruction.",
            "",
        ]
    )


def extract_nwaa124_publication_record(
    external_zip_or_dir: str | Path | None,
    output_dir: str | Path,
) -> dict[str, Any]:
    """Extract NSR comparator artifacts into the benchmark output directory."""

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    table_dir = output / "nwaa124_extracted_tables"

    inventory = inventory_external_archive(external_zip_or_dir)
    docx_payloads = extract_all_docx_payloads(external_zip_or_dir, output)
    figures_payload = _find_figures_docx(docx_payloads)
    methods_payload = _find_methods_docx(docx_payloads)

    figure_index = build_supplement_figure_index(figures_payload["paragraphs"])
    table_outputs = write_extracted_tables(figures_payload, table_dir)
    table5_path = table_outputs.get("supplementary_table_5_growth_rate_samples.csv", {}).get("path")
    growth_rows = read_growth_table(table5_path) if table5_path else []
    growth_inputs = build_reconstructed_growth_inputs(growth_rows)
    growth_summary = summarize_growth_inputs(growth_inputs)
    competition_inputs = build_reconstructed_competition_inputs(figure_index)
    model_records = build_model_records(figure_index, methods_payload)

    extraction_report = {
        "docx_extraction_engine": figures_payload["extraction_engine"],
        "docx_payloads": [
            {
                "docx_name": payload["docx_name"],
                "paragraph_count": payload["paragraph_count"],
                "table_count": payload["table_count"],
                "embedded_media_count": payload["embedded_media_count"],
                "extraction_engine": payload["extraction_engine"],
                "embedded_media": payload["embedded_media"],
            }
            for payload in docx_payloads
        ],
        "table_outputs": table_outputs,
        "overclaim_guardrails": [
            "Embedded plots are publication-level evidence, not raw numeric trajectory tables.",
            "Supplementary Table 5 is handled as structured numeric growth-rate samples.",
            "Supplementary Figure 13 is a spatial model schematic/method record, not raw spatial data.",
        ],
    }

    write_json(output / "nwaa124_archive_inventory.json", inventory)
    write_json(output / "nwaa124_docx_extraction_report.json", extraction_report)
    write_json(output / "nwaa124_supplement_figure_index.json", figure_index)
    write_json(output / "nwaa124_extracted_model_records.json", model_records)
    write_reconstructed_growth_inputs(growth_inputs, output / "nwaa124_reconstructed_growth_inputs.csv")
    _write_csv_dicts(output / "nwaa124_reconstructed_growth_summary.csv", growth_summary)
    write_reconstructed_competition_inputs(competition_inputs, output / "nwaa124_reconstructed_competition_inputs.csv")
    write_markdown(
        output / "nwaa124_publication_level_record.md",
        build_publication_level_markdown(
            inventory=inventory,
            figure_index=figure_index,
            table_outputs=table_outputs,
            model_records=model_records,
            growth_summary=growth_summary,
        ),
    )

    return {
        "inventory": inventory,
        "docx_extraction_report": extraction_report,
        "figure_index": figure_index,
        "table_outputs": table_outputs,
        "model_records": model_records,
        "growth_inputs": growth_inputs,
        "growth_summary": growth_summary,
        "competition_inputs": competition_inputs,
    }
