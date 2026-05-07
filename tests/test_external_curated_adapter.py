from __future__ import annotations

import unittest
from pathlib import Path

from cloneid_agent.external_curated_adapter import load_external_curated_dataset


REPO_ROOT = Path(__file__).resolve().parents[1]


class ExternalCuratedAdapterTests(unittest.TestCase):
    def test_load_curated_external_comparator_records_missingness(self) -> None:
        dataset = load_external_curated_dataset(REPO_ROOT / "data/external/nwaa124_curated")
        self.assertEqual(dataset["dataset_regime"], "nwaa124_curated_external")
        self.assertTrue(dataset["table_status"]["competition_over_time.csv"]["present"])
        self.assertGreater(len(dataset["records"]), 10)
        self.assertFalse(dataset["observability_flags"]["event_linked_history"])
        self.assertIn("no CLONEID-style event_id / parent_event_id ledger", dataset["missingness"]["dataset_level_missingness"])
        self.assertTrue(any("continuous density history" in item for item in dataset["unsupported_assumptions"]))


if __name__ == "__main__":
    unittest.main()
