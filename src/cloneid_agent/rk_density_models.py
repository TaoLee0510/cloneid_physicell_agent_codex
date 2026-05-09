"""Lightweight r/K density adaptation model fits and identifiability summaries."""

from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any


MODEL_FAMILIES = (
    "context_blind_null",
    "proliferation_only",
    "branch_specific_fitness",
    "density_dependent_growth",
    "density_plus_branch_optional",
)

MANUSCRIPT_MODEL_FAMILIES = (
    "neutral_growth",
    "fixed_state_fitness",
    "density_dependent_growth",
)

MANUSCRIPT_TO_INTERNAL_FAMILY = {
    "neutral_growth": "context_blind_null",
    "fixed_state_fitness": "branch_specific_fitness",
    "density_dependent_growth": "density_dependent_growth",
}

INTERNAL_TO_MANUSCRIPT_FAMILY = {
    "context_blind_null": "neutral_growth",
    "proliferation_only": "neutral_growth",
    "branch_specific_fitness": "fixed_state_fitness",
    "density_dependent_growth": "density_dependent_growth",
    "density_plus_branch_optional": "density_dependent_growth",
}

NOT_IDENTIFIABLE_DENSITY = "not_identifiable_due_to_missing_event_level_density_or_event_graph"


def _solve_linear_least_squares(design: list[list[float]], y: list[float]) -> list[float]:
    """Solve small normal equations with Gaussian elimination."""

    if not design:
        return []
    k = len(design[0])
    xtx = [[0.0 for _ in range(k)] for _ in range(k)]
    xty = [0.0 for _ in range(k)]
    for row, target in zip(design, y):
        for i in range(k):
            xty[i] += row[i] * target
            for j in range(k):
                xtx[i][j] += row[i] * row[j]

    for i in range(k):
        xtx[i][i] += 1e-12
    matrix = [xtx[i] + [xty[i]] for i in range(k)]
    for pivot in range(k):
        best = max(range(pivot, k), key=lambda row_idx: abs(matrix[row_idx][pivot]))
        matrix[pivot], matrix[best] = matrix[best], matrix[pivot]
        pivot_value = matrix[pivot][pivot]
        if abs(pivot_value) < 1e-15:
            continue
        for col in range(pivot, k + 1):
            matrix[pivot][col] /= pivot_value
        for row_idx in range(k):
            if row_idx == pivot:
                continue
            factor = matrix[row_idx][pivot]
            for col in range(pivot, k + 1):
                matrix[row_idx][col] -= factor * matrix[pivot][col]
    return [matrix[i][k] for i in range(k)]


def _fit_rate_model(
    *,
    family_id: str,
    episodes: list[dict[str, Any]],
    design_builder,
    parameter_names: list[str],
) -> dict[str, Any]:
    design: list[list[float]] = []
    y: list[float] = []
    for episode in episodes:
        design.append(design_builder(episode))
        y.append(float(episode["growth_rate_per_hour"]))
    coefficients = _solve_linear_least_squares(design, y)
    predictions: list[dict[str, Any]] = []
    sse = 0.0
    for episode, row, observed_rate in zip(episodes, design, y):
        predicted_rate = sum(coef * value for coef, value in zip(coefficients, row))
        predicted_end = float(episode["seed_corrected_count"]) * math.exp(
            predicted_rate * float(episode["duration_hours"])
        )
        observed_end = float(episode["harvest_corrected_count"])
        error = predicted_end - observed_end
        sse += error * error
        predictions.append(
            {
                "episode_id": episode["episode_id"],
                "observed_rate_per_hour": observed_rate,
                "predicted_rate_per_hour": predicted_rate,
                "observed_harvest_corrected_count": observed_end,
                "predicted_harvest_corrected_count": predicted_end,
            }
        )
    n = max(len(episodes), 1)
    k = len(parameter_names)
    rmse = math.sqrt(sse / n)
    aic = n * math.log(max(sse / n, 1e-12)) + 2 * k
    return {
        "family_id": family_id,
        "fit_status": "identifiable",
        "parameters": {name: value for name, value in zip(parameter_names, coefficients)},
        "n_episodes": len(episodes),
        "sse": sse,
        "rmse": rmse,
        "aic": aic,
        "predictions": predictions,
    }


