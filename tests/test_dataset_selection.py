from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cloneid_agent.dataset_selection import select_top_candidate_payload


REPO_ROOT = Path(__file__).resolve().parents[1]


class DatasetSelectionTests(unittest.TestCase):
    def test_select_top_candidate_payload_preserves_ties(self) -> None:
        payload = {
            "source_run_id": "r1",
            "ranked_candidates": [
                {"dataset_id": "a", "score": 5, "score_reasons": ["x"]},
                {"dataset_id": "b", "score": 5, "score_reasons": ["x"]},
                {"dataset_id": "c", "score": 3, "score_reasons": ["y"]},
            ],
        }
        selected = select_top_candidate_payload(payload)
        self.assertEqual(selected["selected_dataset_id"], "a")
        self.assertEqual(selected["ties_at_top_score"], ["a", "b"])

    def test_select_candidate_cli_writes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["PYTHONPATH"] = str(REPO_ROOT / "src")
            candidate_dir = Path(tmpdir) / "candidate"
            ranked_dir = Path(tmpdir) / "ranked"
            selected_dir = Path(tmpdir) / "selected"
            candidate_dir.mkdir()
            ranked_dir.mkdir()
            selected_dir.mkdir()

            inv_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cloneid_agent",
                    "candidate-inventory",
                    "--mode",
                    "mock",
                    "--output",
                    str(candidate_dir),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(inv_result.returncode, 0, msg=inv_result.stderr)

            rank_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cloneid_agent",
                    "rank-candidates",
                    "--input",
                    str(candidate_dir / "dataset_inventory.json"),
                    "--output-dir",
                    str(ranked_dir),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(rank_result.returncode, 0, msg=rank_result.stderr)

            select_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cloneid_agent",
                    "select-candidate",
                    "--input",
                    str(ranked_dir / "ranked_candidates.json"),
                    "--output-dir",
                    str(selected_dir),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(select_result.returncode, 0, msg=select_result.stderr)
            self.assertTrue((selected_dir / "selected_candidate.json").exists())
            self.assertTrue((selected_dir / "selected_candidate.md").exists())

            payload = json.loads((selected_dir / "selected_candidate.json").read_text())
            self.assertIn("selected_dataset_id", payload)


if __name__ == "__main__":
    unittest.main()
