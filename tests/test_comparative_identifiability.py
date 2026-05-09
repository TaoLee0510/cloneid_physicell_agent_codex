from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cloneid_agent.comparative_identifiability import build_comparative_identifiability
from cloneid_agent.compressed_view import build_published_like_compressed_view
from cloneid_agent.family_comparison import build_family_comparison
from cloneid_agent.history_ablation import build_history_ablation
from cloneid_agent.history_covariates import build_dry_run_snu668_fixture, build_history_covariates
from cloneid_agent.observability_profile import build_observability_profile
from cloneid_agent.rk_density_models import fit_cloneid_coarse_models, fit_cloneid_full_models, fit_nsr_reconstructed_models
from cloneid_agent.rk_downsampling import build_growth_episode_table, downsample_cloneid_record
from cloneid_agent.rk_publication_record_extraction import extract_nwaa124_publication_record

from rk_fixture_utils import make_nwaa124_fixture_zip


class ComparativeIdentifiabilityTests(unittest.TestCase):
    def test_identifiability_marks_sparse_regimes_unresolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            nsr = extract_nwaa124_publication_record(make_nwaa124_fixture_zip(tmp), tmp / "external")
            full = build_dry_run_snu668_fixture()
            episodes = build_growth_episode_table(full["passaging_records"])
            coarse = downsample_cloneid_record(full)
            covariates = build_history_covariates(full)
            compressed = build_published_like_compressed_view(full, covariates, coarse)
            ablation = build_history_ablation(covariates, compressed)
            observability = build_observability_profile(
                nsr_record=nsr,
                history_covariates=covariates,
                compressed_view=compressed,
            )
            comparison = build_family_comparison(
                observability_profile=observability,
                nsr_fits=fit_nsr_reconstructed_models(nsr),
                cloneid_full_fits=fit_cloneid_full_models(episodes),
                cloneid_coarse_fits=fit_cloneid_coarse_models(coarse),
            )
            identifiability = build_comparative_identifiability(
                observability_profile=observability,
                family_comparison=comparison,
                history_ablation=ablation,
            )
            summaries = {item["dataset_regime"]: item for item in identifiability["summaries"]}
            self.assertIn(
                "partially unresolved",
                summaries["snu668_published_like_compressed"]["resolution_statement"],
            )
            self.assertIn(
                "unresolved",
                summaries["nwaa124_curated_external"]["resolution_statement"],
            )
            self.assertIn(
                "event_id and parent_event_id ledger",
                identifiability["low_cost_fields_that_rescue_identifiability"],
            )


if __name__ == "__main__":
    unittest.main()
