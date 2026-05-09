from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from cloneid_agent.cloneid_lte_standard import BRONZE_FIELDS, GOLD_FIELDS, SILVER_FIELDS, build_cloneid_lte_schema, write_cloneid_lte_standard


class CloneidLteStandardTests(unittest.TestCase):
    def test_schema_contains_required_tiers(self) -> None:
        schema = build_cloneid_lte_schema()
        self.assertEqual(schema["tiers"]["Bronze"], BRONZE_FIELDS)
        self.assertEqual(schema["tiers"]["Silver"], SILVER_FIELDS)
        self.assertEqual(schema["tiers"]["Gold"], GOLD_FIELDS)
        self.assertIn("event_graph.json", schema["tiers"]["Platinum"])

    def test_standard_artifacts_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            paths = write_cloneid_lte_standard(Path(tmpdir))
            self.assertTrue(paths["standard_md"].exists())
            self.assertTrue(paths["schema_json"].exists())
            with paths["event_template_csv"].open(newline="") as handle:
                header = next(csv.reader(handle))
            self.assertIn("event_id", header)
            self.assertIn("confluence_proxy", header)
            self.assertIn("Perspective_id", header)


if __name__ == "__main__":
    unittest.main()
