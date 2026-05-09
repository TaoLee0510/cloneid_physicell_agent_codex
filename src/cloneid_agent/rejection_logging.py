"""Rejection and unresolved-status reporting for model-family comparisons."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .run_io import write_markdown


def render_rejection_report(family_comparison: dict[str, Any]) -> str:
    lines = [
        "# Rejection Report",
        "",
        "This report uses only bounded language: supports, rejected under tested assumptions, unresolved under available records, and not identifiable from coarse records.",
        "",
    ]
    for row in family_comparison.get("comparison_rows", []):
        lines.append(f"## {row['dataset_regime']} / {row['family_id']}")
        if row.get("selected_under_tested_assumptions"):
            lines.append("- Status: supports under tested assumptions.")
        elif row.get("rejected_under_tested_assumptions"):
            lines.append("- Status: rejected under tested assumptions.")
        elif row.get("unresolved_under_available_records"):
            lines.append("- Status: unresolved under available records.")
        else:
            lines.append(f"- Status: `{row.get('fit_status')}`.")
        if row.get("reason_if_not_identifiable"):
            lines.append(f"- Reason: {row['reason_if_not_identifiable']}")
        lines.append(f"- Required inputs available: {row.get('required_inputs_available') or 'none'}")
        lines.append(f"- Required inputs missing: {row.get('required_inputs_missing') or 'none'}")
        lines.append(f"- Auditability grade: `{row.get('auditability_grade')}`")
        lines.append(f"- Identifiability grade: `{row.get('identifiability_grade')}`")
        lines.append(f"- Guardrail: {row.get('overclaim_guardrail')}")
        lines.append("")
    return "\n".join(lines)


def write_rejection_report(output_dir: str | Path, family_comparison: dict[str, Any]) -> Path:
    return write_markdown(Path(output_dir) / "rejection_report.md", render_rejection_report(family_comparison))
