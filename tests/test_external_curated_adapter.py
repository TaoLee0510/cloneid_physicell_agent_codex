from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cloneid_agent.external_curated_adapter import load_external_curated_dataset, publication_level_external_stub


class ExternalCuratedAdapterTests(unittest.TestCase):
    def test_missing_curated_root_returns_publication_level_stub(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            dataset = load_external_curated_dataset(Path(tmpdir) / "absent")
            self.assertEqual(dataset["dataset_regime"], "nwaa124_curated_external")
            self.assertFalse(dataset["observability_flags"]["event_linked_history"])
            self.assertIn(
                "no CLONEID-style event_id / parent_event_id ledger",
                dataset["missingness"]["dataset_level_missingness"],
            )

    def test_publication_level_stub_records_unsupported_assumptions(self) -> None:
        dataset = publication_level_external_stub()
        self.assertTrue(
            any("continuous density history" in item for item in dataset["unsupported_assumptions"])
        )
        self.assertTrue(
            any("Embedded plots" in item or "embedded plots" in item for item in dataset["unsupported_assumptions"])
        )


if __name__ == "__main__":
    unittest.main()
