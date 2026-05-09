from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cloneid_agent.compressed_view import build_published_like_compressed_view
from cloneid_agent.history_covariates import build_dry_run_snu668_fixture, build_history_covariates
from cloneid_agent.observability_profile import OBSERVABILITY_DIMENSIONS, build_observability_profile, write_observability_profile
from cloneid_agent.rk_downsampling import downsample_cloneid_record
from cloneid_agent.rk_publication_record_extraction import extract_nwaa124_publication_record

from rk_fixture_utils import make_nwaa124_fixture_zip


class ObservabilityProfileTests(unittest.TestCase):
    def test_observability_grades_full_history_above_sparse_views(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            nsr = extract_nwaa124_publication_record(make_nwaa124_fixture_zip(tmp), tmp / "external")
            full = build_dry_run_snu668_fixture()
            covariates = build_history_covariates(full)
            compressed = build_published_like_compressed_view(full, covariates, downsample_cloneid_record(full))
            payload = build_observability_profile(
                nsr_record=nsr,
                history_covariates=covariates,
                compressed_view=compressed,
            )
            rows = {row["dataset_regime"]: row for row in payload["observability_matrix"]}
            self.assertEqual(rows["snu668_full_history"]["auditability_grade"], "A")
            self.assertEqual(rows["snu668_full_history"]["continuous_density_history"], "available")
            self.assertEqual(
                rows["snu668_published_like_compressed"]["continuous_density_history"],
                "not_available_in_archive",
            )
            self.assertEqual(rows["nwaa124_curated_external"]["event_linked_history"], "not_event_linked")
            self.assertTrue(set(OBSERVABILITY_DIMENSIONS).issubset(set(payload["dimensions"])))

    def test_write_observability_profile_outputs_required_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            nsr = extract_nwaa124_publication_record(make_nwaa124_fixture_zip(tmp), tmp / "external")
            full = build_dry_run_snu668_fixture()
            covariates = build_history_covariates(full)
            compressed = build_published_like_compressed_view(full, covariates, downsample_cloneid_record(full))
            payload = build_observability_profile(
                nsr_record=nsr,
                history_covariates=covariates,
                compressed_view=compressed,
            )
            paths = write_observability_profile(tmp / "out", payload)
            self.assertTrue(paths["json"].exists())
            self.assertTrue(paths["csv"].exists())
            self.assertTrue(paths["matrix_json"].exists())
            self.assertTrue(paths["matrix_csv"].exists())
            self.assertTrue(paths["dataset_missingness"].exists())
            self.assertIn("identifiability_grade", paths["csv"].read_text())


if __name__ == "__main__":
    unittest.main()
