from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cloneid_agent.modeling_lineage_selection import (
    classify_lineage_objects_for_modeling,
    select_modeling_lineage_object,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def ranked_fixture() -> dict[str, object]:
    big_bundle = {
        "lineage_object_id": "rooted_trajectory_bundle::big_root",
        "lineage_object_type": "RootedTrajectoryBundle",
        "selection_eligible": True,
        "lineage_object_score": 95.0,
        "lineage_object_score_reasons": ["large bundle"],
        "root_event_id": "big_root",
        "endpoint_event_ids": ["e1", "e2", "e3", "e4"],
        "rooted_subtree_event_ids": [f"b{i}" for i in range(250)],
        "lineage_path_event_ids": [],
        "passaging_records": [{"id": f"b{i}", "cellLine": "MOCK", "growthType": None, "media": i % 5, "date": "2024-01-01 00:00:00"} for i in range(250)],
        "lineage_object_features": {
            "root_count": 1,
            "endpoint_count": 12,
            "event_count": 250,
            "event_graph_depth": 80,
            "lineage_path_length": 0,
            "connected_segment_count": 20,
            "phenotype_observation_count": 150,
            "phenotype_time_span_days": 400.0,
            "terminal_perspective_support": 6,
        },
    }
    bounded_path = {
        "lineage_object_id": "lineage_path::good_end",
        "lineage_object_type": "LineagePath",
        "selection_eligible": True,
        "lineage_object_score": 70.0,
        "lineage_object_score_reasons": ["good path"],
        "root_event_id": "good_root",
        "endpoint_event_ids": ["good_end"],
        "rooted_subtree_event_ids": [],
        "lineage_path_event_ids": ["good_root", "g1", "g2", "good_end"],
        "passaging_records": [
            {"id": "good_root", "cellLine": "MOCK", "growthType": None, "media": 19, "date": "2024-01-01 00:00:00"},
            {"id": "g1", "cellLine": "MOCK", "growthType": None, "media": 19, "date": "2024-01-05 00:00:00"},
            {"id": "g2", "cellLine": "MOCK", "growthType": None, "media": 19, "date": "2024-01-10 00:00:00"},
            {"id": "good_end", "cellLine": "MOCK", "growthType": None, "media": 19, "date": "2024-01-20 00:00:00"},
        ],
        "lineage_object_features": {
            "root_count": 1,
            "endpoint_count": 1,
            "event_count": 4,
            "event_graph_depth": 3,
            "lineage_path_length": 4,
            "connected_segment_count": 2,
            "phenotype_observation_count": 4,
            "phenotype_time_span_days": 19.0,
            "terminal_perspective_support": 1,
        },
    }
    return {"ranked_lineage_objects": [big_bundle, bounded_path]}


class ModelingLineageSelectionTests(unittest.TestCase):
    def test_whole_cell_line_supertree_is_excluded(self) -> None:
        payload = classify_lineage_objects_for_modeling(ranked_fixture())
        excluded = {
            item["lineage_object_id"]: item["modeling_exclusion_reasons"]
            for item in payload["excluded_lineage_objects"]
        }
        self.assertIn("rooted_trajectory_bundle::big_root", excluded)
        self.assertIn("whole_cell_line_supertree", excluded["rooted_trajectory_bundle::big_root"])

    def test_bounded_path_is_selected_over_excessive_bundle(self) -> None:
        payload = classify_lineage_objects_for_modeling(ranked_fixture())
        selection = select_modeling_lineage_object(payload)
        self.assertEqual(selection["selected_lineage_object_id"], "lineage_path::good_end")

    def test_cli_writes_bounded_selection_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            ranked_path = Path(tmpdir) / "ranked_lineage_objects.json"
            out_dir = Path(tmpdir) / "bounded"
            ranked_path.write_text(json.dumps(ranked_fixture()))
            env = os.environ.copy()
            env["PYTHONPATH"] = str(REPO_ROOT / "src")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cloneid_agent",
                    "select-modeling-lineage-candidates",
                    "--input",
                    str(ranked_path),
                    "--output-dir",
                    str(out_dir),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((out_dir / "modeling_candidate_lineage_objects.json").exists())
            self.assertTrue((out_dir / "excluded_lineage_objects.json").exists())


if __name__ == "__main__":
    unittest.main()
