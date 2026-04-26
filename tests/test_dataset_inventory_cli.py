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


class CandidateInventoryCliTests(unittest.TestCase):
    def test_mock_candidate_inventory_json_structure(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_command(
                [
                    sys.executable,
                    "-m",
                    "cloneid_agent",
                    "candidate-inventory",
                    "--mode",
                    "mock",
                    "--output",
                    tmpdir,
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads((Path(tmpdir) / "dataset_inventory.json").read_text())
            self.assertEqual(payload["mode_used"], "mock")
            self.assertIn("grouping_definition", payload)
            self.assertIn("candidates", payload)
            self.assertGreaterEqual(payload["candidate_count"], 1)

    def test_candidate_inventory_falls_back_to_mock_on_live_error(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_command(
                [
                    "Rscript",
                    "scripts/cloneid_candidate_inventory.R",
                    "--mode",
                    "auto",
                    "--output",
                    tmpdir,
                ],
                env={"CLONEID_AGENT_FORCE_LIVE_ERROR": "1"},
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            payload = json.loads((Path(tmpdir) / "dataset_inventory.json").read_text())
            self.assertEqual(payload["mode_used"], "mock")
            self.assertEqual(payload["status"], "degraded")
            self.assertFalse(payload["live_access"]["success"])

    def test_mock_candidate_inventory_writes_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = run_command(
                [
                    sys.executable,
                    "-m",
                    "cloneid_agent",
                    "candidate-inventory",
                    "--mode",
                    "mock",
                    "--output",
                    tmpdir,
                ]
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            report = (Path(tmpdir) / "dataset_inventory.md").read_text()
            self.assertIn("# Candidate Dataset Inventory", report)
            self.assertIn("## Candidates", report)


if __name__ == "__main__":
    unittest.main()
