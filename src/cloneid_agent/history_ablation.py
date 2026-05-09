"""History-ablation summaries for full versus publication-like CLONEID records."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .rk_density_models import MODEL_FAMILIES, NOT_IDENTIFIABLE_DENSITY
from .run_io import write_json, write_markdown


def build_history_ablation(
    history_covariates: dict[str, Any],
    compressed_view: dict[str, Any],
    *,
    cloneid_full_fits: dict[str, Any] | None = None,
    cloneid_coarse_fits: dict[str, Any] | None = None,
) -> dict[str, Any]:
    summary = history_covariates.get("summary", {})
    full_score = 0
    full_score += 2 if summary.get("has_continuous_event_order_context") else 0
    full_score += 2 if summary.get("has_cumulative_density_history_proxy") else 0
    full_score += 2 if summary.get("events_with_confluence_proxy") else 0
    full_score += 1 if summary.get("transfer_reset_count", 0) else 0
    compressed_score = 1 if compressed_view.get("terminal_perspective_summary", {}).get("perspective_record_count") else 0
    delta = full_score - compressed_score

    full_by_family = {
        row["family_id"]: row for row in (cloneid_full_fits or {}).get("models", [])
    }
    coarse_by_family = {
        row["family_id"]: row for row in (cloneid_coarse_fits or {}).get("models", [])
    }
    model_family_effects = []
    for family in MODEL_FAMILIES:
        full_fit = full_by_family.get(family, {})
        coarse_fit = coarse_by_family.get(family, {})
        model_family_effects.append(
            {
                "family_id": family,
                "full_native_fit_status": full_fit.get("fit_status", "not_run"),
                "downsampled_fit_status": coarse_fit.get("fit_status", "not_run"),
                "effect_of_downsampling": _effect_of_downsampling(family, coarse_fit.get("fit_status")),
            }
        )

    return {
        "ablation_schema_version": "cloneid_lte_history_ablation_v2",
        "source_regime": "CLONEID_full_native_record",
        "ablated_regime": "CLONEID_publication_level_downsampled_record",
        "paired_conditions": [
            {
                "condition_id": "full_native_record",
                "dataset_regime": "CLONEID_full_native_record",
                "retained_inputs": [
                    "event_id",
                    "parent_event_id",
                    "seed_event_id",
                    "harvest_event_id",
                    "transfer/bottleneck event semantics",
                    "per-event confluence_proxy",
                    "cumulative_confluence_exposure_before_event",
                    "image-derived phenotype provenance",
                    "terminal Perspective event linkage",
                ],
                "removed_inputs": [],
                "history_signal_score": full_score,
            },
            {
                "condition_id": "publication_level_downsampled_record",
                "dataset_regime": "CLONEID_publication_level_downsampled_record",
                "retained_inputs": compressed_view.get("retained_information", []),
                "removed_inputs": compressed_view.get("removed_or_collapsed_information", []),
                "history_signal_score": compressed_score,
            },
        ],
        "history_ablation_delta": delta,
        "delta_interpretation": (
            "large event-history loss"
            if delta >= 5
            else "moderate event-history loss"
            if delta >= 2
            else "limited event-history loss"
        ),
        "model_family_effects": model_family_effects,
        "strict_provenance_notes": [
            "Endpoint Perspective is validation/support only, not a growth-fitting target.",
            "Identity is inferred secondary support only.",
            "Transfer/passaging events are not growth intervals.",
            "Mock SNU-668 values are schema fixtures; manuscript numerical interpretation requires live or frozen CLONEID data.",
        ],
    }


def _effect_of_downsampling(family_id: str, coarse_status: str | None) -> str:
    if coarse_status == NOT_IDENTIFIABLE_DENSITY:
        return "not identifiable from coarse records because event-level density/history was removed"
    if family_id in {"context_blind_null", "proliferation_only", "branch_specific_fitness"}:
        return "reduced to summary-identifiable coarse growth comparison"
    return "unresolved under available records"


def render_history_ablation_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# History Ablation",
        "",
        f"- Source regime: `{payload['source_regime']}`",
        f"- Ablated regime: `{payload['ablated_regime']}`",
        f"- History ablation delta: `{payload['history_ablation_delta']}`",
        f"- Interpretation: {payload['delta_interpretation']}",
        "",
        "## Model Family Effects",
        "",
    ]
    for effect in payload["model_family_effects"]:
        lines.append(
            f"- `{effect['family_id']}`: full `{effect['full_native_fit_status']}`, "
            f"downsampled `{effect['downsampled_fit_status']}`; {effect['effect_of_downsampling']}"
        )
    lines.extend(["", "## Removed Inputs", ""])
    for item in payload["paired_conditions"][1]["removed_inputs"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Provenance Notes", ""])
    lines.extend(f"- {item}" for item in payload["strict_provenance_notes"])
    lines.append("")
    return "\n".join(lines)


def write_history_ablation(output_dir: str | Path, payload: dict[str, Any]) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    return {
        "json": write_json(output / "history_ablation.json", payload),
        "md": write_markdown(output / "history_ablation.md", render_history_ablation_markdown(payload)),
    }
