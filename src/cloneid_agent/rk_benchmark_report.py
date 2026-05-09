"""Markdown reports for the CLONEID-LTE r/K benchmark."""

from __future__ import annotations

from pathlib import Path
import re
from typing import Any

from .run_io import write_markdown


FORBIDDEN_OVERCLAIM_TERMS = (
    "proves",
    "discovers the true mechanism",
    "establishes causality",
    "NSR data are bad",
    "NSR paper is flawed",
    "HeLa and SNU-668 are biologically equivalent",
)


def _best_full_family(cloneid_full_fits: dict[str, Any]) -> str:
    return cloneid_full_fits.get("best_supported_family") or "not selected"


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
    density_rows = [
        row
        for row in comparison_rows
        if row["family_id"] in {"density_dependent_growth", "density_plus_branch_optional"}
    ]
    density_lines = [
        f"- `{row['family_id']}`: NSR `{row['NSR_publication_level_reconstructed_record_fit_status']}`, "
        f"CLONEID full `{row['CLONEID_full_native_record_fit_status']}`, "
        f"CLONEID coarse `{row['CLONEID_publication_level_downsampled_record_fit_status']}`"
        for row in density_rows
    ]
    family_lines = []
    for row in (family_comparison or {}).get("comparison_rows", []):
        if row["family_id"] not in {"branch_specific_fitness", "density_dependent_growth", "density_plus_branch_optional"}:
            continue
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
    return "\n".join(
        [
            "# CLONEID-LTE r/K Benchmark Model Selection Report",
            "",
            "NSR is a strong biological comparator, not a weak dataset.",
            "The NSR supplement contains publication-level experimental records sufficient for coarse model reconstruction.",
            "CLONEID improves agent readiness by preserving event linkage, image-derived phenotype, confluence proxies, transfer/bottleneck events, and endpoint Perspective provenance.",
            "The benchmark asks what becomes identifiable automatically, not whether the original paper was correct.",
            "CLONEID-LTE is a low-cost standard for making future long-term evolution experiments modelable.",
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
            "- NSR reconstructed record: supports coarse summaries from Supplementary Table 5, Fig. 9, Fig. 10, and model captions/methods.",
            "- CLONEID full native record: supports event-aware fitting of proliferation, branch-specific, and density/confluence models.",
            "- CLONEID publication-level downsampled record: preserves group summaries but loses event graph and density identifiability.",
            "",
            "## Observability Profile",
            "",
            *observability_lines,
            "",
            f"History ablation delta from full native record to publication-level downsampled record: `{ablation_delta}`.",
            "",
            "## Density Model Identifiability",
            "",
            *density_lines,
            "",
            "## Family Comparison",
            "",
            *family_lines,
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
            "The application distinguishes biological support from automatic modelability. Publication-level records support reconstruction and interpretation; event-linked CLONEID records make density/confluence terms directly queryable and auditable as benchmark objects.",
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
            "We benchmarked CLONEID-LTE against the publication-level r/K-selection record from Li et al. NSR 2021. The external supplement provided structured growth-rate samples, growth-model fit statistics, carrying-capacity formulas, mixed-population captions and plots, spatial-model methods, migration evidence, and molecular endpoint records. These records supported coarse ecological reconstruction while retaining clear limits around plot-only evidence and absent event linkage.",
            "",
            "In the CLONEID native SNU-668 record, seed, harvest, transfer, image-derived phenotype, confluence proxy, and endpoint Perspective records were preserved as linked events. This event graph allowed the same model families to be evaluated with explicit separation of biological growth episodes from passaging resets. Downsampling the native record to publication-level summaries removed the parent-child graph, per-event density, image provenance, and Perspective-event linkage, making density/confluence model families not identifiable from the coarse record.",
            "",
            "## Methods",
            "",
            "Docx/txt/vcf extraction was performed by listing the archive, classifying document types, extracting docx paragraphs and tables, and exporting embedded media into an audit folder. Supplementary figure captions were indexed, Supplementary Tables 1, 2, 3, 5, and 6 were exported as CSV when present, and model formulas or reported fit statistics were parsed from captions and methods text.",
            "",
            "Publication-level reconstruction used Supplementary Table 5 growth-rate samples, Supplementary Fig. 9 reported R-squared values, Supplementary Fig. 10 logistic carrying-capacity formulas, and mixed-population plot captions. Plot-only trajectories were retained as evidence requiring deterministic digitization before curve fitting.",
            "",
            "CLONEID native modeling used seed-to-harvest growth episodes, transfer/bottleneck schedule events, image-derived occupied area and cell size, confluence proxy, and endpoint Perspective provenance. CLONEID downsampling removed event IDs, parent-child event graph, individual seed/harvest/transfer records, per-event image provenance, per-event confluence, and Perspective-event linkage.",
            "",
            "The modelability audit assigned controlled record-status labels across NSR reconstructed records, CLONEID full native records, and CLONEID publication-level downsampled records. Model families were evaluated as identifiable, summary-only identifiable, publication-level reconstruction only, or not identifiable due to missing event-level density or event graph.",
            "",
            "## Figure Caption",
            "",
            "Figure X. CLONEID-LTE r/K benchmark from publication-level records to event-linked model inputs. The external NSR supplement supports coarse reconstruction through structured tables, captions, model formulas, and methods text. CLONEID native records preserve seed-harvest-transfer event linkage, image-derived phenotype, confluence proxy, and endpoint Perspective provenance, enabling density/confluence model families to be evaluated automatically. Downsampling CLONEID to publication-level summaries shows which modeling claims remain identifiable after event linkage is removed.",
            "",
            "## Nature Methods Significance",
            "",
            "This benchmark reframes long-term evolution datasets as agent-ready model inputs. Rather than judging a prior publication, it asks which biological hypotheses become automatically testable when routine passaging, imaging, and endpoint assay records are linked by event identifiers. CLONEID-LTE provides a practical minimum standard for transforming low-cost culture records into auditable schedules for mechanistic modeling.",
            "",
            "## Limitations",
            "",
            "The NSR reconstruction is limited by publication-level granularity and by plot-only mixed-population trajectories unless deterministic digitization is added. The CLONEID mock run demonstrates the benchmark workflow without live database access; manuscript numerical interpretation requires live read-only CLONEID extraction or an approved frozen SNU-668 snapshot. HeLa biology is not equated with SNU-668 biology, and endpoint Perspective records remain validation/support rather than growth-fitting targets.",
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
    }
