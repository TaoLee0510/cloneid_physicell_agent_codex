from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cloneid_agent.history_covariates import (
    build_dry_run_snu668_fixture,
    build_history_covariates,
    write_history_covariates,
)


class HistoryCovariatesTests(unittest.TestCase):
    def test_build_history_covariates_preserves_event_history_and_transfer_resets(self) -> None:
        dataset = build_dry_run_snu668_fixture()
        payload = build_history_covariates(dataset)
        self.assertEqual(payload["dataset_regime"], "CLONEID_full_native_record")
        self.assertGreaterEqual(payload["summary"]["event_count"], 8)
        self.assertGreaterEqual(payload["summary"]["transfer_reset_count"], 2)
        self.assertTrue(payload["summary"]["has_cumulative_density_history_proxy"])
        first_reset = next(row for row in payload["covariate_rows"] if row["transfer_reset_semantics"])
        self.assertEqual(first_reset["event_type"], "seeding")
        self.assertIn("cumulative_confluence_exposure_before_event", first_reset)

    def test_write_history_covariates_outputs_json_md_and_csv(self) -> None:
        payload = build_history_covariates(build_dry_run_snu668_fixture())
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = write_history_covariates(tmpdir, payload)
            self.assertTrue(paths["json"].exists())
            self.assertTrue(paths["md"].exists())
            self.assertTrue(paths["csv"].exists())
            self.assertIn("transfer_reset_semantics", Path(paths["csv"]).read_text())


if __name__ == "__main__":
    unittest.main()