def fit_cloneid_full_models(growth_episodes: list[dict[str, Any]]) -> dict[str, Any]:
    """Fit simple rate models to event-linked CLONEID growth episodes."""

    episodes = [row for row in growth_episodes if row["branch_label"] in {"r", "K"}]
    if not episodes:
        return {"models": [], "best_supported_family": None}
    models = [
        _fit_rate_model(
            family_id="context_blind_null",
            episodes=episodes,
            design_builder=lambda _row: [1.0],
            parameter_names=["shared_mean_growth_rate_per_hour"],
        ),
        _fit_rate_model(
            family_id="proliferation_only",
            episodes=episodes,
            design_builder=lambda _row: [1.0],
            parameter_names=["shared_exponential_rate_per_hour"],
        ),
        _fit_rate_model(
            family_id="branch_specific_fitness",
            episodes=episodes,
            design_builder=lambda row: [1.0, 1.0 if row["branch_label"] == "K" else 0.0],
            parameter_names=["r_baseline_rate_per_hour", "K_branch_rate_delta_per_hour"],
        ),
        _fit_rate_model(
            family_id="density_dependent_growth",
            episodes=episodes,
            design_builder=lambda row: [1.0, float(row["seed_confluence_proxy"])],
            parameter_names=["baseline_rate_per_hour", "seed_confluence_slope_per_hour"],
        ),
        _fit_rate_model(
            family_id="density_plus_branch_optional",
            episodes=episodes,
            design_builder=lambda row: [
                1.0,
                float(row["seed_confluence_proxy"]),
                1.0 if row["branch_label"] == "K" else 0.0,
            ],
            parameter_names=["baseline_rate_per_hour", "seed_confluence_slope_per_hour", "K_branch_delta_per_hour"],
        ),
    ]
    best = min(models, key=lambda item: item["aic"])
    return {
        "models": models,
        "best_supported_family": best["family_id"],
        "selection_rule": "lowest AIC among identifiable event-linked mock fits",
        "usage_guardrails": [
            "Transfer/passaging events are excluded from growth-rate fitting.",
            "Endpoint Perspective is validation/support only.",
            "Identity is secondary inferred support only.",
        ],
    }


def fit_cloneid_coarse_models(coarse_record: dict[str, Any]) -> dict[str, Any]:
    """Summarize identifiable models after publication-level downsampling."""

    summaries = coarse_record.get("coarse_growth_summary", [])
    models: list[dict[str, Any]] = []
    for family in MODEL_FAMILIES:
        if family in {"density_dependent_growth", "density_plus_branch_optional"}:
            models.append(
                {
                    "family_id": family,
                    "fit_status": NOT_IDENTIFIABLE_DENSITY,
                    "reason": "event graph and per-event confluence proxy were removed by downsampling",
                }
            )
        elif family == "branch_specific_fitness":
            branch_rates = {
                row["branch_label"]: row["mean_growth_rate_per_hour"]
                for row in summaries
                if row["branch_label"] in {"r", "K"}
            }
            models.append(
                {
                    "family_id": family,
                    "fit_status": "summary_only_identifiable",
                    "branch_mean_growth_rates": branch_rates,
                    "limitation": "group means are available, but seed-harvest-transfer event linkage is absent",
                }
            )
        else:
            values = [row["mean_growth_rate_per_hour"] for row in summaries if row["branch_label"] in {"r", "K"}]
            shared = sum(values) / len(values) if values else None
            models.append(
                {
                    "family_id": family,
                    "fit_status": "summary_only_identifiable",
                    "shared_mean_growth_rate_per_hour": shared,
                    "limitation": "coarse summary does not preserve event-level density or transfer resets",
                }
            )
    return {
        "models": models,
        "best_supported_family": None,
        "selection_rule": "density/confluence models are not identifiable after downsampling",
    }


