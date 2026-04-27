from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cloneid_agent.trajectory_bundles import discover_trajectory_bundle


REPO_ROOT = Path(__file__).resolve().parents[1]


def build_mock_bundle_fixture() -> dict[str, list[dict[str, object]]]:
    return {
        "passaging": [
            {
                "id": "seed_A",
                "cellLine": "MOCK_LINE",
                "growthType": "0",
                "passage": 5,
                "media": 19,
                "flask": 1,
                "event": "seeding",
                "date": "2024-01-01 00:00:00",
                "passaged_from_id1": None,
                "passaged_from_id2": None,
                "cellCount": 100,
                "correctedCount": 98,
                "areaOccupied_um2": 1000.0,
            },
            {
                "id": "harvest_A",
                "cellLine": "MOCK_LINE",
                "growthType": "0",
                "passage": 5,
                "media": 19,
                "flask": 1,
                "event": "harvest",
                "date": "2024-01-02 00:00:00",
                "passaged_from_id1": "seed_A",
                "passaged_from_id2": None,
                "cellCount": 160,
                "correctedCount": 155,
                "areaOccupied_um2": 1600.0,
            },
            {
                "id": "seed_B",
                "cellLine": "MOCK_LINE",
                "growthType": "0",
                "passage": 6,
                "media": 19,
                "flask": 2,
                "event": "seeding",
                "date": "2024-01-03 00:00:00",
                "passaged_from_id1": "harvest_A",
                "passaged_from_id2": None,
                "cellCount": 120,
                "correctedCount": 118,
                "areaOccupied_um2": 1200.0,
            },
            {
                "id": "harvest_B",
                "cellLine": "MOCK_LINE",
                "growthType": "0",
                "passage": 6,
                "media": 20,
                "flask": 2,
                "event": "harvest",
                "date": "2024-01-05 00:00:00",
                "passaged_from_id1": "seed_B",
                "passaged_from_id2": "seed_A",
                "cellCount": 220,
                "correctedCount": 215,
                "areaOccupied_um2": 2200.0,
            },
        ],
        "perspective": [
            {
                "cloneID": "persp_1",
                "origin": "harvest_B",
                "whichPerspective": "GenomePerspective",
                "size": 0.7,
                "state": "A",
                "sampleSource": "harvest_B",
                "rootID": "root_1",
            },
            {
                "cloneID": "persp_2",
                "origin": "harvest_B",
                "whichPerspective": "GenomePerspective",
                "size": 0.3,
                "state": "B",
                "sampleSource": "harvest_B",
                "rootID": "root_1",
            },
        ],
        "identity": [
            {
                "cloneID": "id_1",
                "sampleSource": "harvest_B",
                "GenomePerspective": "persp_1",
                "state": "A",
            }
        ],
    }


