from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cloneid_agent.schemas import DatabaseInventory


REPO_ROOT = Path(__file__).resolve().parents[1]


class SchemaTests(unittest.TestCase):
    def _make_mock_inventory(self) -> Path:
        tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(tmpdir.cleanup)
        outdir = Path(tmpdir.name)
        result = subprocess.run(
            [
                "Rscript",
                "scripts/cloneid_inventory.R",
                "--mode",
                "mock",
                "--output",
                str(outdir),
            ],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        return outdir / "database_inventory.json"

    def test_database_inventory_schema_accepts_mock_output(self) -> None:
        inventory_path = self._make_mock_inventory()
        inventory = DatabaseInventory.from_json_file(inventory_path)
        self.assertEqual(inventory.mode_used, "mock")
        self.assertEqual(inventory.table_count, len(inventory.tables))
        self.assertIn("Passaging", inventory.fields)
        self.assertIn("Passaging", inventory.key_table_summaries)

    def test_database_inventory_schema_rejects_missing_key_summary(self) -> None:
        inventory_path = self._make_mock_inventory()
        payload = json.loads(inventory_path.read_text())
        del payload["key_table_summaries"]["Passaging"]
        with self.assertRaises(ValueError):
            DatabaseInventory.from_dict(payload)

    def test_database_inventory_schema_rejects_bad_table_count(self) -> None:
        inventory_path = self._make_mock_inventory()
        payload = json.loads(inventory_path.read_text())
        payload["table_count"] = payload["table_count"] + 1
        with self.assertRaises(ValueError):
            DatabaseInventory.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
