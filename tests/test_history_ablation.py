from __future__ import annotations

import unittest

from cloneid_agent.compressed_view import build_published_like_compressed_view
from cloneid_agent.history_ablation import build_history_ablation
from cloneid_agent.history_covariates import build_dry_run_snu668_fixture, build_history_covariates


class HistoryAblationTests(unittest.TestCase):
    def test_historyless_condition_removes_density_and_transfer_inputs(self) -> None:
        dataset = build_dry_run_snu668_fixture()
        covariates = build_history_covariates(dataset)
        compressed = build_published_like_compressed_view(dataset, covariates)
        ablation = build_history_ablation(covariates, compressed)
        self.assertEqual([item["condition_id"] for item in ablation["paired_conditions"]], ["full_history", "historyless_or_passage_only"])
        historyless = ablation["paired_conditions"][1]
        self.assertIn("cumulative confluence / crowding history", historyless["removed_inputs"])
        self.assertGreater(ablation["history_ablation_delta"], 0)


if __name__ == "__main__":
    unittest.main()
