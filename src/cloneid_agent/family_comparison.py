"""Evidence-structure-aware model-family comparison for the r/K benchmark."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .rk_density_models import MODEL_FAMILIES, NOT_IDENTIFIABLE_DENSITY
from .run_io import write_json, write_markdown


FAMILY_REQUIREMENTS = {
    "context_blind_null": {
        "required": ["coarse growth summary"],
        "meaning": "one shared growth behavior without branch or density terms",
    },
    "proliferation_only": {
        "required": ["seed/harvest counts", "growth duration"],
        "meaning": "growth explained by proliferation-rate differences alone",
    },
    "branch_specific_fitness": {
        "required": ["branch labels", "seed/harvest counts", "growth duration"],
        "meaning": "r/K branches have fixed fitness parameters without density-history terms",
    },
    "density_dependent_growth": {
        "required": ["event graph", "seed/harvest episodes", "event-linked confluence proxy"],
        "meaning": "growth depends on density/confluence history",
    },
    "density_plus_branch_optional": {
        "required": ["event graph", "seed/harvest episodes", "event-linked confluence proxy", "branch labels"],
        "meaning": "density response plus optional branch-specific term",
    },
}


FAMILY_COMPARISON_FIELDS = (
    "dataset_regime",
    "family_id",
    "fit_status",
    "identifiable",
    "reason_if_not_identifiable",
    "required_inputs_available",
    "required_inputs_missing",
    "auditability_grade",
    "identifiability_grade",
    "selected_under_tested_assumptions",
    "rejected_under_tested_assumptions",
    "unresolved_under_available_records",
    "overclaim_guardrail",
    "rmse",
    "aic",
)


def _model_by_family(fits: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["family_id"]: row for row in fits.get("models", [])}


def _obs_by_regime(observability_profile: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["dataset_regime"]: row for row in observability_profile.get("observability_matrix", [])}


def _input_status(regime: str, family_id: str, obs: dict[str, Any]) -> tuple[list[str], list[str]]:
    requirements = FAMILY_REQUIREMENTS[family_id]["required"]
    available: list[str] = []
    missing: list[str] = []
    for item in requirements:
        if item == "coarse growth summary":
            available.append(item)
        elif item == "branch labels":
            available.append(item)
        elif item == "seed/harvest counts":
            if obs.get("seed_harvest_transfer_classification") == "available":
                available.append(item)
            else:
                missing.append(item)
        elif item == "growth duration":
            if obs.get("exact_time_series_points") == "available":
                available.append(item)
            else:
                missing.append(item)
        elif item == "event graph":
            if obs.get("parent_child_event_graph") == "available":
                available.append(item)
            else:
                missing.append(item)
        elif item == "seed/harvest episodes":
            if obs.get("seed_harvest_transfer_classification") == "available":
                available.append(item)
            else:
                missing.append(item)
        elif item == "event-linked confluence proxy":
            if obs.get("confluence_proxy") in {"available", "structured_numeric_table"}:
                available.append(item)
            else:
                missing.append(item)
    if regime == "NSR_publication_level_reconstructed_record" and family_id in {
        "proliferation_only",
        "branch_specific_fitness",
    }:
        available.append("Supplementary Table 5 growth-rate distribution")
    return available, missing


def build_family_comparison(
    *,
    observability_profile: dict[str, Any],
    nsr_fits: dict[str, Any],
    cloneid_full_fits: dict[str, Any],
    cloneid_coarse_fits: dict[str, Any],
) -> dict[str, Any]:
    fit_sources = {
        "NSR_publication_level_reconstructed_record": _model_by_family(nsr_fits),
        "CLONEID_full_native_record": _model_by_family(cloneid_full_fits),
        "CLONEID_publication_level_downsampled_record": _model_by_family(cloneid_coarse_fits),
    }
    obs_sources = _obs_by_regime(observability_profile)
    best_full = cloneid_full_fits.get("best_supported_family")
    rows: list[dict[str, Any]] = []
    for regime, fits in fit_sources.items():
        obs = obs_sources.get(regime, {})
        for family_id in MODEL_FAMILIES:
            fit = fits.get(family_id, {})
            available, missing = _input_status(regime, family_id, obs)
            fit_status = fit.get("fit_status", "not_available_in_archive")
            identifiable = fit_status in {"identifiable", "summary_only_identifiable", "publication_level_reconstruction_only"}
            if fit_status == NOT_IDENTIFIABLE_DENSITY:
                identifiable = False
            selected = regime == "CLONEID_full_native_record" and family_id == best_full
            unresolved = (
                fit_status == "publication_level_reconstruction_only"
                or "not_agent_ready" in " ".join(missing)
                or (regime != "CLONEID_full_native_record" and family_id in {"density_dependent_growth", "density_plus_branch_optional"})
            )
            rejected = regime == "CLONEID_full_native_record" and bool(best_full) and family_id != best_full
            reason = fit.get("reason") or fit.get("limitation") or ""
            if not identifiable and not reason:
                reason = "required event-linked inputs are missing under this record regime"
            rows.append(
                {
                    "dataset_regime": regime,
                    "family_id": family_id,
                    "fit_status": fit_status,
                    "identifiable": identifiable,
                    "reason_if_not_identifiable": reason,
                    "required_inputs_available": "; ".join(available),
                    "required_inputs_missing": "; ".join(missing),
                    "auditability_grade": obs.get("auditability_grade", ""),
                    "identifiability_grade": obs.get("identifiability_grade", ""),
                    "selected_under_tested_assumptions": selected,
                    "rejected_under_tested_assumptions": rejected,
                    "unresolved_under_available_records": unresolved,
                    "overclaim_guardrail": _guardrail_for_row(regime, family_id, fit_status),
                    "rmse": fit.get("rmse", ""),
                    "aic": fit.get("aic", ""),
                }
            )
    return {
        "family_comparison_schema_version": "cloneid_lte_family_comparison_v2",
        "families": [
            {"family_id": family_id, **FAMILY_REQUIREMENTS[family_id]}
            for family_id in MODEL_FAMILIES
        ],
        "comparison_rows": rows,
        "primary_claim_contract": "Event-linked CLONEID records make density/confluence model families auditable; publication-level records support reconstruction but leave key comparisons unresolved.",
    }


def _guardrail_for_row(regime: str, family_id: str, fit_status: str) -> str:
    if regime == "NSR_publication_level_reconstructed_record":
        return "publication-level reconstruction only; do not treat plot-only evidence as raw numeric data"
    if regime == "CLONEID_publication_level_downsampled_record":
        return "coarse record cannot identify density-history terms after event linkage removal"
    if fit_status == "identifiable":
        return "identifiable under available mock records; manuscript numerical interpretation requires live or frozen CLONEID data"
    return "unresolved under available records"


def render_family_comparison_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Family Comparison",
        "",
        payload["primary_claim_contract"],
        "",
    ]
    for row in payload["comparison_rows"]:
        if row["selected_under_tested_assumptions"]:
            status = "selected under tested assumptions"
        elif row["rejected_under_tested_assumptions"]:
            status = "rejected under tested assumptions"
        elif row["unresolved_under_available_records"]:
            status = "unresolved under available records"
        else:
            status = row["fit_status"]
        lines.append(
            f"- `{row['dataset_regime']}` / `{row['family_id']}`: {status}; "
            f"identifiability `{row['identifiability_grade']}`."
        )
    lines.append("")
    return "\n".join(lines)


def write_family_comparison(output_dir: str | Path, payload: dict[str, Any]) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    csv_path = output / "family_comparison.csv"
    with csv_path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(FAMILY_COMPARISON_FIELDS))
        writer.writeheader()
        writer.writerows(payload["comparison_rows"])
    return {
        "json": write_json(output / "family_comparison.json", payload),
        "csv": csv_path,
        "md": write_markdown(output / "family_comparison.md", render_family_comparison_markdown(payload)),
    }
