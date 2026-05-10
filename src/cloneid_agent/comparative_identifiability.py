"""Comparative identifiability summaries for r/K benchmark regimes."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .run_io import write_json, write_markdown


LOW_COST_FIELDS_THAT_RESCUE_IDENTIFIABILITY = [
    "event_id and parent_event_id ledger",
    "timestamped seeding, harvest, transfer, and bottleneck records",
    "seeded and harvested cell counts",
    "vessel area and split ratio or bottleneck ratio",
    "event-linked areaOccupied, cellSize, and confluence proxy with QC",
    "image URI and segmentation/provenance version",
    "terminal Perspective anchor to upstream culture event",
]


def build_comparative_identifiability(
    *,
    observability_profile: dict[str, Any],
    family_comparison: dict[str, Any],
    history_ablation: dict[str, Any],
) -> dict[str, Any]:
    obs_by_regime = {
        row["dataset_regime"]: row for row in observability_profile.get("observability_matrix", [])
    }
    comparison_by_regime: dict[str, list[dict[str, Any]]] = {}
    for row in family_comparison.get("comparison_rows", []):
        comparison_by_regime.setdefault(row["dataset_regime"], []).append(row)

    summaries = []
    for regime, obs in obs_by_regime.items():
        rows = comparison_by_regime.get(regime, [])
        selected = [row["family_id"] for row in rows if row.get("selected_under_tested_assumptions")]
        rejected = [row["family_id"] for row in rows if row.get("rejected_under_tested_assumptions")]
        unresolved = [row["family_id"] for row in rows if row.get("unresolved_under_available_records")]
        resolution = _resolution_statement_from_rows(rows)
        summaries.append(
            {
                "dataset_regime": regime,
                "auditability_grade": obs.get("auditability_grade"),
                "identifiability_grade": obs.get("identifiability_grade"),
                "selected_under_tested_assumptions": selected,
                "rejected_under_tested_assumptions": rejected,
                "unresolved_under_available_records": unresolved,
                "resolution_statement": resolution,
            }
        )

    return {
        "comparative_identifiability_schema_version": "cloneid_lte_comparative_identifiability_v2",
        "history_ablation_delta": history_ablation.get("history_ablation_delta"),
        "summaries": summaries,
        "low_cost_fields_that_rescue_identifiability": LOW_COST_FIELDS_THAT_RESCUE_IDENTIFIABILITY,
        "manuscript_claim_boundary": [
            "No mechanism proof is claimed.",
            "HeLa and SNU-668 biology are not treated as biologically equivalent.",
            "NSR is treated as a strong publication-level comparator, not criticized.",
            "Endpoint Perspective is validation/support only.",
            "Identity is inferred secondary support only.",
            "Transfer/passaging events are schedule resets, not growth intervals.",
            "Mock SNU-668 values require replacement by live read-only CLONEID extraction or approved frozen snapshot for manuscript numerical interpretation.",
        ],
    }


def _resolution_statement_from_rows(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "no family-comparison evidence was generated"
    selected = [row["family_id"] for row in rows if row.get("selected_under_tested_assumptions")]
    rejected = [row["family_id"] for row in rows if row.get("rejected_under_tested_assumptions")]
    unresolved_rows = [row for row in rows if row.get("unresolved_under_available_records")]
    if selected and rejected and not unresolved_rows:
        return (
            "model-family comparison is resolved under tested assumptions: "
            f"selected {', '.join(selected)} and rejected {', '.join(rejected)}"
        )
    if unresolved_rows:
        basis = "; ".join(
            f"{row['family_id']}: {row.get('dominant_limitation') or row.get('status_decision_basis')}"
            for row in unresolved_rows[:2]
        )
        return f"partially unresolved under available records because {basis}"
    identifiable = [row["family_id"] for row in rows if row.get("identifiable")]
    if identifiable:
        return f"families are identifiable but not uniquely selected under available evidence: {', '.join(identifiable)}"
    return "not identifiable under available records because required evidence is missing"


def render_comparative_identifiability_report(payload: dict[str, Any]) -> str:
    lines = [
        "# Comparative Identifiability Report",
        "",
        f"- History ablation delta: `{payload['history_ablation_delta']}`",
        "",
        "## Regime Summaries",
        "",
    ]
    for summary in payload["summaries"]:
        lines.append(f"### {summary['dataset_regime']}")
        lines.append(f"- Auditability: `{summary['auditability_grade']}`")
        lines.append(f"- Identifiability: `{summary['identifiability_grade']}`")
        lines.append(f"- Resolution: {summary['resolution_statement']}")
        selected = summary["selected_under_tested_assumptions"] or ["none"]
        rejected = summary["rejected_under_tested_assumptions"] or ["none"]
        unresolved = summary["unresolved_under_available_records"] or ["none"]
        lines.append(f"- Selected: `{', '.join(selected)}`")
        lines.append(f"- Rejected: `{', '.join(rejected)}`")
        lines.append(f"- Unresolved: `{', '.join(unresolved)}`")
        lines.append("")
    lines.append("## Low-Cost Fields That Rescue Identifiability")
    lines.extend(f"- {item}" for item in payload["low_cost_fields_that_rescue_identifiability"])
    lines.extend(["", "## Claim Boundary"])
    lines.extend(f"- {item}" for item in payload["manuscript_claim_boundary"])
    lines.append("")
    return "\n".join(lines)


def write_comparative_identifiability(output_dir: str | Path, payload: dict[str, Any]) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    return {
        "json": write_json(output / "comparative_identifiability_report.json", payload),
        "md": write_markdown(
            output / "comparative_identifiability_report.md",
            render_comparative_identifiability_report(payload),
        ),
    }
