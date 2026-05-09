from __future__ import annotations

import unittest

from cloneid_agent.compressed_view import build_published_like_compressed_view
from cloneid_agent.history_ablation import build_history_ablation
from cloneid_agent.history_covariates import build_dry_run_snu668_fixture, build_history_covariates
from cloneid_agent.rk_density_models import fit_cloneid_coarse_models, fit_cloneid_full_models
from cloneid_agent.rk_downsampling import build_growth_episode_table, downsample_cloneid_record


class HistoryAblationTests(unittest.TestCase):
    def test_downsampled_condition_removes_density_and_transfer_inputs(self) -> None:
        full = build_dry_run_snu668_fixture()
        covariates = build_history_covariates(full)
        coarse = downsample_cloneid_record(full)
        compressed = build_published_like_compressed_view(full, covariates, coarse)
        ablation = build_history_ablation(
            covariates,
            compressed,
            cloneid_full_fits=fit_cloneid_full_models(build_growth_episode_table(full["passaging_records"])),
            cloneid_coarse_fits=fit_cloneid_coarse_models(coarse),
        )
        self.assertEqual(
            [item["condition_id"] for item in ablation["paired_conditions"]],
            ["full_native_record", "publication_level_downsampled_record"],
        )
        historyless = ablation["paired_conditions"][1]
        self.assertIn("per-event confluence", historyless["removed_inputs"])
        self.assertGreater(ablation["history_ablation_delta"], 0)
        density_effect = next(
            item for item in ablation["model_family_effects"] if item["family_id"] == "density_dependent_growth"
        )
        self.assertIn("not identifiable from coarse records", density_effect["effect_of_downsampling"])


if __name__ == "__main__":
    unittest.main()
