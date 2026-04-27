from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cloneid_agent.trajectory_bundle_pipeline import select_seed_dataset_ids


REPO_ROOT = Path(__file__).resolve().parents[1]


class TrajectoryBundlePipelineTests(unittest.TestCase):
    def test_select_seed_dataset_ids_uses_rank_order(self) -> None:
        payload = {
            "ranked_candidates": [
                {"dataset_id": "seed_a", "score": 10},
                {"dataset_id": "seed_b", "score": 9},
                {"dataset_id": "seed_c", "score": 8},
            ]
        }
        self.assertEqual(
            select_seed_dataset_ids(payload, top_n=2),
            ["seed_a", "seed_b"],
        )

    def test_discover_live_trajectory_bundles_cli_supports_mock_mode(self) -> None:
        ranked_payload = {
            "ranked_candidates": [
                {"dataset_id": "MOCK__0__1__1__1", "score": 99.0},
                {"dataset_id": "MOCK__0__2__1__1", "score": 98.0},
            ]
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            ranked_path = Path(tmpdir) / "ranked_candidates.json"
            out_dir = Path(tmpdir) / "bundle_run"
            ranked_path.write_text(json.dumps(ranked_payload))
            env = os.environ.copy()
            env["PYTHONPATH"] = str(REPO_ROOT / "src")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cloneid_agent",
                    "discover-live-trajectory-bundles",
                    "--ranked-candidates",
                    str(ranked_path),
                    "--mode",
                    "mock",
                    "--top-n",
                    "2",
                    "--output",
                    str(out_dir),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((out_dir / "ranked_trajectory_bundles.json").exists())
            self.assertTrue((out_dir / "trajectory_bundle_pipeline_summary.json").exists())
            ranked = json.loads((out_dir / "ranked_trajectory_bundles.json").read_text())
            self.assertEqual(ranked["bundle_count"], 2)


if __name__ == "__main__":
    unittest.main()
