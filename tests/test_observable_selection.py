from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cloneid_agent.observable_selection import select_observables_from_lineage_object_payload


REPO_ROOT = Path(__file__).resolve().parents[1]


class ObservableSelectionTests(unittest.TestCase):
    def test_select_observables_prefers_corrected_count_and_perspective(self) -> None:
        payload = {
            "selected_lineage_object_id": "rooted_trajectory_bundle::mock_root",
            "selected_lineage_object_type": "RootedTrajectoryBundle",
            "passaging_records": [
                {"correctedCount": 100, "areaOccupied_um2": 1000.0, "cellCount": 110},
                {"correctedCount": 150, "areaOccupied_um2": 1400.0, "cellCount": 160},
            ],
            "perspective_records": [{"size": 0.7}, {"size": 0.3}],
            "identity_support_records": [{"size": 0.7}],
        }
        observables = select_observables_from_lineage_object_payload(payload)
        self.assertEqual(observables["selected"][0]["source"], "Passaging.correctedCount")
        self.assertEqual(observables["selected"][1]["source"], "Perspective.size")
        self.assertEqual(observables["selected_lineage_object_id"], "rooted_trajectory_bundle::mock_root")
        self.assertTrue(any(item["source"] == "Identity.size/state" for item in observables["excluded"]))

    def test_select_observables_cli_writes_artifacts(self) -> None:
        payload = {
            "selected_lineage_object_id": "lineage_path::mock_endpoint",
            "selected_lineage_object_type": "LineagePath",
            "passaging_records": [{"correctedCount": 100}],
            "perspective_records": [{"size": 1.0}],
            "identity_support_records": [],
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle_path = Path(tmpdir) / "selected_lineage_object.json"
            out_dir = Path(tmpdir) / "observables"
            bundle_path.write_text(json.dumps(payload))
            out_dir.mkdir()
            env = os.environ.copy()
            env["PYTHONPATH"] = str(REPO_ROOT / "src")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cloneid_agent",
                    "select-observables",
                    "--input",
                    str(bundle_path),
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
            self.assertTrue((out_dir / "selected_observables.json").exists())
            self.assertTrue((out_dir / "selected_observables.md").exists())
            saved = json.loads((out_dir / "selected_observables.json").read_text())
            self.assertEqual(saved["selected_lineage_object_id"], "lineage_path::mock_endpoint")


if __name__ == "__main__":
    unittest.main()
