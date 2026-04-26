from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cloneid_agent.dataset_ranking import rank_candidates_from_inventory_payload, summary_from_candidate_record


REPO_ROOT = Path(__file__).resolve().parents[1]


class DatasetRankingTests(unittest.TestCase):
    def test_summary_from_candidate_record_uses_event_and_phenotype_logic(self) -> None:
        summary = summary_from_candidate_record(
            {
                "dataset_id": "toy_dataset",
                "passaging_rows": 3,
                "harvest_events": 2,
                "distinct_dates": 3,
                "lineage_link_rows": 2,
                "corrected_count_rows": 3,
                "area_rows": 0,
                "qupath_rows": 0,
                "perspective_rows": 10,
                "distinct_perspectives": 1,
                "distinct_perspective_states": 2,
                "context_complete": True,
            }
        )
        self.assertTrue(summary.event_history_available)
        self.assertTrue(summary.repeated_phenotype_measurements)
        self.assertTrue(summary.endpoint_molecular_readout)
        self.assertTrue(summary.sufficient_context_for_initialization)
        self.assertTrue(summary.multiple_plausible_mechanisms)

    def test_rank_candidates_from_inventory_payload_sorts_scores(self) -> None:
        payload = {
            "run_id": "candidate_run",
            "candidates": [
                {
                    "dataset_id": "low",
                    "passaging_rows": 1,
                    "harvest_events": 1,
                    "distinct_dates": 1,
                    "lineage_link_rows": 0,
                    "corrected_count_rows": 0,
                    "area_rows": 0,
                    "qupath_rows": 0,
                    "perspective_rows": 0,
                    "distinct_perspectives": 0,
                    "distinct_perspective_states": 0,
                    "context_complete": True,
                },
                {
                    "dataset_id": "high",
                    "passaging_rows": 3,
                    "harvest_events": 2,
                    "distinct_dates": 3,
                    "lineage_link_rows": 2,
                    "corrected_count_rows": 3,
                    "area_rows": 2,
                    "qupath_rows": 0,
                    "perspective_rows": 5,
                    "distinct_perspectives": 1,
                    "distinct_perspective_states": 3,
                    "context_complete": True,
                },
            ],
        }
        ranked = rank_candidates_from_inventory_payload(payload)
        self.assertEqual(ranked["ranked_candidates"][0]["dataset_id"], "high")
        self.assertGreater(ranked["ranked_candidates"][0]["score"], ranked["ranked_candidates"][1]["score"])

    def test_rank_candidates_cli_writes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            env = os.environ.copy()
            env["PYTHONPATH"] = str(REPO_ROOT / "src")
            inventory_dir = Path(tmpdir) / "inventory"
            rank_dir = Path(tmpdir) / "ranked"
            inventory_dir.mkdir()
            rank_dir.mkdir()

            inv_result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cloneid_agent",
                    "candidate-inventory",
                    "--mode",
                    "mock",
                    "--output",
                    str(inventory_dir),
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
                    str(inventory_dir / "dataset_inventory.json"),
                    "--output-dir",
                    str(rank_dir),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(rank_result.returncode, 0, msg=rank_result.stderr)
            self.assertTrue((rank_dir / "ranked_candidates.json").exists())
            self.assertTrue((rank_dir / "ranked_candidates.md").exists())

            payload = json.loads((rank_dir / "ranked_candidates.json").read_text())
            self.assertEqual(payload["candidate_count"], 2)


if __name__ == "__main__":
    unittest.main()
