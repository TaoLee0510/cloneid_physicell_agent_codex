"""Evidence-structure-aware model-family comparison for the r/K benchmark."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .rk_density_models import (
    MANUSCRIPT_MODEL_FAMILIES,
    NOT_IDENTIFIABLE_DENSITY,
    project_fits_to_manuscript_families,
)
from .run_io import write_json, write_markdown


FAMILY_REQUIREMENTS = {
    "neutral_growth": {
        "required": ["coarse growth summary"],
        "meaning": "no lineage/regime advantage, no density feedback, no cumulative history dependence",
    },
    "fixed_state_fitness": {
        "required": ["branch labels", "seed/harvest counts", "growth duration"],
        "meaning": "constant branch/regime-specific advantage without continuous density-history terms",
    },
    "density_dependent_growth": {
        "required": ["event graph", "seed/harvest episodes", "event-linked confluence proxy"],
        "meaning": "growth depends on crowding/confluence history and transfer/reset semantics",
    },
}


FAMILY_COMPARISON_FIELDS = (
    "dataset_regime",
    "family_id",
    "decision_status",
    "fit_status",
    "identifiable",
    "identifiability_class",
    "reason_if_not_identifiable",
    "required_inputs_available",
    "required_inputs_missing",
    "missing_required_input_count",
    "fit_evidence_available",
    "fit_evidence_strength",
    "observability_support_score",
    "ablation_support_score",
    "overall_identifiability_support",
    "dominant_limitation",
    "status_decision_basis",
    "history_ablation_delta",
    "family_downsampling_effect",
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
    if regime == "nwaa124_curated_external" and family_id in {"neutral_growth", "fixed_state_fitness"}:
        available.append("Supplementary Table 5 growth-rate distribution")
    return available, missing


def _grade_to_support_level(auditability_grade: str, identifiability_grade: str) -> int:
    """Map report grades to a small ordinal support score.

    The score is deliberately simple and auditable: auditability captures provenance,
    while identifiability captures whether the necessary model inputs are observable.
    """

    audit_score = {"A": 3, "B": 2, "C": 1, "D": 0}.get(str(auditability_grade), 0)
    ident_score = {"strong": 3, "moderate": 2, "limited": 1, "poor": 0}.get(
        str(identifiability_grade),
        0,
    )
    return audit_score + ident_score


def _fit_support_strength(fit: dict[str, Any]) -> tuple[bool, str, int]:
    """Classify fit evidence without treating numeric fit metrics as mechanism proof."""

    fit_status = fit.get("fit_status", "not_available_in_archive")
    if fit_status == "identifiable":
        score = 4 if fit.get("rmse") not in (None, "") or fit.get("aic") not in (None, "") else 3
        return True, "event_linked_numeric_fit" if score == 4 else "identifiable_fit_without_metric", score
    if fit_status == "summary_only_identifiable":
        return True, "summary_level_fit", 2
    if fit_status == "publication_level_reconstruction_only":
        return True, "publication_level_reconstruction", 1
    return False, "no_fit_evidence", 0


def _identifiability_class(fit_status: str, missing_count: int) -> str:
    if missing_count:
        return "not_identifiable_due_to_missing_required_inputs"
    if fit_status == "identifiable":
        return "fully_identifiable"
    if fit_status == "summary_only_identifiable":
        return "summary_identifiable"
    if fit_status == "publication_level_reconstruction_only":
        return "publication_level_reconstruction_only"
    return "not_identifiable"


def _ablation_by_family(history_ablation: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not history_ablation:
        return {}
    return {
        row.get("family_id"): row
        for row in history_ablation.get("model_family_effects", [])
        if row.get("family_id")
    }


def _ablation_support_strength(
    *,
    regime: str,
    family_id: str,
    fit_status: str,
    missing_count: int,
    history_ablation: dict[str, Any] | None,
) -> tuple[int, str]:
    """Score whether the paired history ablation explains this row's evidence.

    A positive score means the ablation adds interpretability to the decision,
    not that the biological mechanism is established.
    """

    if not history_ablation:
        return 0, "history ablation not available"
    effect = _ablation_by_family(history_ablation).get(family_id, {})
    text = effect.get("effect_of_downsampling", "")
    source_regime = history_ablation.get("source_regime")
    ablated_regime = history_ablation.get("ablated_regime")
    delta = history_ablation.get("history_ablation_delta") or 0
    downsampled_status = effect.get("downsampled_fit_status")
    full_status = effect.get("full_native_fit_status")

    if regime == source_regime and fit_status == "identifiable" and downsampled_status != fit_status and delta:
        return 3, f"paired ablation shows history loss changes `{family_id}` from `{full_status}` to `{downsampled_status}`"
    if regime == ablated_regime and (missing_count or downsampled_status == NOT_IDENTIFIABLE_DENSITY):
        return 2, text or "paired ablation shows removed history inputs limit this family"
    if delta:
        return 1, "paired history ablation available but not decisive for this row"
    return 0, "paired history ablation did not show material history loss"


def _dominant_limitation(
    *,
    fit: dict[str, Any],
    missing: list[str],
    obs: dict[str, Any],
    ablation_note: str,
) -> str:
    if missing:
        return f"missing required inputs: {', '.join(missing)}"
    if fit.get("reason"):
        return str(fit["reason"])
    if fit.get("limitation"):
        return str(fit["limitation"])
    if obs.get("unsupported_assumptions"):
        return str(obs["unsupported_assumptions"])
    if obs.get("missing_data_warnings"):
        return str(obs["missing_data_warnings"])
    return ablation_note


def _row_decision(
    *,
    family_id: str,
    fit: dict[str, Any],
    missing: list[str],
    fit_evidence_available: bool,
    fit_evidence_strength: str,
    fit_score: int,
    observability_support_score: int,
    ablation_support_score: int,
    selected_family: str | None,
    dominant_limitation: str,
) -> dict[str, Any]:
    fit_status = fit.get("fit_status", "not_available_in_archive")
    missing_count = len(missing)
    identifiable_class = _identifiability_class(fit_status, missing_count)
    overall_support = max(0, fit_score + observability_support_score + ablation_support_score - (2 * missing_count))

    selected = (
        selected_family == family_id
        and identifiable_class == "fully_identifiable"
        and fit_score >= 3
        and observability_support_score >= 4
    )
    rejected = (
        bool(selected_family)
        and selected_family != family_id
        and identifiable_class == "fully_identifiable"
        and fit_score >= 3
        and observability_support_score >= 4
    )

    if selected:
        decision_status = "selected under tested assumptions"
    elif rejected:
        decision_status = "rejected under tested assumptions"
    elif missing_count:
        decision_status = "not identifiable due to missing required inputs"
    elif fit_status in {"summary_only_identifiable", "publication_level_reconstruction_only"}:
        decision_status = "unresolved under available records"
    elif not fit_evidence_available:
        decision_status = "unresolved under available records"
    elif observability_support_score < 3:
        decision_status = "unresolved under available records"
    else:
        decision_status = "identifiable but not selected"

    unresolved = decision_status in {
        "unresolved under available records",
        "not identifiable due to missing required inputs",
    }
    basis = (
        f"fit `{fit_status}` with `{fit_evidence_strength}`; "
        f"{missing_count} required input(s) missing; "
        f"observability support `{observability_support_score}`; "
        f"ablation support `{ablation_support_score}`; "
        f"dominant limitation: {dominant_limitation}"
    )
    return {
        "decision_status": decision_status,
        "identifiable": identifiable_class != "not_identifiable_due_to_missing_required_inputs"
        and identifiable_class != "not_identifiable",
        "identifiability_class": identifiable_class,
        "selected_under_tested_assumptions": selected,
        "rejected_under_tested_assumptions": rejected,
        "unresolved_under_available_records": unresolved,
        "overall_identifiability_support": overall_support,
        "status_decision_basis": basis,
    }


def build_family_comparison(
    *,
    observability_profile: dict[str, Any],
    nsr_fits: dict[str, Any],
    cloneid_full_fits: dict[str, Any],
    cloneid_coarse_fits: dict[str, Any],
    history_ablation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    manuscript_nsr_fits = project_fits_to_manuscript_families(nsr_fits)
    manuscript_full_fits = project_fits_to_manuscript_families(cloneid_full_fits)
    manuscript_coarse_fits = project_fits_to_manuscript_families(cloneid_coarse_fits)
    fit_sources = {
        "snu668_full_history": _model_by_family(manuscript_full_fits),
        "snu668_published_like_compressed": _model_by_family(manuscript_coarse_fits),
        "nwaa124_curated_external": _model_by_family(manuscript_nsr_fits),
    }
    obs_sources = _obs_by_regime(observability_profile)
    best_by_regime = {
        "snu668_full_history": manuscript_full_fits.get("best_supported_family"),
        "snu668_published_like_compressed": manuscript_coarse_fits.get("best_supported_family"),
        "nwaa124_curated_external": manuscript_nsr_fits.get("best_supported_family"),
    }
    ablation_effects = _ablation_by_family(history_ablation)
    rows: list[dict[str, Any]] = []
    for regime, fits in fit_sources.items():
        obs = obs_sources.get(regime, {})
        for family_id in MANUSCRIPT_MODEL_FAMILIES:
            fit = fits.get(family_id, {})
            available, missing = _input_status(regime, family_id, obs)
            fit_status = fit.get("fit_status", "not_available_in_archive")
            fit_evidence_available, fit_evidence_strength, fit_score = _fit_support_strength(fit)
            observability_support_score = _grade_to_support_level(
                obs.get("auditability_grade", ""),
                obs.get("identifiability_grade", ""),
            )
            ablation_support_score, ablation_note = _ablation_support_strength(
                regime=regime,
                family_id=family_id,
                fit_status=fit_status,
                missing_count=len(missing),
                history_ablation=history_ablation,
            )
            dominant_limitation = _dominant_limitation(
                fit=fit,
                missing=missing,
                obs=obs,
                ablation_note=ablation_note,
            )
            decision = _row_decision(
                family_id=family_id,
                fit=fit,
                missing=missing,
                fit_evidence_available=fit_evidence_available,
                fit_evidence_strength=fit_evidence_strength,
                fit_score=fit_score,
                observability_support_score=observability_support_score,
                ablation_support_score=ablation_support_score,
                selected_family=best_by_regime.get(regime),
                dominant_limitation=dominant_limitation,
            )
            reason = fit.get("reason") or fit.get("limitation") or ""
            if decision["identifiability_class"] == "not_identifiable_due_to_missing_required_inputs" and not reason:
                reason = dominant_limitation
            ablation_effect = ablation_effects.get(family_id, {})
            rows.append(
                {
                    "dataset_regime": regime,
                    "family_id": family_id,
                    "decision_status": decision["decision_status"],
                    "fit_status": fit_status,
                    "identifiable": decision["identifiable"],
                    "identifiability_class": decision["identifiability_class"],
                    "reason_if_not_identifiable": reason,
                    "required_inputs_available": "; ".join(available),
                    "required_inputs_missing": "; ".join(missing),
                    "missing_required_input_count": len(missing),
                    "fit_evidence_available": fit_evidence_available,
                    "fit_evidence_strength": fit_evidence_strength,
                    "observability_support_score": observability_support_score,
                    "ablation_support_score": ablation_support_score,
                    "overall_identifiability_support": decision["overall_identifiability_support"],
                    "dominant_limitation": dominant_limitation,
                    "status_decision_basis": decision["status_decision_basis"],
                    "history_ablation_delta": "" if not history_ablation else history_ablation.get("history_ablation_delta", ""),
                    "family_downsampling_effect": ablation_effect.get("effect_of_downsampling", ablation_note),
                    "auditability_grade": obs.get("auditability_grade", ""),
                    "identifiability_grade": obs.get("identifiability_grade", ""),
                    "selected_under_tested_assumptions": decision["selected_under_tested_assumptions"],
                    "rejected_under_tested_assumptions": decision["rejected_under_tested_assumptions"],
                    "unresolved_under_available_records": decision["unresolved_under_available_records"],
                    "overclaim_guardrail": _guardrail_for_row(regime, family_id, fit_status),
                    "rmse": fit.get("rmse", ""),
                    "aic": fit.get("aic", ""),
                }
            )
    return {
        "family_comparison_schema_version": "cloneid_lte_family_comparison_v3",
        "families": [
            {"family_id": family_id, **FAMILY_REQUIREMENTS[family_id]}
            for family_id in MANUSCRIPT_MODEL_FAMILIES
        ],
        "comparison_rows": rows,
        "primary_claim_contract": "Event-linked CLONEID records make density/confluence model families auditable; publication-level records support reconstruction, and unresolved outcomes are assigned from evidence structure rather than regime names.",
    }


def _guardrail_for_row(regime: str, family_id: str, fit_status: str) -> str:
    if regime == "nwaa124_curated_external":
        return "publication-level reconstruction only; do not treat plot-only evidence as raw numeric data"
    if regime == "snu668_published_like_compressed":
        return "coarse record interpretation must follow available inputs and history-ablation evidence"
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
        lines.append(
            f"- `{row['dataset_regime']}` / `{row['family_id']}`: {row.get('decision_status', row['fit_status'])}; "
            f"identifiability `{row['identifiability_grade']}`; basis: {row.get('status_decision_basis', 'not recorded')}."
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