def fit_nsr_reconstructed_models(publication_record: dict[str, Any]) -> dict[str, Any]:
    """Fit or summarize coarse NSR models supported by extracted records."""

    growth_summary = publication_record.get("growth_summary", [])
    model_records = publication_record.get("model_records", {})
    branch_rates = {
        row["branch_label"]: {
            "n": row["n"],
            "mean_growth_rate": row["mean_growth_rate"],
            "sd_growth_rate": row["sd_growth_rate"],
        }
        for row in growth_summary
    }
    fig9 = model_records.get("growth_model_fit_statistics", [])
    fig10 = model_records.get("carrying_capacity_logistic_formulas", [])
    methods = model_records.get("methods_model_records", [])
    models = [
        {
            "family_id": "context_blind_null",
            "fit_status": "summary_only_identifiable",
            "inputs": "Supplementary Table 5 growth-rate samples",
            "branch_rates": branch_rates,
        },
        {
            "family_id": "proliferation_only",
            "fit_status": "summary_only_identifiable",
            "inputs": "Supplementary Table 5 growth-rate samples",
            "branch_rates": branch_rates,
        },
        {
            "family_id": "branch_specific_fitness",
            "fit_status": "summary_only_identifiable",
            "inputs": "r/K grouped growth-rate samples from Supplementary Table 5",
            "branch_rates": {key: value for key, value in branch_rates.items() if key in {"r", "K"}},
        },
        {
            "family_id": "density_dependent_growth",
            "fit_status": "publication_level_reconstruction_only",
            "published_support": {
                "figure_9_r_squared": fig9,
                "figure_10_logistic_formulas": fig10,
            },
            "limitation": "event-level confluence and seed-harvest-transfer graph are not available in archive",
        },
        {
            "family_id": "density_plus_branch_optional",
            "fit_status": "publication_level_reconstruction_only",
            "published_support": {
                "interaction_parameter_records": methods,
                "mixed_population_plots": model_records.get("plot_only_limitations", []),
            },
            "limitation": "mixed-population plots require deterministic digitization before trajectory fitting",
        },
    ]
    return {
        "models": models,
        "published_evidence": {
            "growth_rate_distribution": "Supplementary Table 5",
            "growth_model_r_squared": "Supplementary Figure 9",
            "carrying_capacity_formulas": "Supplementary Figure 10",
            "mixed_population_dynamics": "Supplementary Figures 4, 5, 11, 12",
        },
        "guardrail": "NSR is a strong biological comparator; this fit summary is limited by publication-level record structure.",
    }


def project_fits_to_manuscript_families(fits: dict[str, Any]) -> dict[str, Any]:
    """Map extended benchmark fit families onto the three paper-facing families."""

    by_internal = {row["family_id"]: row for row in fits.get("models", [])}
    models: list[dict[str, Any]] = []
    for family_id in MANUSCRIPT_MODEL_FAMILIES:
        internal_id = MANUSCRIPT_TO_INTERNAL_FAMILY[family_id]
        source = dict(by_internal.get(internal_id, {"family_id": internal_id, "fit_status": "not_available_in_archive"}))
        source["source_internal_family_id"] = source.get("family_id", internal_id)
        source["family_id"] = family_id
        if family_id == "density_dependent_growth" and "density_plus_branch_optional" in by_internal:
            optional = by_internal["density_plus_branch_optional"]
            if optional.get("fit_status") == "identifiable" and optional.get("aic", float("inf")) < source.get("aic", float("inf")):
                source["source_internal_family_id"] = "density_plus_branch_optional"
                source["aic"] = optional.get("aic", source.get("aic"))
                source["rmse"] = optional.get("rmse", source.get("rmse"))
                source["fit_status"] = optional.get("fit_status", source.get("fit_status"))
                source["reason"] = (
                    "best extended internal density model included an optional branch term; "
                    "manuscript-facing interpretation remains density-dependent growth"
                )
        models.append(source)
    best_internal = fits.get("best_supported_family")
    best_manuscript = INTERNAL_TO_MANUSCRIPT_FAMILY.get(best_internal) if best_internal else None
    payload = dict(fits)
    payload["models"] = models
    payload["best_supported_family"] = best_manuscript
    payload["source_best_supported_family"] = best_internal
    payload["family_projection"] = "extended benchmark families mapped to neutral_growth, fixed_state_fitness, and density_dependent_growth"
    return payload


