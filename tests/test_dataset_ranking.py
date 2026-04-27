from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cloneid_agent.dataset_ranking import (
    extract_candidate_features,
    fine_score_candidate_record,
    rank_candidates_from_inventory_payload,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


class DatasetRankingTests(unittest.TestCase):
    def test_extract_candidate_features_uses_event_and_phenotype_logic(self) -> None:
        features = extract_candidate_features(
            {
                "dataset_id": "toy_dataset",
                "passaging_rows": 3,
                "harvest_events": 2,
                "seeding_events": 1,
                "distinct_dates": 3,
                "lineage_link_rows": 2,
                "corrected_count_rows": 3,
                "area_rows": 0,
                "qupath_rows": 0,
                "perspective_rows": 10,
                "distinct_perspectives": 1,
                "distinct_perspective_states": 2,
                "context_complete": True,
                "date_min": "2024-01-01 00:00:00",
                "date_max": "2024-01-10 00:00:00",
            }
        )
        self.assertTrue(features["event_history_available"])
        self.assertTrue(features["trajectory_available"])
        self.assertTrue(features["endpoint_molecular_available"])
        self.assertEqual(features["phenotype_modalities"], 1)
        self.assertGreater(features["temporal_span_days"], 0)

    def test_fine_score_prefers_longitudinal_trajectory_over_sparse_molecular_heavy_candidate(self) -> None:
        sparse_molecular = fine_score_candidate_record(
            {
                "dataset_id": "molecular_heavy",
                "passaging_rows": 2,
                "harvest_events": 1,
                "seeding_events": 0,
                "distinct_dates": 2,
                "lineage_link_rows": 0,
                "corrected_count_rows": 0,
                "area_rows": 0,
                "qupath_rows": 0,
                "perspective_rows": 10000,
                "distinct_perspectives": 1,
                "distinct_perspective_states": 20,
                "context_complete": True,
                "date_min": "2024-01-01 00:00:00",
                "date_max": "2024-01-02 00:00:00",
            }
        )
        trajectory_rich = fine_score_candidate_record(
            {
                "dataset_id": "trajectory_rich",
                "passaging_rows": 14,
                "harvest_events": 7,
                "seeding_events": 7,
                "distinct_dates": 14,
                "lineage_link_rows": 14,
                "corrected_count_rows": 14,
                "area_rows": 14,
                "qupath_rows": 0,
                "perspective_rows": 21,
                "distinct_perspectives": 1,
                "distinct_perspective_states": 10,
                "context_complete": True,
                "date_min": "2024-01-01 00:00:00",
                "date_max": "2024-03-01 00:00:00",
            }
        )
        self.assertGreater(trajectory_rich["score"], sparse_molecular["score"])
        self.assertGreater(
            trajectory_rich["score_components"]["trajectory_strength"],
            sparse_molecular["score_components"]["trajectory_strength"],
        )
        self.assertGreater(sparse_molecular["score_penalties"]["molecular_only_penalty"], 0)

    def test_rank_candidates_from_inventory_payload_sorts_fine_scores(self) -> None:
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
                    "date_min": "2024-01-01 00:00:00",
                    "date_max": "2024-01-01 00:00:00",
                },
                {
                    "dataset_id": "high",
                    "passaging_rows": 6,
                    "harvest_events": 3,
                    "seeding_events": 3,
                    "distinct_dates": 6,
                    "lineage_link_rows": 5,
                    "corrected_count_rows": 6,
                    "area_rows": 6,
                    "qupath_rows": 0,
                    "perspective_rows": 5,
                    "distinct_perspectives": 1,
                    "distinct_perspective_states": 3,
                    "context_complete": True,
                    "date_min": "2024-01-01 00:00:00",
                    "date_max": "2024-02-15 00:00:00",
                },
            ],
        }
        ranked = rank_candidates_from_inventory_payload(payload)
        self.assertEqual(ranked["ranked_candidates"][0]["dataset_id"], "high")
        self.assertGreater(ranked["ranked_candidates"][0]["score"], ranked["ranked_candidates"][1]["score"])
        self.assertEqual(ranked["score_model"], "fine_grained_v1")

    def test_fine_rank_candidates_cli_writes_artifacts(self) -> None:
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
                    "fine-rank-candidates",
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
            self.assertEqual(payload["score_model"], "fine_grained_v1")
            self.assertIn("score_components", payload["ranked_candidates"][0])


if __name__ == "__main__":
    unittest.main()
