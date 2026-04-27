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
                "passaged_from_id2": None,
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
        self.assertEqual(len(bundle["connected_candidate_segments"]), 3)
        self.assertEqual(len(bundle["passaging_records"]), 4)
        self.assertGreaterEqual(len(bundle["context_transitions"]), 3)
        self.assertEqual(len(bundle["perspective_records"]), 2)
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


if __name__ == "__main__":
    unittest.main()
