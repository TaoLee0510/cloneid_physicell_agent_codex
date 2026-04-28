from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cloneid_agent.lineage_object_ranking import rank_lineage_object_inventory
from cloneid_agent.lineage_object_selection import select_top_lineage_object
from cloneid_agent.lineage_objects import discover_global_lineage_objects


REPO_ROOT = Path(__file__).resolve().parents[1]


def build_global_fixture() -> dict[str, list[dict[str, object]]]:
    return {
        "passaging": [
            {
                "id": "short_root",
                "cellLine": "MOCK",
                "growthType": "0",
                "passage": 1,
                "media": 1,
                "flask": 1,
                "event": "seed",
                "date": "2024-01-01 00:00:00",
                "passaged_from_id1": None,
                "passaged_from_id2": None,
                "correctedCount": 100,
            },
            {
                "id": "short_end",
                "cellLine": "MOCK",
                "growthType": "0",
                "passage": 1,
                "media": 1,
                "flask": 1,
                "event": "harvest",
                "date": "2024-01-02 00:00:00",
                "passaged_from_id1": "short_root",
                "passaged_from_id2": None,
                "correctedCount": 140,
            },
            {
                "id": "long_r0",
                "cellLine": "MOCK",
                "growthType": "0",
                "passage": 10,
                "media": 1,
                "flask": 1,
                "event": "seed",
                "date": "2024-02-01 00:00:00",
                "passaged_from_id1": None,
                "passaged_from_id2": None,
                "correctedCount": 100,
            },
            {
                "id": "long_r1",
                "cellLine": "MOCK",
                "growthType": "0",
                "passage": 11,
                "media": 1,
                "flask": 1,
                "event": "seed",
                "date": "2024-02-03 00:00:00",
                "passaged_from_id1": "long_r0",
                "passaged_from_id2": None,
                "correctedCount": 120,
            },
            {
                "id": "long_r2",
                "cellLine": "MOCK",
                "growthType": "0",
                "passage": 12,
                "media": 1,
                "flask": 1,
                "event": "seed",
                "date": "2024-02-05 00:00:00",
                "passaged_from_id1": "long_r1",
                "passaged_from_id2": None,
                "correctedCount": 150,
            },
            {
                "id": "long_r3",
                "cellLine": "MOCK",
                "growthType": "0",
                "passage": 13,
                "media": 1,
                "flask": 1,
                "event": "seed",
                "date": "2024-02-07 00:00:00",
                "passaged_from_id1": "long_r2",
                "passaged_from_id2": None,
                "correctedCount": 180,
            },
            {
                "id": "long_end",
                "cellLine": "MOCK",
                "growthType": "0",
                "passage": 14,
                "media": 1,
                "flask": 1,
                "event": "harvest",
                "date": "2024-02-09 00:00:00",
                "passaged_from_id1": "long_r3",
                "passaged_from_id2": None,
                "correctedCount": 220,
            },
        ],
        "perspective": [
            {
                "cloneID": "p_short",
                "origin": "short_end",
                "whichPerspective": "GenomePerspective",
                "size": 1.0,
                "state": "S",
                "sampleSource": "short_end",
            },
            {
                "cloneID": "p_long",
                "origin": "long_end",
                "whichPerspective": "GenomePerspective",
                "size": 1.0,
                "state": "L",
                "sampleSource": "long_end",
            },
        ],
        "identity": [
            {
                "cloneID": "id_long",
                "sampleSource": "long_end",
                "GenomePerspective": "p_long",
                "state": "L",
            }
        ],
    }


def build_ranked_candidates_payload() -> dict[str, object]:
    return {
        "ranked_candidates": [
            {"dataset_id": "MOCK__0__1__1__1", "score": 99.0, "score_reasons": ["shallow local segment has very high local score"]},
            {"dataset_id": "MOCK__0__10__1__1", "score": 60.0, "score_reasons": ["long path start"]},
            {"dataset_id": "MOCK__0__11__1__1", "score": 58.0, "score_reasons": ["long path segment"]},
            {"dataset_id": "MOCK__0__12__1__1", "score": 56.0, "score_reasons": ["long path segment"]},
            {"dataset_id": "MOCK__0__13__1__1", "score": 55.0, "score_reasons": ["long path segment"]},
            {"dataset_id": "MOCK__0__14__1__1", "score": 54.0, "score_reasons": ["long path end"]},
        ]
    }


