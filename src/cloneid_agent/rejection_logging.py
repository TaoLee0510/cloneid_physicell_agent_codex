"""Render explicit rejection logging for model-family comparisons."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .run_io import write_markdown


def render_rejection_report(family_comparison: dict[str, Any]) -> str:
    lines = [
        "# Rejection Report",
        "",
        "Language in this report is limited to supported, rejected, consistent with, insufficient to distinguish, and partially unresolved.",
        "",
    ]
    for row in family_comparison.get("comparison_rows", []):
        lines.append(f"## {row['dataset_regime']} / {row['family']}")
        if row.get("selected_under_tested_assumptions"):
            lines.append("- Status: supported under tested assumptions.")
        elif row.get("rejection_reason"):
            lines.append(f"- Status: {row['rejection_reason']}")
        else:
            lines.append("- Status: insufficient to distinguish under tested assumptions.")
        lines.append(f"- Auditability grade: `{row.get('auditability_grade')}`")
        lines.append(f"- Identifiability grade: `{row.get('identifiability_grade')}`")
        if row.get("missing_data_warnings"):
            lines.append(f"- Missing data warnings: {row['missing_data_warnings']}")
        if row.get("unsupported_assumptions"):
            lines.append(f"- Unsupported assumptions: {row['unsupported_assumptions']}")
        lines.append("")
    return "\n".join(lines)


def write_rejection_report(output_dir: str | Path, family_comparison: dict[str, Any]) -> None:
    write_markdown(Path(output_dir) / "rejection_report.md", render_rejection_report(family_comparison))
