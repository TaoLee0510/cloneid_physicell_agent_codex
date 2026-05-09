"""Markdown reports for the CLONEID-LTE r/K benchmark."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from .run_io import write_markdown
from .rk_density_models import INTERNAL_TO_MANUSCRIPT_FAMILY


FORBIDDEN_OVERCLAIM_TERMS = (
    "proves",
    "discovers the true mechanism",
    "establishes causality",
    "NSR data are bad",
    "NSR paper is flawed",
    "HeLa and SNU-668 are biologically equivalent",
)


def _best_full_family(cloneid_full_fits: dict[str, Any]) -> str:
    selected = cloneid_full_fits.get("best_supported_family")
    return INTERNAL_TO_MANUSCRIPT_FAMILY.get(selected, selected) if selected else "not selected"


def build_model_selection_report(
    *,
    nsr_fits: dict[str, Any],
    cloneid_full_fits: dict[str, Any],
    cloneid_coarse_fits: dict[str, Any],
    comparison_rows: list[dict[str, Any]],
    observability_profile: dict[str, Any] | None = None,
    history_ablation: dict[str, Any] | None = None,
    family_comparison: dict[str, Any] | None = None,
    comparative_identifiability: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> str:
    family_order = {"neutral_growth": 0, "fixed_state_fitness": 1, "density_dependent_growth": 2}
    regime_order = {
        "snu668_full_history": 0,
        "snu668_published_like_compressed": 1,
        "nwaa124_curated_external": 2,
    }
    family_lines = []
    for row in sorted(
        (family_comparison or {}).get("comparison_rows", []),
        key=lambda item: (regime_order.get(item["dataset_regime"], 99), family_order.get(item["family_id"], 99)),
    ):
        if row["selected_under_tested_assumptions"]:
            status = "selected under tested assumptions"
        elif row["rejected_under_tested_assumptions"]:
            status = "rejected under tested assumptions"
        elif row["unresolved_under_available_records"]:
            status = "unresolved under available records"
        else:
            status = row["fit_status"]
        family_lines.append(
            f"- `{row['dataset_regime']}` / `{row['family_id']}`: {status}; "
            f"missing inputs `{row['required_inputs_missing'] or 'none'}`"
        )
    if not family_lines:
        family_lines = ["- Family comparison was not generated."]

    observability_lines = []
    for row in (observability_profile or {}).get("observability_matrix", []):
        observability_lines.append(
            f"- `{row['dataset_regime']}`: auditability `{row['auditability_grade']}`, "
            f"identifiability `{row['identifiability_grade']}`"
        )
    if not observability_lines:
        observability_lines = ["- Observability profile was not generated."]

    ablation_delta = (history_ablation or {}).get("history_ablation_delta", "not computed")
    low_cost_fields = (comparative_identifiability or {}).get("low_cost_fields_that_rescue_identifiability", [])
    low_cost_lines = [f"- {item}" for item in low_cost_fields] or ["- event-linked minimum metadata fields"]
    required_data_lines = _required_data_by_question_lines()
    return "\n".join(
        [
            "# SNU-668 Density-History Model Selection Report",
            "",
            "The primary application is `snu668_full_history`; the main controlled ablation is `snu668_published_like_compressed`; the supporting external comparator is `nwaa124_curated_external`.",
            "NSR is a strong publication-level biological comparator, not a weak dataset.",
            "The NSR supplement contains publication-level experimental records sufficient for coarse ecological reconstruction.",
            "CLONEID improves modelability by preserving event linkage, image-derived phenotype, confluence proxies, transfer/bottleneck events, and endpoint Perspective provenance.",
            "The application asks what becomes identifiable automatically, not whether the original paper was correct.",
            "The minimum longitudinal evolution record is a low-cost standard for making future long-term evolution experiments modelable.",
            "",
            "## Central Question",
            "",
            (config or {}).get(
                "scientific_question",
                "Can r/K density adaptation be explained by proliferation-rate differences alone, or does it require density/confluence/spatial interaction terms?",
            ),
            "",
            "## Record-Level Outcome",
            "",
            "- `snu668_full_history`: supports event-aware comparison of `neutral_growth`, `fixed_state_fitness`, and `density_dependent_growth` under mock workflow validation.",
            "- `snu668_published_like_compressed`: preserves group summaries but loses event graph, transfer/reset semantics, and density-history identifiability.",
            "- `nwaa124_curated_external`: supports coarse reconstruction from Supplementary Table 5, Fig. 9, Fig. 10, and model captions/methods, while remaining publication-level rather than event-linked.",
            "",
            "## Observability Profile",
            "",
            *observability_lines,
            "",
            f"History ablation delta from `snu668_full_history` to `snu668_published_like_compressed`: `{ablation_delta}`.",
            "",
            "## Family Comparison",
            "",
            *family_lines,
            "",
            "## Question-Specific Required Data",
            "",
            "The benchmark also asks which low-cost records are necessary for specific mechanistic questions. NSR directly compares r and K populations at publication level; CLONEID adds the native event ledger needed to answer event-history questions automatically and audibly.",
            "",
            *required_data_lines,
            "",
            "## Current Mock Fit Selection",
            "",
            f"- Best CLONEID full mock family under the tested assumptions: `{_best_full_family(cloneid_full_fits)}`",
            "- Endpoint Perspective records were used only as validation/support.",
            "- Identity records were treated as secondary inferred support.",
            "- Transfer/passaging events were represented as schedule resets and excluded from growth-rate fitting.",
            "- Manuscript numerical interpretation requires live read-only CLONEID extraction or an approved frozen SNU-668 snapshot.",
            "",
            "## CLONEID-LTE Low-Cost Fields",
            "",
            "These fields define a low-cost, gold-standard-style minimum record for long-term evolutionary experiments: enough structure to make model discrimination auditable without requiring exhaustive omics at every passage.",
            "",
            *low_cost_lines,
            "",
            "## Guardrails",
            "",
            "- No mechanism proof is claimed.",
            "- HeLa biology is not equated with SNU-668 biology.",
            "- NSR is not criticized; it is used as a strong publication-level comparator.",
            "- Plot-only evidence is not treated as raw numeric data.",
            "- Endpoint Perspective is not used as a growth-fitting target.",
            "- Identity is not used as direct phenotype.",
            "- Transfer/passaging events are not treated as growth intervals.",
            "",
            "## Interpretation",
            "",
            "The application distinguishes biological support from automatic modelability. Publication-level records support reconstruction and interpretation; event-linked CLONEID records make density/confluence history directly queryable and auditable for the tested model families.",
            "",
        ]
    )


def build_manuscript_facing_summary(
    *,
    observability_profile: dict[str, Any] | None,
    history_ablation: dict[str, Any] | None,
    family_comparison: dict[str, Any] | None,
    comparative_identifiability: dict[str, Any] | None,
    config: dict[str, Any] | None,
) -> str:
    observation_lines = [
        f"- `{row['dataset_regime']}`: auditability `{row['auditability_grade']}`, identifiability `{row['identifiability_grade']}`"
        for row in (observability_profile or {}).get("observability_matrix", [])
    ] or ["- Observability matrix was not generated."]
    family_lines = []
    for row in (family_comparison or {}).get("comparison_rows", []):
        if row["dataset_regime"] != "snu668_full_history" and row["family_id"] == "density_dependent_growth":
            family_lines.append(
                f"- `{row['dataset_regime']}` / `density_dependent_growth`: {row['fit_status']}; "
                f"missing `{row['required_inputs_missing'] or 'none'}`"
            )
    if not family_lines:
        family_lines = ["- Density-history loss was not computed."]
    low_cost = (comparative_identifiability or {}).get("low_cost_fields_that_rescue_identifiability", [])
    return "\n".join(
        [
            "# Manuscript-Facing Summary",
            "",
            "## Scientific Question",
            "",
            (config or {}).get(
                "scientific_question",
                "In long-term r/K density selection, can late growth advantage be explained by fixed fitness alone, or is continuous event-linked crowding/confluence history required?",
            ),
            "",
            "## Datasets / Regimes Compared",
            "",
            "- `snu668_full_history`: primary CLONEID event-linked record.",
            "- `snu668_published_like_compressed`: controlled publication-like compression of the same internal record.",
            "- `nwaa124_curated_external`: supporting publication-level NSR comparator.",
            "",
            "## Compared Model Families",
            "",
            "- `neutral_growth`",
            "- `fixed_state_fitness`",
            "- `density_dependent_growth`",
            "",
            "## What Full CLONEID History Supports",
            "",
            "Full history preserves event order, parent-child graph structure, seed/harvest episodes, transfer/reset semantics, event-linked phenotype, confluence proxies, and terminal Perspective support.",
            "",
            "This converts question-specific data needs into a concrete standard: for density-history model discrimination, the necessary low-cost fields are event IDs, parent-child links, timestamps, event type, seeded/harvested counts, vessel area, confluence or areaOccupied proxy, transfer/bottleneck metadata, and endpoint Perspective anchor.",
            "",
            "## What Compressed CLONEID History Loses",
            "",
            f"History ablation delta: `{(history_ablation or {}).get('history_ablation_delta', 'not computed')}`.",
            *family_lines,
            "",
            "## What The External Sparse Dataset Can And Cannot Distinguish",
            "",
            "The NSR supplement supports coarse ecological reconstruction and biological interpretation from publication-level records. It does not provide a native event ledger or event-linked confluence history for automatic density-history model fitting without manual reconstruction or deterministic plot digitization.",
            "",
            "## Low-Cost Fields That Rescue Identifiability",
            "",
            "CLONEID-LTEE can therefore be framed as a low-cost gold-standard-style record for long-term evolutionary experiments: not more data for its own sake, but the minimum event-linked structure needed to answer mechanistic questions reproducibly.",
            "",
            *[f"- {item}" for item in (low_cost or ["event ledger", "event-linked confluence proxy", "terminal Perspective anchor"])],
            "",
            "## Non-Claims / Limitations",
            "",
            "- No mechanism proof is claimed.",
            "- HeLa and SNU-668 biology are not treated as biologically equivalent.",
            "- The NSR paper is not criticized.",
            "- Plot-only evidence is not treated as raw numeric data.",
            "- Endpoint Perspective is validation/support only.",
            "- Identity is inferred secondary support only.",
            "- Transfer/passaging events are not treated as growth intervals.",
            "- Mock numerical values require live read-only CLONEID extraction or an approved frozen SNU-668 snapshot before manuscript interpretation.",
            "",
            "## Observability Matrix",
            "",
            *observation_lines,
            "",
        ]
    )


def build_family_discrimination_summary(family_comparison: dict[str, Any] | None) -> str:
    lines = [
        "# Family Discrimination Summary",
        "",
        "The manuscript-facing comparison asks whether `fixed_state_fitness` can be separated from `density_dependent_growth` only when event-linked history is present.",
        "",
    ]
    by_regime: dict[str, list[dict[str, Any]]] = {}
    for row in (family_comparison or {}).get("comparison_rows", []):
        by_regime.setdefault(row["dataset_regime"], []).append(row)
    for regime in ("snu668_full_history", "snu668_published_like_compressed", "nwaa124_curated_external"):
        lines.append(f"## {regime}")
        rows = {row["family_id"]: row for row in by_regime.get(regime, [])}
        for family_id in ("neutral_growth", "fixed_state_fitness", "density_dependent_growth"):
            row = rows.get(family_id, {})
            if not row:
                lines.append(f"- `{family_id}`: not evaluated.")
                continue
            if row.get("selected_under_tested_assumptions"):
                status = "selected under tested assumptions"
            elif row.get("rejected_under_tested_assumptions"):
                status = "rejected under tested assumptions"
            elif row.get("unresolved_under_available_records"):
                status = "unresolved under available records"
            else:
                status = row.get("fit_status", "not evaluated")
            lines.append(
                f"- `{family_id}`: {status}; missing inputs `{row.get('required_inputs_missing') or 'none'}`."
            )
        lines.append("")
    return "\n".join(lines)


def _required_data_by_question_lines() -> list[str]:
    rows = [
        (
            "Can fixed-state fitness be separated from density-dependent growth?",
            "seed-harvest episodes; elapsed time; seeded/harvested counts; event-linked confluence or areaOccupied; branch labels",
            "supports r/K coarse reconstruction, but event-linked density history is not native",
            "directly auditable from `snu668_full_history` when fields are present",
        ),
        (
            "Are transfer/passaging records growth intervals or schedule resets?",
            "event_type; parent_event_id; seed/harvest/transfer classification",
            "protocol-level reconstruction from methods/captions",
            "explicit event schedule with transfer resets excluded from growth fitting",
        ),
        (
            "Which density exposure preceded the terminal assay?",
            "ordered event graph; cumulative confluence exposure; terminal Perspective origin",
            "not native without manual reconstruction",
            "queryable through Event -> Phenotype -> Perspective linkage",
        ),
        (
            "What is lost when a full experiment is compressed to a paper-like summary?",
            "paired full record and deliberately downsampled record",
            "not applicable as a controlled internal ablation",
            "directly measured by `snu668_full_history` -> `snu668_published_like_compressed`",
        ),
        (
            "Can an agent create an auditable model schedule automatically?",
            "event ledger; transfer semantics; image-derived phenotype provenance; endpoint assay anchor",
            "requires manual reconstruction from publication-level records",
            "agent-ready schedule can be generated from native records",
        ),
    ]
    lines = [
        "| Mechanistic question | Necessary data | NSR publication-level record | CLONEID event-linked record |",
        "|---|---|---|---|",
    ]
    lines.extend(f"| {question} | {needed} | {nsr} | {cloneid} |" for question, needed, nsr, cloneid in rows)
    return lines


def build_required_data_by_question_report() -> str:
    return "\n".join(
        [
            "# Required Data By Question",
            "",
            "This report states the benchmark's practical claim: the necessary data depend on the mechanistic question. NSR provides rich publication-level r/K evidence. CLONEID adds the low-cost event-linked fields that make event-history questions automatically queryable, auditable, and agent-ready.",
            "",
            *_required_data_by_question_lines(),
            "",
            "## Interpretation",
            "",
            "The distinction is not that NSR lacks r/K biology. The distinction is that CLONEID records the experiment as an event-linked object. That structure makes specific questions easier to answer: which observations are growth episodes, which records are transfer resets, which confluence exposure preceded each harvest, and which endpoint Perspective anchors to which upstream event.",
            "",
            "This is the basis for describing CLONEID-LTEE as a low-cost gold-standard-style data standard for long-term evolutionary experiments.",
            "",
        ]
    )


def build_manuscript_insert() -> str:
    return "\n".join(
        [
            "# MANUSCRIPT INSERT",
            "",
            "## Results: Benchmarking CLONEID against publication-level r/K-selection records",
            "",
            "We evaluated the SNU-668 density-history proof-of-principle against a publication-level r/K-selection record from Li et al. NSR 2021. The external supplement provided structured growth-rate samples, growth-model fit statistics, carrying-capacity formulas, mixed-population captions and plots, spatial-model methods, migration evidence, and molecular endpoint records. These records supported coarse ecological reconstruction while retaining clear limits around plot-only evidence and absent event linkage.",
            "",
            "In the CLONEID native SNU-668 record, seed, harvest, transfer, image-derived phenotype, confluence proxy, and endpoint Perspective records were preserved as linked events. This event graph allowed neutral growth, fixed-state fitness, and density-dependent growth families to be evaluated with explicit separation of biological growth episodes from passaging resets. Downsampling the native record to publication-level summaries removed the parent-child graph, per-event density, image provenance, and Perspective-event linkage, making density/confluence model families not identifiable from the coarse record.",
            "",
            "## Methods",
            "",
            "Docx/txt/vcf extraction was performed by listing the archive, classifying document types, extracting docx paragraphs and tables, and exporting embedded media into an audit folder. Supplementary figure captions were indexed, Supplementary Tables 1, 2, 3, 5, and 6 were exported as CSV when present, and model formulas or reported fit statistics were parsed from captions and methods text.",
            "",
            "Publication-level reconstruction used Supplementary Table 5 growth-rate samples, Supplementary Fig. 9 reported R-squared values, Supplementary Fig. 10 logistic carrying-capacity formulas, and mixed-population plot captions. Plot-only trajectories were retained as evidence requiring deterministic digitization before curve fitting.",
            "",
            "CLONEID native modeling used seed-to-harvest growth episodes, transfer/bottleneck schedule events, image-derived occupied area and cell size, confluence proxy, and endpoint Perspective provenance. CLONEID downsampling removed event IDs, parent-child event graph, individual seed/harvest/transfer records, per-event image provenance, per-event confluence, and Perspective-event linkage.",
            "",
            "The modelability audit assigned controlled record-status labels across `snu668_full_history`, `snu668_published_like_compressed`, and `nwaa124_curated_external`. Model families were evaluated as identifiable, summary-only identifiable, publication-level reconstruction only, or not identifiable due to missing event-level density or event graph.",
            "",
            "## Figure Caption",
            "",
            "Figure X. SNU-668 density-history proof-of-principle. The full CLONEID regime preserves seed-harvest-transfer event linkage, image-derived phenotype, confluence proxy, and endpoint Perspective provenance. The compressed SNU-668 regime removes those links to mimic a publication-like sparse view. The external NSR supplement supports coarse reconstruction through structured tables, captions, model formulas, and methods text, and acts as a supporting observability comparator.",
            "",
            "## Nature Methods Significance",
            "",
            "This application reframes long-term evolution datasets as agent-ready model inputs. Rather than judging a prior publication, it asks which biological hypotheses become automatically testable when routine passaging, imaging, and endpoint assay records are linked by event identifiers. CLONEID-LTEE provides a practical low-cost gold-standard-style minimum record for transforming culture records into auditable schedules for mechanistic modeling.",
            "",
            "## Limitations",
            "",
            "The NSR reconstruction is limited by publication-level granularity and by plot-only mixed-population trajectories unless deterministic digitization is added. The CLONEID mock run demonstrates the workflow without live database access; manuscript numerical interpretation requires live read-only CLONEID extraction or an approved frozen SNU-668 snapshot. HeLa biology is not equated with SNU-668 biology, and endpoint Perspective records remain validation/support rather than growth-fitting targets.",
            "",
        ]
    )


def write_rk_benchmark_reports(
    output_dir: str | Path,
    *,
    nsr_fits: dict[str, Any],
    cloneid_full_fits: dict[str, Any],
    cloneid_coarse_fits: dict[str, Any],
    comparison_rows: list[dict[str, Any]],
    observability_profile: dict[str, Any] | None = None,
    history_ablation: dict[str, Any] | None = None,
    family_comparison: dict[str, Any] | None = None,
    comparative_identifiability: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Path]:
    output = Path(output_dir)
    report = build_model_selection_report(
        nsr_fits=nsr_fits,
        cloneid_full_fits=cloneid_full_fits,
        cloneid_coarse_fits=cloneid_coarse_fits,
        comparison_rows=comparison_rows,
        observability_profile=observability_profile,
        history_ablation=history_ablation,
        family_comparison=family_comparison,
        comparative_identifiability=comparative_identifiability,
        config=config,
    )
    for term in FORBIDDEN_OVERCLAIM_TERMS:
        pattern = rf"\b{re.escape(term.lower())}\b"
        if re.search(pattern, report.lower()):
            raise ValueError(f"Forbidden overclaim term found in report: {term}")
    manuscript = build_manuscript_insert()
    for term in FORBIDDEN_OVERCLAIM_TERMS:
        pattern = rf"\b{re.escape(term.lower())}\b"
        if re.search(pattern, manuscript.lower()):
            raise ValueError(f"Forbidden overclaim term found in manuscript insert: {term}")
    return {
        "model_selection_report": write_markdown(output / "model_selection_report.md", report),
        "manuscript_insert": write_markdown(output / "MANUSCRIPT_INSERT.md", manuscript),
        "required_data_by_question": write_markdown(
            output / "required_data_by_question.md",
            build_required_data_by_question_report(),
        ),
        "manuscript_facing_summary": write_markdown(
            output / "manuscript_facing_summary.md",
            build_manuscript_facing_summary(
                observability_profile=observability_profile,
                history_ablation=history_ablation,
                family_comparison=family_comparison,
                comparative_identifiability=comparative_identifiability,
                config=config,
            ),
        ),
        "family_discrimination_summary": write_markdown(
            output / "family_discrimination_summary.md",
            build_family_discrimination_summary(family_comparison),
        ),
    }
