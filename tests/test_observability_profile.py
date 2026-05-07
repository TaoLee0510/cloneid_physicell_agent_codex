from __future__ import annotations

import unittest
from pathlib import Path

from cloneid_agent.compressed_view import build_published_like_compressed_view
from cloneid_agent.external_curated_adapter import load_external_curated_dataset
from cloneid_agent.history_covariates import build_dry_run_snu668_fixture, build_history_covariates
from cloneid_agent.observability_profile import build_observability_profile


REPO_ROOT = Path(__file__).resolve().parents[1]


class ObservabilityProfileTests(unittest.TestCase):
    def test_observability_grades_full_history_above_sparse_views(self) -> None:
        dataset = build_dry_run_snu668_fixture()
        covariates = build_history_covariates(dataset)
        compressed = build_published_like_compressed_view(dataset, covariates)
        external = load_external_curated_dataset(REPO_ROOT / "data/external/nwaa124_curated")
        payload = build_observability_profile(
            history_covariates=covariates,
            compressed_view=compressed,
            external_comparator=external,
        )
        rows = {row["dataset_regime"]: row for row in payload["observability_matrix"]}
        self.assertEqual(rows["snu668_full_history"]["auditability_grade"], "A")
        self.assertFalse(rows["snu668_published_like_compressed"]["continuous_density_history"])
        self.assertFalse(rows["nwaa124_curated_external"]["exact_time_series_points"])


if __name__ == "__main__":
    unittest.main()