class GlobalLineageObjectTests(unittest.TestCase):
    def test_global_discovery_finds_long_path_spanning_multiple_segments(self) -> None:
        fixture = build_global_fixture()
        inventory = discover_global_lineage_objects(
            passaging_records=fixture["passaging"],
            perspective_records=fixture["perspective"],
            identity_records=fixture["identity"],
            ranked_candidates_payload=build_ranked_candidates_payload(),
        )
        self.assertEqual(inventory["discovered_object_counts"]["RootedTrajectoryBundle"], 2)
        self.assertEqual(inventory["discovered_object_counts"]["LineagePath"], 2)
        self.assertEqual(inventory["discovered_object_counts"]["LineageForest"], 0)

        long_path = next(
            item for item in inventory["global_lineage_objects"]
            if item["lineage_object_id"] == "lineage_path::long_end"
        )
        self.assertEqual(long_path["lineage_object_type"], "LineagePath")
        self.assertEqual(long_path["root_event_id"], "long_r0")
        self.assertEqual(long_path["lineage_path_event_ids"], ["long_r0", "long_r1", "long_r2", "long_r3", "long_end"])
        self.assertGreater(len(long_path["candidate_segments_covered"]), 1)

    def test_ranking_can_prefer_long_global_path_over_high_scoring_shallow_segment(self) -> None:
        fixture = build_global_fixture()
        inventory = discover_global_lineage_objects(
            passaging_records=fixture["passaging"],
            perspective_records=fixture["perspective"],
            identity_records=fixture["identity"],
            ranked_candidates_payload=build_ranked_candidates_payload(),
        )
        ranked = rank_lineage_object_inventory(inventory)
        selected = select_top_lineage_object(ranked)
        self.assertIn(
            selected["selected_lineage_object_id"],
            {"lineage_path::long_end", "rooted_trajectory_bundle::long_r0"},
        )
        self.assertNotIn(
            selected["selected_lineage_object_id"],
            {"lineage_path::short_end", "rooted_trajectory_bundle::short_root"},
        )

    def test_multi_root_object_cannot_be_selected_as_rooted_bundle(self) -> None:
        ranked = {
            "ranked_lineage_objects": [
                {
                    "lineage_object_id": "lineage_forest::1",
                    "lineage_object_type": "LineageForest",
                    "selection_eligible": False,
                    "lineage_object_score": 999.0,
                    "lineage_object_score_reasons": ["invalid"],
                },
                {
                    "lineage_object_id": "lineage_path::valid",
                    "lineage_object_type": "LineagePath",
                    "selection_eligible": True,
                    "lineage_object_score": 50.0,
                    "lineage_object_score_reasons": ["valid"],
                },
            ]
        }
        selected = select_top_lineage_object(ranked)
        self.assertEqual(selected["selected_lineage_object_id"], "lineage_path::valid")

    def test_live_lineage_objects_cli_supports_mock_mode(self) -> None:
        ranked_payload = build_ranked_candidates_payload()
        with tempfile.TemporaryDirectory() as tmpdir:
            ranked_path = Path(tmpdir) / "ranked_candidates.json"
            out_dir = Path(tmpdir) / "lineage_run"
            ranked_path.write_text(json.dumps(ranked_payload))
            env = os.environ.copy()
            env["PYTHONPATH"] = str(REPO_ROOT / "src")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cloneid_agent",
                    "discover-live-lineage-objects",
                    "--ranked-candidates",
                    str(ranked_path),
                    "--mode",
                    "mock",
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
            self.assertTrue((out_dir / "global_lineage_object_inventory.json").exists())
            self.assertTrue((out_dir / "ranked_lineage_objects.json").exists())
            self.assertTrue((out_dir / "selected_lineage_object.json").exists())


if __name__ == "__main__":
    unittest.main()
