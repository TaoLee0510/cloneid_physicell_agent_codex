"""Comparative identifiability summaries across full, compressed, and external regimes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .run_io import write_json, write_markdown


def build_comparative_identifiability(
    *,
    observability_profile: dict[str, Any],
    family_comparison: dict[str, Any],
    history_ablation: dict[str, Any],
) -> dict[str, Any]:
    rows_by_regime = {
        row["dataset_regime"]: row for row in observability_profile.get("observability_matrix", [])
    }
    comparison_by_regime: dict[str, list[dict[str, Any]]] = {}
    for row in family_comparison.get("comparison_rows", []):
        comparison_by_regime.setdefault(row["dataset_regime"], []).append(row)

    summaries = []
    for regime, obs in rows_by_regime.items():
        selected = [
            row["family"]
            for row in comparison_by_regime.get(regime, [])
            if row.get("selected_under_tested_assumptions")
        ]
        unresolved = [
            row["family"]
            for row in comparison_by_regime.get(regime, [])
            if "partially unresolved" in row.get("rejection_reason", "")
            or "insufficient" in row.get("rejection_reason", "")
        ]
        if regime == "snu668_full_history":
            resolution = "fixed-state and density-history-dependent families are auditable under the dry-run contract"
        elif regime == "snu668_published_like_compressed":
            resolution = "comparison is partially unresolved after controlled loss of event-linked history"
        else:
            resolution = "external published sparse view supports observability discussion but remains partially unresolved"
        summaries.append(
            {
                "dataset_regime": regime,
                "auditability_grade": obs["auditability_grade"],
                "identifiability_grade": obs["identifiability_grade"],
                "selected_families_under_tested_assumptions": selected,
                "partially_unresolved_families": unresolved,
                "resolution_statement": resolution,
            }
        )
    return {
        "comparative_identifiability_schema_version": "comparative_identifiability_v1",
        "history_ablation_delta": history_ablation.get("history_ablation_delta"),
        "summaries": summaries,
        "manuscript_claim_boundary": [
            "proof of principle only",
            "terminal Perspective is endpoint validation/support only",
            "Identity is inferred secondary support only",
            "compressed and external arms measure observability/identifiability loss",
            "no cross-cell-line biological truth claim",
        ],
        "low_cost_fields_that_rescue_identifiability": [
            "event_id and parent_event_id ledger",
            "timestamped seeding and harvest records",
            "seeding count or density and vessel area",
            "split ratio or transfer threshold",
            "event-linked cellCount, areaOccupied, and confluence proxy with QC",
            "terminal Perspective anchor to the originating Event",
        ],
    }


def render_comparative_identifiability_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Comparative Identifiability Report",
        "",
        f"- History ablation delta: `{payload['history_ablation_delta']}`",
        "",
        "## Regime summaries",
        "",
    ]
    for summary in payload["summaries"]:
        lines.append(f"### {summary['dataset_regime']}")
        lines.append(f"- Auditability: `{summary['auditability_grade']}`")
        lines.append(f"- Identifiability: `{summary['identifiability_grade']}`")
        lines.append(f"- Resolution: {summary['resolution_statement']}")
        selected = summary["selected_families_under_tested_assumptions"] or ["none"]
        lines.append(f"- Selected under tested assumptions: `{', '.join(selected)}`")
        unresolved = summary["partially_unresolved_families"] or ["none"]
        lines.append(f"- Partially unresolved families: `{', '.join(unresolved)}`")
        lines.append("")
    lines.append("## Claim boundary")
    for item in payload["manuscript_claim_boundary"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Low-cost fields that rescue identifiability")
    for item in payload["low_cost_fields_that_rescue_identifiability"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def render_family_discrimination_summary(payload: dict[str, Any]) -> str:
    full = next(item for item in payload["summaries"] if item["dataset_regime"] == "snu668_full_history")
    compressed = next(item for item in payload["summaries"] if item["dataset_regime"] == "snu668_published_like_compressed")
    external = next(item for item in payload["summaries"] if item["dataset_regime"] == "nwaa124_curated_external")
    return (
        "# Family Discrimination Summary\n\n"
        "Full CLONEID event history preserves the inputs needed to audit fixed-state fitness against density-history-dependent growth. "
        f"In the full-history regime the selected family set is `{', '.join(full['selected_families_under_tested_assumptions'] or ['none'])}` under the dry-run contract. "
        "The compressed SNU-668 view and NWAA124 external sparse view both lose continuous event-linked history, so fixed-state and density-history-dependent explanations remain partially unresolved there.\n\n"
        f"- Full history identifiability: `{full['identifiability_grade']}`\n"
        f"- Compressed-view identifiability: `{compressed['identifiability_grade']}`\n"
        f"- External sparse-view identifiability: `{external['identifiability_grade']}`\n"
    )


def write_comparative_identifiability(output_dir: str | Path, payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    write_json(output_dir / "comparative_identifiability.json", payload)
    write_markdown(output_dir / "comparative_identifiability_report.md", render_comparative_identifiability_report(payload))
    write_markdown(output_dir / "family_discrimination_summary.md", render_family_discrimination_summary(payload))
