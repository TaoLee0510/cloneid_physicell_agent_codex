from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cloneid_agent.compressed_view import build_published_like_compressed_view
from cloneid_agent.family_comparison import build_family_comparison, write_family_comparison
from cloneid_agent.history_ablation import build_history_ablation
from cloneid_agent.history_covariates import build_dry_run_snu668_fixture, build_history_covariates
from cloneid_agent.observability_profile import build_observability_profile
from cloneid_agent.rejection_logging import render_rejection_report
from cloneid_agent.rk_density_models import fit_cloneid_coarse_models, fit_cloneid_full_models, fit_nsr_reconstructed_models
from cloneid_agent.rk_downsampling import build_growth_episode_table, downsample_cloneid_record
from cloneid_agent.rk_publication_record_extraction import extract_nwaa124_publication_record

from rk_fixture_utils import make_nwaa124_fixture_zip


def _strong_observability_profile() -> dict:
    base = {
        "event_linked_history": "available",
        "parent_child_event_graph": "available",
        "seed_harvest_transfer_classification": "available",
        "continuous_density_history": "available",
        "image_derived_phenotype": "structured_numeric_table",
        "confluence_proxy": "structured_numeric_table",
        "endpoint_perspective_support": "available",
        "molecular_assay_event_linkage": "available",
        "exact_time_series_points": "available",
        "raw_image_or_segmentation_provenance": "available",
        "agent_ready_schedule": "agent_ready",
        "physiCell_mapping_possible": "available",
        "auditability_grade": "A",
        "identifiability_grade": "strong",
        "missing_data_warnings": "",
        "unsupported_assumptions": "",
        "low_cost_fields_that_would_rescue_identifiability": "",
    }
    return {
        "observability_matrix": [
            {"dataset_regime": "snu668_full_history", **base},
            {"dataset_regime": "snu668_published_like_compressed", **base},
            {"dataset_regime": "nwaa124_curated_external", **base},
        ]
    }


def _identifiable_fits(best_family: str | None = None) -> dict:
    return {
        "models": [
            {"family_id": "context_blind_null", "fit_status": "identifiable", "rmse": 3.0, "aic": 30.0},
            {"family_id": "branch_specific_fitness", "fit_status": "identifiable", "rmse": 2.0, "aic": 20.0},
            {"family_id": "density_dependent_growth", "fit_status": "identifiable", "rmse": 1.0, "aic": 10.0},
        ],
        "best_supported_family": best_family,
    }


class FamilyComparisonEvidenceTests(unittest.TestCase):
    def test_non_full_density_family_is_not_unresolved_when_evidence_is_strong(self) -> None:
        comparison = build_family_comparison(
            observability_profile=_strong_observability_profile(),
            nsr_fits=_identifiable_fits("density_dependent_growth"),
            cloneid_full_fits=_identifiable_fits(None),
            cloneid_coarse_fits=_identifiable_fits(None),
        )
        row = next(
            item
            for item in comparison["comparison_rows"]
            if item["dataset_regime"] == "nwaa124_curated_external"
            and item["family_id"] == "density_dependent_growth"
        )
        self.assertFalse(row["unresolved_under_available_records"])
        self.assertTrue(row["identifiable"])
        self.assertEqual(row["decision_status"], "selected under tested assumptions")
        self.assertEqual(row["missing_required_input_count"], 0)
        self.assertIn("fit `identifiable`", row["status_decision_basis"])

    def test_sparse_density_family_remains_unresolved_for_evidence_reasons(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            nsr = extract_nwaa124_publication_record(make_nwaa124_fixture_zip(tmp), tmp / "external")
            full = build_dry_run_snu668_fixture()
            episodes = build_growth_episode_table(full["passaging_records"])
            coarse = downsample_cloneid_record(full)
            covariates = build_history_covariates(full)
            compressed = build_published_like_compressed_view(full, covariates, coarse)
            full_fits = fit_cloneid_full_models(episodes)
            coarse_fits = fit_cloneid_coarse_models(coarse)
            ablation = build_history_ablation(
                covariates,
                compressed,
                cloneid_full_fits=full_fits,
                cloneid_coarse_fits=coarse_fits,
            )
            comparison = build_family_comparison(
                observability_profile=build_observability_profile(
                    nsr_record=nsr,
                    history_covariates=covariates,
                    compressed_view=compressed,
                ),
                nsr_fits=fit_nsr_reconstructed_models(nsr),
                cloneid_full_fits=full_fits,
                cloneid_coarse_fits=coarse_fits,
                history_ablation=ablation,
            )
            row = next(
                item
                for item in comparison["comparison_rows"]
                if item["dataset_regime"] == "snu668_published_like_compressed"
                and item["family_id"] == "density_dependent_growth"
            )
            self.assertTrue(row["unresolved_under_available_records"])
            self.assertEqual(row["decision_status"], "not identifiable due to missing required inputs")
            self.assertGreater(row["missing_required_input_count"], 0)
            self.assertIn("missing required inputs", row["dominant_limitation"])
            self.assertIn("event-level density", row["family_downsampling_effect"])
            self.assertNotIn("not full history", row["status_decision_basis"].lower())

    def test_full_history_is_not_automatically_selected_when_evidence_is_poor(self) -> None:
        weak = _strong_observability_profile()
        for row in weak["observability_matrix"]:
            if row["dataset_regime"] == "snu668_full_history":
                row["auditability_grade"] = "D"
                row["identifiability_grade"] = "poor"
                row["missing_data_warnings"] = "synthetic weak observability"
        comparison = build_family_comparison(
            observability_profile=weak,
            nsr_fits=_identifiable_fits(None),
            cloneid_full_fits=_identifiable_fits("density_dependent_growth"),
            cloneid_coarse_fits=_identifiable_fits(None),
        )
        row = next(
            item
            for item in comparison["comparison_rows"]
            if item["dataset_regime"] == "snu668_full_history"
            and item["family_id"] == "density_dependent_growth"
        )
        self.assertFalse(row["selected_under_tested_assumptions"])
        self.assertEqual(row["decision_status"], "unresolved under available records")
        self.assertIn("observability support `0`", row["status_decision_basis"])

    def test_markdown_and_rejection_reports_include_decision_basis(self) -> None:
        comparison = build_family_comparison(
            observability_profile=_strong_observability_profile(),
            nsr_fits=_identifiable_fits("density_dependent_growth"),
            cloneid_full_fits=_identifiable_fits(None),
            cloneid_coarse_fits=_identifiable_fits(None),
        )
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = write_family_comparison(tmpdir, comparison)
            markdown = paths["md"].read_text()
        rejection = render_rejection_report(comparison)
        self.assertIn("basis:", markdown)
        self.assertIn("Decision basis:", rejection)
        self.assertIn("Dominant limitation:", rejection)


if __name__ == "__main__":
    unittest.main()