class TrajectoryBundleTests(unittest.TestCase):
    def test_discover_trajectory_bundle_expands_across_connected_segments(self) -> None:
        fixture = build_mock_bundle_fixture()
        bundle = discover_trajectory_bundle(
            seed_dataset_id="MOCK_LINE__0__5__19__1",
            passaging_records=fixture["passaging"],
            perspective_records=fixture["perspective"],
            identity_records=fixture["identity"],
        )
        self.assertEqual(bundle["seed_candidate_segment_id"], "MOCK_LINE__0__5__19__1")
        self.assertEqual(bundle["traversal_policy"]["primary_backbone"], "passaged_from_id1")
        self.assertEqual(
            bundle["traversal_policy"]["secondary_edges"],
            "passaged_from_id2_recorded_not_traversed",
        )
        self.assertEqual(bundle["root_event_id"], "seed_A")
        self.assertEqual(bundle["endpoint_event_ids"], ["harvest_B"])
        self.assertEqual(bundle["selected_endpoint_event_id"], "harvest_B")
        self.assertEqual(bundle["rooted_subtree_event_ids"], ["harvest_A", "harvest_B", "seed_A", "seed_B"])
        self.assertEqual(bundle["lineage_path_event_ids"], ["seed_A", "harvest_A", "seed_B", "harvest_B"])
        self.assertEqual(bundle["perspective_origin_event_ids"], ["harvest_B"])
        self.assertEqual(len(bundle["connected_candidate_segments"]), 3)
        self.assertEqual(len(bundle["candidate_segments_covered"]), 3)
        self.assertEqual(len(bundle["passaging_records"]), 4)
        self.assertEqual(len(bundle["primary_lineage_edges"]), 3)
        self.assertEqual(len(bundle["secondary_lineage_edges"]), 1)
        self.assertEqual(len(bundle["lineage_edges"]), 3)
        self.assertEqual(len(bundle["segment_connections"]), 2)
        self.assertEqual(len(bundle["context_transitions_primary"]), 3)
        self.assertEqual(len(bundle["context_transitions_secondary"]), 3)
        self.assertEqual(len(bundle["context_transitions"]), 3)
        self.assertEqual(len(bundle["perspective_records"]), 2)
        self.assertEqual(len(bundle["identity_support_records"]), 1)
        self.assertEqual(len(bundle["identity_records"]), 1)
        self.assertEqual(bundle["trajectory_bundle_features"]["connected_segment_count"], 3)
        self.assertGreater(bundle["trajectory_bundle_features"]["terminal_perspective_support"], 0)
        self.assertEqual(bundle["trajectory_bundle_features"]["event_graph_depth"], 3)
        self.assertTrue(bundle["trajectory_bundle_features"]["calibration_validation_split_possible"])
        self.assertEqual(bundle["trajectory_bundle_features"]["phenotype_time_span_days"], 4.0)
        self.assertEqual(
            bundle["identity_records"][0]["attachment_role"],
            "inferred_secondary_identity_support",
        )
        self.assertEqual(bundle["segment_connections"][0]["parent_segment_id"], "MOCK_LINE__0__5__19__1")
        self.assertEqual(bundle["segment_connections"][0]["child_segment_id"], "MOCK_LINE__0__6__19__2")
        self.assertEqual(
            [change["field"] for change in bundle["segment_connections"][0]["context_changes"]],
            ["passage", "flask"],
        )
        self.assertEqual(bundle["secondary_lineage_edges"][0]["parent_event_id"], "seed_A")
        self.assertEqual(bundle["secondary_lineage_edges"][0]["child_event_id"], "harvest_B")

    def test_discover_trajectory_bundle_cli_writes_artifacts(self) -> None:
        fixture = build_mock_bundle_fixture()
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture_path = Path(tmpdir) / "fixture.json"
            out_dir = Path(tmpdir) / "bundle"
            fixture_path.write_text(json.dumps(fixture))
            out_dir.mkdir()
            env = os.environ.copy()
            env["PYTHONPATH"] = str(REPO_ROOT / "src")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cloneid_agent",
                    "discover-trajectory-bundle",
                    "--input",
                    str(fixture_path),
                    "--seed-dataset-id",
                    "MOCK_LINE__0__5__19__1",
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
            self.assertTrue((out_dir / "trajectory_bundle.json").exists())
            self.assertTrue((out_dir / "trajectory_bundle.md").exists())
            payload = json.loads((out_dir / "trajectory_bundle.json").read_text())
            self.assertEqual(payload["trajectory_bundle_features"]["connected_segment_count"], 3)
            self.assertEqual(payload["root_event_id"], "seed_A")
            self.assertEqual(payload["selected_endpoint_event_id"], "harvest_B")
            self.assertEqual(payload["traversal_policy"]["context_grouping_role"], "annotation_only")

    def test_subgraph_boundary_counts_as_root_for_depth(self) -> None:
        fixture = build_mock_bundle_fixture()
        bundle = discover_trajectory_bundle(
            seed_dataset_id="MOCK_LINE__0__6__19__2",
            passaging_records=fixture["passaging"],
            perspective_records=fixture["perspective"],
            identity_records=fixture["identity"],
            max_upstream_depth=0,
            max_downstream_depth=4,
        )
        self.assertEqual(bundle["trajectory_bundle_features"]["root_event_count"], 1)
        self.assertEqual(bundle["trajectory_bundle_features"]["event_graph_depth"], 1)
        self.assertEqual(bundle["root_event_id"], "seed_B")
        self.assertEqual(bundle["lineage_path_event_ids"], ["seed_B", "harvest_B"])


if __name__ == "__main__":
    unittest.main()
