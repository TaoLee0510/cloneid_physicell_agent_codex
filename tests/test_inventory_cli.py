from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHONPATH = str(REPO_ROOT / "src")


def run_command(cmd: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    merged_env["PYTHONPATH"] = PYTHONPATH
    if env:
        merged_env.update(env)
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        env=merged_env,
    )


class InventoryCliTests(unittest.TestCase):
    def test_mock_inventory_json_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_command(
                [
                    sys.executable,
                    "-m",
                    "cloneid_agent",
                    "inventory",
                    "--mode",
                    "mock",
                    "--output",
                    tmpdir,
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            inventory_path = Path(tmpdir) / "database_inventory.json"
            self.assertTrue(inventory_path.exists())

            payload = json.loads(inventory_path.read_text())
            self.assertEqual(payload["mode_used"], "mock")
            self.assertIn("tables", payload)
            self.assertIn("row_counts", payload)
            self.assertIn("fields", payload)
            self.assertIn("key_table_summaries", payload)
            self.assertIn("Passaging", payload["key_table_summaries"])
            self.assertIn("QuPathEvaluation", payload["key_table_summaries"])
            self.assertIn("Perspective", payload["key_table_summaries"])
            self.assertIn("Identity", payload["key_table_summaries"])

    def test_graceful_failure_falls_back_to_mock(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_command(
                [
                    "Rscript",
                    "scripts/cloneid_inventory.R",
                    "--mode",
                    "auto",
                    "--output",
                    tmpdir,
                ],
                env={"CLONEID_AGENT_FORCE_LIVE_ERROR": "1"},
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            payload = json.loads((Path(tmpdir) / "database_inventory.json").read_text())
            self.assertEqual(payload["mode_used"], "mock")
            self.assertEqual(payload["status"], "degraded")
            self.assertFalse(payload["live_access"]["success"])
            self.assertIn("Forced live error", payload["live_access"]["error"])

    def test_mock_inventory_writes_markdown_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_command(
                [
                    sys.executable,
                    "-m",
                    "cloneid_agent",
                    "inventory",
                    "--mode",
                    "mock",
                    "--output",
                    tmpdir,
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            report_path = Path(tmpdir) / "database_inventory.md"
            self.assertTrue(report_path.exists())
            report_text = report_path.read_text()
            self.assertIn("# Database Inventory", report_text)
            self.assertIn("## Tables", report_text)
            self.assertIn("## Key Table Summaries", report_text)


if __name__ == "__main__":
    unittest.main()