def build_model_family_specification() -> dict[str, Any]:
    return {
        "benchmark": "SNU-668 density-history proof-of-principle",
        "central_question": "Can late growth advantage be explained by fixed fitness alone, or is continuous event-linked crowding/confluence history required?",
        "families": [
            {
                "family_id": "neutral_growth",
                "meaning": "No lineage/regime advantage, no density feedback, and no cumulative history dependence.",
                "requires_event_linkage": False,
                "requires_density_proxy": False,
            },
            {
                "family_id": "fixed_state_fitness",
                "meaning": "A constant branch/regime-specific growth advantage is allowed without continuous crowding-memory terms.",
                "requires_event_linkage": True,
                "requires_density_proxy": False,
            },
            {
                "family_id": "density_dependent_growth",
                "meaning": "Growth rate depends on event-linked confluence/density proxy and transfer/reset semantics.",
                "requires_event_linkage": True,
                "requires_density_proxy": True,
            },
        ],
        "extended_internal_families": [
            {
                "family_id": "context_blind_null",
                "manuscript_family": "neutral_growth",
            },
            {
                "family_id": "proliferation_only",
                "manuscript_family": "neutral_growth",
            },
            {
                "family_id": "branch_specific_fitness",
                "manuscript_family": "fixed_state_fitness",
            },
            {
                "family_id": "density_plus_branch_optional",
                "manuscript_family": "density_dependent_growth",
            },
        ],
        "non_growth_event_rule": "Transfer/passaging events are schedule resets, not biological growth episodes.",
        "endpoint_rule": "Endpoint Perspective is validation/support only, not fitting.",
    }


def model_family_specification_markdown(specification: dict[str, Any]) -> str:
    rows = [
        "# r/K Model Family Specification",
        "",
        specification["central_question"],
        "",
        "## Families",
        "",
    ]
    for family in specification["families"]:
        rows.extend(
            [
                f"### {family['family_id']}",
                "",
                family["meaning"],
                "",
                f"- Requires event linkage: `{family['requires_event_linkage']}`",
                f"- Requires density proxy: `{family['requires_density_proxy']}`",
                "",
            ]
        )
    rows.extend(
        [
            "## Rules",
            "",
            f"- {specification['non_growth_event_rule']}",
            f"- {specification['endpoint_rule']}",
            "",
        ]
    )
    return "\n".join(rows)


def build_model_comparison_rows(
    *,
    nsr_fits: dict[str, Any],
    cloneid_full_fits: dict[str, Any],
    cloneid_coarse_fits: dict[str, Any],
) -> list[dict[str, Any]]:
    by_source = {
        "snu668_full_history": cloneid_full_fits["models"],
        "snu668_published_like_compressed": cloneid_coarse_fits["models"],
        "nwaa124_curated_external": nsr_fits["models"],
    }
    rows: list[dict[str, Any]] = []
    for family in MODEL_FAMILIES:
        row: dict[str, Any] = {"family_id": family}
        for source, models in by_source.items():
            model = next((item for item in models if item["family_id"] == family), {})
            fit_status = model.get("fit_status", "not_available_in_archive")
            row[f"{source}_fit_status"] = fit_status
            row[f"{source}_rmse"] = model.get("rmse", "")
            row[f"{source}_aic"] = model.get("aic", "")
            row[f"{source}_identifiability_interpretation"] = _interpret_fit_status(source, family, fit_status)
        rows.append(row)
    return rows


def _interpret_fit_status(source: str, family: str, fit_status: str) -> str:
    if fit_status == "identifiable":
        return "identifiable under available event-linked records"
    if fit_status == "summary_only_identifiable":
        return "summary-identifiable but not fully event-auditable"
    if fit_status == "publication_level_reconstruction_only":
        return "supports coarse reconstruction; unresolved under available publication-level records"
    if fit_status == NOT_IDENTIFIABLE_DENSITY:
        return "not identifiable from coarse records because event-level density or event graph is missing"
    if source == "nwaa124_curated_external":
        return "not available in publication-level archive"
    return "unresolved under available records"


def write_model_comparison_csv(path: str | Path, rows: list[dict[str, Any]]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys()) if rows else ["family_id"]
    with target.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return target


def write_json(path: str | Path, payload: Any) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return target
