"""History-ablation contracts for density-history model comparisons."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .run_io import write_json, write_markdown


def build_history_ablation(
    history_covariates: dict[str, Any],
    compressed_view: dict[str, Any],
) -> dict[str, Any]:
    summary = history_covariates.get("summary", {})
    full_history_inputs = [
        "event_order_index",
        "parent_event_id",
        "duration_hours_since_parent",
        "density_proxy_relative_area",
        "cumulative_area_history_proxy_before_event",
        "transfer_reset_semantics",
        "terminal Perspective support as endpoint validation only",
    ]
    historyless_inputs = [
        "coarse_passage",
        "baseline_summary",
        "terminal_summary",
        "terminal Perspective support count",
    ]
    full_score = 0
    full_score += 2 if summary.get("has_continuous_event_order_context") else 0
    full_score += 2 if summary.get("has_cumulative_crowding_history_proxy") else 0
    full_score += 1 if summary.get("transfer_reset_count", 0) else 0
    compressed_score = 1 if compressed_view.get("terminal_perspective_summary", {}).get("perspective_record_count", 0) else 0
    delta = full_score - compressed_score
    return {
        "ablation_schema_version": "history_ablation_v1",
        "paired_conditions": [
            {
                "condition_id": "full_history",
                "dataset_regime": "snu668_full_history",
                "retained_inputs": full_history_inputs,
                "removed_inputs": [],
                "history_signal_score": full_score,
                "interpretation": "event-linked density and transfer history is available for mechanistic discrimination",
            },
            {
                "condition_id": "historyless_or_passage_only",
                "dataset_regime": "snu668_published_like_compressed",
                "retained_inputs": historyless_inputs,
                "removed_inputs": list(compressed_view.get("removed_or_collapsed_information", [])),
                "history_signal_score": compressed_score,
                "interpretation": "history inputs are collapsed to a sparse publication-like summary",
            },
        ],
        "history_ablation_delta": delta,
        "delta_interpretation": (
            "large event-history loss"
            if delta >= 3
            else "modest event-history loss"
            if delta >= 1
            else "little event-history loss under this schema"
        ),
        "strict_provenance_notes": [
            "Perspective is endpoint or assay-specific support, not longitudinal phenotype.",
            "Identity is inferred secondary support, not directly observed phenotype.",
            "Derived count, areaOccupied, and confluence-like quantities must retain processing provenance.",
        ],
    }


def render_history_ablation_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# History Ablation",
        "",
        f"- History ablation delta: `{payload['history_ablation_delta']}`",
        f"- Interpretation: {payload['delta_interpretation']}",
        "",
        "## Paired conditions",
        "",
    ]
    for condition in payload["paired_conditions"]:
        lines.append(f"### {condition['condition_id']}")
        lines.append(f"- Regime: `{condition['dataset_regime']}`")
        lines.append(f"- History signal score: `{condition['history_signal_score']}`")
        lines.append(f"- Interpretation: {condition['interpretation']}")
        if condition["removed_inputs"]:
            lines.append("- Removed inputs:")
            for item in condition["removed_inputs"]:
                lines.append(f"  - {item}")
    lines.extend(["", "## Provenance notes", ""])
    for item in payload["strict_provenance_notes"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def write_history_ablation(output_dir: str | Path, payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    write_json(output_dir / "history_ablation.json", payload)
    write_markdown(output_dir / "history_ablation.md", render_history_ablation_markdown(payload))
