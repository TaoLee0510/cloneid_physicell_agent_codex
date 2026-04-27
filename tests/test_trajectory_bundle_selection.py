from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cloneid_agent.trajectory_bundle_selection import select_top_trajectory_bundle_payload


REPO_ROOT = Path(__file__).resolve().parents[1]


class TrajectoryBundleSelectionTests(unittest.TestCase):
    def test_select_top_trajectory_bundle_payload_preserves_ties(self) -> None:
        payload = {
            "ranked_trajectory_bundles": [
                {"bundle_id": "trajectory_bundle::a", "trajectory_bundle_score": 10, "trajectory_bundle_score_reasons": ["x"]},
                {"bundle_id": "trajectory_bundle::b", "trajectory_bundle_score": 10, "trajectory_bundle_score_reasons": ["x"]},
                {"bundle_id": "trajectory_bundle::c", "trajectory_bundle_score": 8, "trajectory_bundle_score_reasons": ["y"]},
            ]
        }
        selected = select_top_trajectory_bundle_payload(payload)
        self.assertEqual(selected["selected_bundle_id"], "trajectory_bundle::a")
        self.assertEqual(selected["ties_at_top_score"], ["trajectory_bundle::a", "trajectory_bundle::b"])

    def test_select_trajectory_bundle_cli_writes_artifacts(self) -> None:
        ranked_payload = {
            "ranked_trajectory_bundles": [
                {
                    "bundle_id": "trajectory_bundle::mock",
                    "seed_candidate_segment_id": "MOCK__0__1__1__1",
                    "trajectory_bundle_score": 12.5,
                    "trajectory_bundle_score_reasons": ["connected event history spans multiple useful local segments"],
                    "bundle_role": "rooted_trajectory_bundle",
                    "object_types": {"RootedTrajectoryBundle": "descendants_of_root_event_via_passaged_from_id1"},
                    "traversal_policy": {"primary_backbone": "passaged_from_id1"},
                    "root_event_id": "root_a",
                    "rooted_subtree_root_event_ids": ["root_a"],
                    "endpoint_event_ids": ["endpoint_b"],
                    "selected_endpoint_event_id": "endpoint_b",
                    "rooted_subtree_event_ids": ["root_a", "endpoint_b"],
                    "lineage_path_event_ids": ["root_a", "endpoint_b"],
                    "candidate_segments_covered": [{"dataset_id": "MOCK__0__1__1__1"}],
                    "connected_candidate_segments": [{"dataset_id": "MOCK__0__1__1__1"}],
                    "passaging_records": [{"id": "mock_seed"}],
                    "primary_lineage_edges": [{"parent_event_id": "a", "child_event_id": "b"}],
                    "secondary_lineage_edges": [{"parent_event_id": "x", "child_event_id": "b"}],
                    "lineage_edges": [{"parent_event_id": "a", "child_event_id": "b"}],
                    "segment_connections": [{"parent_segment_id": "x", "child_segment_id": "y"}],
                    "context_transitions_primary": [],
                    "context_transitions_secondary": [],
                    "context_transitions": [],
                    "perspective_origin_event_ids": ["endpoint_b"],
                    "perspective_records": [],
                    "identity_support_records": [],
                    "identity_records": [],
                    "trajectory_bundle_features": {"connected_segment_count": 1, "event_count": 1, "terminal_perspective_support": 0},
                    "attachment_policy": {},
                    "warnings": [],
                }
            ]
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            ranked_path = Path(tmpdir) / "ranked_trajectory_bundles.json"
            out_dir = Path(tmpdir) / "selected"
            ranked_path.write_text(json.dumps(ranked_payload))
            out_dir.mkdir()
            env = os.environ.copy()
            env["PYTHONPATH"] = str(REPO_ROOT / "src")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cloneid_agent",
                    "select-trajectory-bundle",
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
            self.assertTrue((out_dir / "selected_trajectory_bundle.json").exists())
            self.assertTrue((out_dir / "selected_trajectory_bundle_selection.json").exists())
            self.assertTrue((out_dir / "selected_trajectory_bundle.md").exists())
            payload = json.loads((out_dir / "selected_trajectory_bundle.json").read_text())
            self.assertEqual(payload["selected_bundle_id"], "trajectory_bundle::mock")
            self.assertEqual(len(payload["lineage_edges"]), 1)
            self.assertEqual(len(payload["primary_lineage_edges"]), 1)
            self.assertEqual(len(payload["secondary_lineage_edges"]), 1)
            self.assertEqual(len(payload["segment_connections"]), 1)
            self.assertEqual(payload["root_event_id"], "root_a")
            self.assertEqual(payload["selected_endpoint_event_id"], "endpoint_b")


if __name__ == "__main__":
    unittest.main()
