from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class ToyWorkflowTests(unittest.TestCase):
    def test_toy_roundtrip_cli_writes_expected_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cloneid_agent",
                    "toy-roundtrip",
                    "--output",
                    tmpdir,
                ],
                cwd=REPO_ROOT,
                env={"PYTHONPATH": str(REPO_ROOT / "src")},
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)

            expected = [
                "toy_fixture.json",
                "database_inventory.json",
                "selected_dataset.json",
                "trajectory_bundle.json",
                "observables.json",
                "agent_plan.json",
                "model_selection_report.md",
            ]
            for name in expected:
                self.assertTrue((Path(tmpdir) / name).exists(), msg=name)

            self.assertTrue((Path(tmpdir) / "evaluation" / "model_comparison.csv").exists())
            self.assertTrue((Path(tmpdir) / "model_candidates" / "neutral_growth.json").exists())
            self.assertTrue((Path(tmpdir) / "model_candidates" / "fixed_state_fitness.json").exists())

            payload = json.loads((Path(tmpdir) / "selected_dataset.json").read_text())
            self.assertEqual(payload["dataset_id"], "toy_dataset_001")
            self.assertEqual(payload["score"], 5)


if __name__ == "__main__":
    unittest.main()
