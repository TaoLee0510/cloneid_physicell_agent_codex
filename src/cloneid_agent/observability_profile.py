"""Observability and missingness profiles across comparison regimes."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .run_io import write_json, write_markdown


OBSERVABILITY_FIELDS = (
    "dataset_regime",
    "event_linked_history",
    "longitudinal_phenotype",
    "continuous_density_history",
    "transfer_semantics",
    "endpoint_perspective_support",
    "identity_inferred_support",
    "exact_time_series_points",
    "missing_data_warnings",
    "unsupported_assumptions",
    "auditability_grade",
    "identifiability_grade",
)


def _grade_profile(
    *,
    event_linked_history: bool,
    longitudinal_phenotype: bool,
    continuous_density_history: bool,
    transfer_semantics: bool,
    endpoint_perspective_support: bool,
    exact_time_series_points: bool,
) -> tuple[str, str]:
    score = sum(
        [
            event_linked_history,
            longitudinal_phenotype,
            continuous_density_history,
            transfer_semantics,
            endpoint_perspective_support,
            exact_time_series_points,
        ]
    )
    if score >= 5:
        return "A", "strong"
    if score >= 3:
        return "B", "moderate"
    if score >= 2:
        return "C", "limited"
    return "D", "poor"


def _row(
    *,
    dataset_regime: str,
    event_linked_history: bool,
    longitudinal_phenotype: bool,
    continuous_density_history: bool,
    transfer_semantics: bool,
    endpoint_perspective_support: bool,
    identity_inferred_support: bool,
    exact_time_series_points: bool,
    missing_data_warnings: list[str],
    unsupported_assumptions: list[str],
) -> dict[str, Any]:
    auditability_grade, identifiability_grade = _grade_profile(
        event_linked_history=event_linked_history,
        longitudinal_phenotype=longitudinal_phenotype,
        continuous_density_history=continuous_density_history,
        transfer_semantics=transfer_semantics,
        endpoint_perspective_support=endpoint_perspective_support,
        exact_time_series_points=exact_time_series_points,
    )
    return {
        "dataset_regime": dataset_regime,
        "event_linked_history": event_linked_history,
        "longitudinal_phenotype": longitudinal_phenotype,
        "continuous_density_history": continuous_density_history,
        "transfer_semantics": transfer_semantics,
        "endpoint_perspective_support": endpoint_perspective_support,
        "identity_inferred_support": identity_inferred_support,
        "exact_time_series_points": exact_time_series_points,
        "missing_data_warnings": "; ".join(missing_data_warnings),
        "unsupported_assumptions": "; ".join(unsupported_assumptions),
        "auditability_grade": auditability_grade,
        "identifiability_grade": identifiability_grade,
    }


def build_observability_profile(
    *,
    history_covariates: dict[str, Any],
    compressed_view: dict[str, Any],
    external_comparator: dict[str, Any],
) -> dict[str, Any]:
    history_summary = history_covariates.get("summary", {})
    compressed_flags = compressed_view.get("observability_flags", {})
    external_flags = external_comparator.get("observability_flags", {})
    rows = [
        _row(
            dataset_regime="snu668_full_history",
            event_linked_history=bool(history_summary.get("has_continuous_event_order_context")),
            longitudinal_phenotype=bool(history_summary.get("events_with_correctedCount") or history_summary.get("events_with_areaOccupied_um2")),
            continuous_density_history=bool(history_summary.get("has_cumulative_crowding_history_proxy")),
            transfer_semantics=bool(history_summary.get("transfer_reset_count")),
            endpoint_perspective_support=True,
            identity_inferred_support=True,
            exact_time_series_points=True,
            missing_data_warnings=[] if history_covariates.get("data_status", "").startswith("mock") is False else ["dry-run fixture; replace with live CLONEID bundle before biological interpretation"],
            unsupported_assumptions=[],
        ),
        _row(
            dataset_regime="snu668_published_like_compressed",
            event_linked_history=False,
            longitudinal_phenotype=True,
            continuous_density_history=False,
            transfer_semantics=False,
            endpoint_perspective_support=bool(compressed_flags.get("endpoint_support_present")),
            identity_inferred_support=False,
            exact_time_series_points=False,
            missing_data_warnings=list(compressed_view.get("removed_or_collapsed_information", [])),
            unsupported_assumptions=["cannot assume continuous crowding exposure from baseline and terminal summaries"],
        ),
        _row(
            dataset_regime="nwaa124_curated_external",
            event_linked_history=bool(external_flags.get("event_linked_history")),
            longitudinal_phenotype=bool(external_flags.get("competition_summaries_present")),
            continuous_density_history=False,
            transfer_semantics=False,
            endpoint_perspective_support=bool(external_flags.get("phenotype_support_present")),
            identity_inferred_support=False,
            exact_time_series_points=bool(external_flags.get("exact_time_series_points_present")),
            missing_data_warnings=list(external_comparator.get("missingness", {}).get("dataset_level_missingness", [])),
            unsupported_assumptions=list(external_comparator.get("unsupported_assumptions", [])),
        ),
    ]
    return {
        "observability_schema_version": "observability_profile_v1",
        "observability_matrix": rows,
        "regimes_compared": [row["dataset_regime"] for row in rows],
    }


def render_dataset_missingness_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Dataset Missingness", ""]
    for row in payload["observability_matrix"]:
        lines.append(f"## {row['dataset_regime']}")
        lines.append(f"- Auditability grade: `{row['auditability_grade']}`")
        lines.append(f"- Identifiability grade: `{row['identifiability_grade']}`")
        warnings = row["missing_data_warnings"] or "none recorded"
        lines.append(f"- Missing data warnings: {warnings}")
        unsupported = row["unsupported_assumptions"] or "none recorded"
        lines.append(f"- Unsupported assumptions: {unsupported}")
        lines.append("")
    return "\n".join(lines)


def write_observability_profile(output_dir: str | Path, payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    rows = payload["observability_matrix"]
    write_json(output_dir / "observability_matrix.json", payload)
    with (output_dir / "observability_matrix.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(OBSERVABILITY_FIELDS))
        writer.writeheader()
        writer.writerows(rows)
    write_markdown(output_dir / "dataset_missingness.md", render_dataset_missingness_markdown(payload))
