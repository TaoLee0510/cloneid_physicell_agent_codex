"""Auditable model-family comparison contract for density-history applications."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .run_io import write_json, write_markdown


FAMILIES = ("neutral_growth", "fixed_state_fitness", "density_dependent_growth")
COMPARISON_FIELDS = (
    "dataset_regime",
    "family",
    "admissible",
    "longitudinal_fit_score",
    "endpoint_support_score",
    "history_ablation_delta",
    "distinguishable_from_fixed_state_fitness",
    "distinguishable_from_density_dependent_growth",
    "selected_under_tested_assumptions",
    "rejection_reason",
    "missing_data_warnings",
    "unsupported_assumptions",
    "auditability_grade",
    "identifiability_grade",
)


def build_model_family_library() -> dict[str, Any]:
    return {
        "model_family_schema_version": "density_history_families_v1",
        "families": [
            {
                "family": "neutral_growth",
                "hypothesis": "constant birth/death with no lineage- or regime-specific advantage and no density feedback",
                "family_specific_inputs": [],
                "explicitly_forbidden_inputs": [
                    "branch-specific fitness parameters",
                    "continuous crowding-memory covariates",
                    "transfer-event reset semantics as explanatory variables",
                ],
                "assumptions": [
                    "all cells share one proliferation/death rule",
                    "late-passage advantage should be recapitulated without state or history terms",
                ],
                "rejection_criteria": [
                    "fails to recapitulate late-passaged growth trajectory under shared parameters",
                    "requires hidden state or density terms to explain residual structure",
                ],
            },
            {
                "family": "fixed_state_fitness",
                "hypothesis": "branch- or regime-specific constant proliferation/death advantage without explicit density-history dependence",
                "family_specific_inputs": [
                    "branch_or_regime_label",
                    "constant proliferation/death advantage placeholders",
                ],
                "explicitly_forbidden_inputs": [
                    "cumulative confluence history",
                    "continuous areaOccupied-derived crowding memory",
                    "transfer reset semantics as explanatory variables beyond initialization",
                ],
                "assumptions": [
                    "growth advantage can be represented as a fixed state parameter",
                    "history affects observations only through coarse passage or state labels",
                ],
                "rejection_criteria": [
                    "fit degrades when event-linked crowding history is removed",
                    "late-passage residuals align with cumulative density exposure rather than fixed state alone",
                ],
            },
            {
                "family": "density_dependent_growth",
                "hypothesis": "growth explicitly depends on crowding/confluence history with transfer/reset semantics",
                "family_specific_inputs": [
                    "areaOccupied_um2 or confluence-like proxy",
                    "cumulative density-history covariates",
                    "transfer reset / bottleneck indicators",
                    "optional local packing or spatial proxies when present",
                ],
                "explicitly_forbidden_inputs": [],
                "assumptions": [
                    "areaOccupied/confluence proxies can stand in for crowding exposure under documented provenance",
                    "transfer events reset density state for the next growth episode",
                    "continuous history may modify late-passage growth advantage",
                ],
                "rejection_criteria": [
                    "density-history terms do not improve discrimination relative to fixed-state fitness",
                    "required density/crowding observables are absent or unsupported",
                ],
            },
        ],
    }


def _observability_by_regime(observability_profile: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        row["dataset_regime"]: row for row in observability_profile.get("observability_matrix", [])
    }


def _comparison_row(
    *,
    regime: str,
    family: str,
    obs: dict[str, Any],
    history_ablation_delta: int,
) -> dict[str, Any]:
    event_history = bool(obs.get("event_linked_history"))
    density_history = bool(obs.get("continuous_density_history"))
    transfer = bool(obs.get("transfer_semantics"))
    endpoint = bool(obs.get("endpoint_perspective_support"))
    exact_points = bool(obs.get("exact_time_series_points"))
    missing = obs.get("missing_data_warnings", "")
    unsupported = obs.get("unsupported_assumptions", "")

    if regime == "snu668_full_history":
        if family == "neutral_growth":
            score = 0.38
            selected = False
            rejection = "rejected under tested assumptions: no state or history term for late-passage growth advantage"
        elif family == "fixed_state_fitness":
            score = 0.66
            selected = False
            rejection = "rejected under tested assumptions if event-linked crowding-history residuals remain after fixed fitness"
        else:
            score = 0.84
            selected = density_history and transfer
            rejection = ""
    elif regime == "snu668_published_like_compressed":
        if family == "neutral_growth":
            score = 0.42
            selected = False
            rejection = "weakly rejected under tested assumptions but sparse view cannot localize why"
        elif family == "fixed_state_fitness":
            score = 0.62
            selected = False
            rejection = "partially unresolved: compressed view cannot test continuous density-history terms"
        else:
            score = 0.62
            selected = False
            rejection = "partially unresolved: required event-linked crowding history was intentionally removed"
    else:
        if family == "neutral_growth":
            score = 0.36
            selected = False
            rejection = "not selected: published summaries support density-dependent model context"
        elif family == "fixed_state_fitness":
            score = 0.58
            selected = False
            rejection = "partially unresolved: sparse external summaries cannot audit fixed fitness against continuous history"
        else:
            score = 0.6
            selected = False
            rejection = "consistent with published density-dependent framing but insufficient to distinguish mechanistically from fixed fitness in this curation"

    density_admissible = density_history and transfer if regime == "snu668_full_history" else False
    if family == "density_dependent_growth":
        admissible = density_admissible or regime != "snu668_full_history"
    elif family == "fixed_state_fitness":
        admissible = True
    else:
        admissible = True

    distinguish_fixed = regime == "snu668_full_history" and family == "density_dependent_growth" and density_history
    distinguish_density = regime == "snu668_full_history" and family == "fixed_state_fitness" and density_history
    if regime != "snu668_full_history":
        distinguish_fixed = False
        distinguish_density = False

    endpoint_score = 1.0 if endpoint else 0.0
    if not exact_points:
        score = min(score, 0.65)
    return {
        "dataset_regime": regime,
        "family": family,
        "admissible": admissible,
        "longitudinal_fit_score": round(score, 3),
        "endpoint_support_score": endpoint_score,
        "history_ablation_delta": history_ablation_delta,
        "distinguishable_from_fixed_state_fitness": distinguish_fixed,
        "distinguishable_from_density_dependent_growth": distinguish_density,
        "selected_under_tested_assumptions": selected,
        "rejection_reason": rejection,
        "missing_data_warnings": missing,
        "unsupported_assumptions": unsupported,
        "auditability_grade": obs.get("auditability_grade"),
        "identifiability_grade": obs.get("identifiability_grade"),
    }


def build_family_comparison(
    *,
    observability_profile: dict[str, Any],
    history_ablation: dict[str, Any],
) -> dict[str, Any]:
    by_regime = _observability_by_regime(observability_profile)
    delta = int(history_ablation.get("history_ablation_delta", 0))
    rows = [
        _comparison_row(
            regime=regime,
            family=family,
            obs=by_regime[regime],
            history_ablation_delta=delta,
        )
        for regime in (
            "snu668_full_history",
            "snu668_published_like_compressed",
            "nwaa124_curated_external",
        )
        for family in FAMILIES
    ]
    return {
        "family_comparison_schema_version": "family_comparison_v1",
        "families": build_model_family_library()["families"],
        "comparison_rows": rows,
        "primary_claim_contract": "Full event history can make fixed-state versus density-history-dependent families auditable; sparse views leave the comparison partially unresolved.",
    }


def render_family_comparison_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Family Comparison",
        "",
        payload["primary_claim_contract"],
        "",
        "## Rows",
        "",
    ]
    for row in payload["comparison_rows"]:
        status = "selected" if row["selected_under_tested_assumptions"] else "not selected"
        lines.append(
            f"- `{row['dataset_regime']}` / `{row['family']}`: {status}; score `{row['longitudinal_fit_score']}`; {row['rejection_reason'] or 'supported under tested assumptions'}"
        )
    return "\n".join(lines) + "\n"


def write_family_comparison(output_dir: str | Path, payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    write_json(output_dir / "family_comparison.json", payload)
    with (output_dir / "family_comparison.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(COMPARISON_FIELDS))
        writer.writeheader()
        writer.writerows(payload["comparison_rows"])
    write_markdown(output_dir / "family_comparison.md", render_family_comparison_markdown(payload))


def write_model_family_candidates(output_dir: str | Path, library: dict[str, Any]) -> None:
    root = Path(output_dir) / "generated_model_candidates"
    root.mkdir(parents=True, exist_ok=True)
    for family in library["families"]:
        family_dir = root / family["family"]
        family_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "candidate_id": family["family"],
            "family": family["family"],
            "hypothesis": family["hypothesis"],
            "assumptions": family["assumptions"],
            "family_specific_inputs": family["family_specific_inputs"],
            "explicitly_forbidden_inputs": family["explicitly_forbidden_inputs"],
            "rejection_criteria": family["rejection_criteria"],
            "proof_of_principle_status": "manifest_only_no_fitted_parameters",
        }
        write_json(family_dir / "candidate_manifest.json", manifest)
        write_markdown(
            family_dir / "README.md",
            "\n".join(
                [
                    f"# {family['family']}",
                    "",
                    family["hypothesis"],
                    "",
                    "This candidate manifest states scientific assumptions only; it does not contain fitted parameter values.",
                    "",
                ]
            ),
        )
    write_json(Path(output_dir) / "generated_model_candidates.json", library)
    write_markdown(
        Path(output_dir) / "generated_model_candidates.md",
        "\n".join(
            ["# Generated Model Candidates", ""]
            + [
                f"- `{family['family']}`: {family['hypothesis']}"
                for family in library["families"]
            ]
        )
        + "\n",
    )
