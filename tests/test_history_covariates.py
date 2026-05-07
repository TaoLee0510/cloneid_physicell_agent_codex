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
        self.assertEqual(payload["dataset_regime"], "snu668_full_history")
        self.assertEqual(payload["summary"]["event_count"], 8)
        self.assertGreaterEqual(payload["summary"]["transfer_reset_count"], 3)
        self.assertTrue(payload["summary"]["has_cumulative_crowding_history_proxy"])
        first_reset = next(row for row in payload["covariate_rows"] if row["transfer_reset_semantics"])
        self.assertEqual(first_reset["event_type"], "seeding")

    def test_write_history_covariates_outputs_json_md_and_csv(self) -> None:
        payload = build_history_covariates(build_dry_run_snu668_fixture())
        with tempfile.TemporaryDirectory() as tmpdir:
            write_history_covariates(tmpdir, payload)
            self.assertTrue((Path(tmpdir) / "history_covariates.json").exists())
            self.assertTrue((Path(tmpdir) / "history_covariates.md").exists())
            self.assertTrue((Path(tmpdir) / "history_covariates.csv").exists())


if __name__ == "__main__":
    unittest.main()
