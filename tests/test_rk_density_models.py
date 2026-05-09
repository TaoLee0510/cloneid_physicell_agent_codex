from __future__ import annotations

import unittest

from cloneid_agent.rk_density_models import NOT_IDENTIFIABLE_DENSITY, fit_cloneid_coarse_models, fit_cloneid_full_models
from cloneid_agent.rk_downsampling import build_growth_episode_table, build_mock_cloneid_full_record, downsample_cloneid_record


class RkDensityModelsTests(unittest.TestCase):
    def test_full_cloneid_mock_supports_density_model_fitting(self) -> None:
        full = build_mock_cloneid_full_record("auto")
        episodes = build_growth_episode_table(full["passaging_records"])
        fits = fit_cloneid_full_models(episodes)
        models = {row["family_id"]: row for row in fits["models"]}
        self.assertEqual(models["density_dependent_growth"]["fit_status"], "identifiable")
        self.assertEqual(models["density_plus_branch_optional"]["fit_status"], "identifiable")
        self.assertEqual(fits["best_supported_family"], "density_plus_branch_optional")

    def test_coarse_record_marks_density_models_not_identifiable(self) -> None:
        full = build_mock_cloneid_full_record("auto")
        coarse = downsample_cloneid_record(full)
        fits = fit_cloneid_coarse_models(coarse)
        models = {row["family_id"]: row for row in fits["models"]}
        self.assertEqual(models["density_dependent_growth"]["fit_status"], NOT_IDENTIFIABLE_DENSITY)
        self.assertEqual(models["density_plus_branch_optional"]["fit_status"], NOT_IDENTIFIABLE_DENSITY)


if __name__ == "__main__":
    unittest.main()
