from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cloneid_agent.physicell_mapping import build_physicell_mapping


REPO_ROOT = Path(__file__).resolve().parents[1]


class PhysiCellMappingTests(unittest.TestCase):
    def test_build_physicell_mapping_extracts_initialization_and_observables(self) -> None:
        bundle = {
            "selected_lineage_object_id": "rooted_trajectory_bundle::mock_root",
            "selected_lineage_object_type": "RootedTrajectoryBundle",
            "passaging_records": [
                {"id": "a", "cellLine": "MOCK", "flask": 1, "media": 1, "passage": 1, "date": "2024-01-01 00:00:00", "passaged_from_id1": None, "passaged_from_id2": None},
                {"id": "b", "cellLine": "MOCK", "flask": 1, "media": 1, "passage": 1, "date": "2024-01-02 00:00:00", "passaged_from_id1": "a", "passaged_from_id2": None},
            ],
            "lineage_object_features": {
                "event_count": 2,
                "phenotype_time_span_days": 1.0,
                "terminal_perspective_support": 1,
                "identity_support_count": 0,
            },
            "root_event_ids": ["a"],
            "root_event_id": "a",
            "traversal_policy": {"primary_backbone": "passaged_from_id1"},
            "context_transitions_primary": [],
            "context_transitions_secondary": [],
        }
        observables = {
            "selected": [
                {"source": "Passaging.correctedCount", "target": "viable cell count", "allowed_uses": ["calibration"]},
                {"source": "Perspective.size", "target": "endpoint state fraction", "allowed_uses": ["validation"]},
            ]
        }
        mapping = build_physicell_mapping(bundle, observables)
        self.assertEqual(mapping["initialization"]["initial_event_id"], "a")
        self.assertEqual(mapping["selected_lineage_object_id"], "rooted_trajectory_bundle::mock_root")
        self.assertEqual(mapping["observables"][0]["source"], "Passaging.correctedCount")
        self.assertIn("neutral_growth", mapping["recommended_model_families"])
        self.assertEqual(mapping["timeline"]["planned_max_time_min"], 1440)
        self.assertTrue(mapping["timeline"]["within_proof_of_principle_guardrail"])

    def test_map_to_physicell_cli_writes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle_path = Path(tmpdir) / "selected_lineage_object.json"
            observables_path = Path(tmpdir) / "selected_observables.json"
            out_dir = Path(tmpdir) / "mapping"
            bundle_path.write_text(
                json.dumps(
                    {
                        "selected_lineage_object_id": "lineage_path::mock_endpoint",
                        "selected_lineage_object_type": "LineagePath",
                        "passaging_records": [{"id": "a", "cellLine": "MOCK", "flask": 1, "media": 1, "passage": 1, "date": "2024-01-01 00:00:00", "passaged_from_id1": None, "passaged_from_id2": None}],
                        "lineage_object_features": {"event_count": 1, "phenotype_time_span_days": 0.0, "terminal_perspective_support": 0, "identity_support_count": 0},
                        "root_event_ids": ["a"],
                        "root_event_id": "a",
                        "context_transitions_primary": [],
                        "context_transitions_secondary": [],
                    }
                )
            )
            observables_path.write_text(json.dumps({"selected": []}))
            out_dir.mkdir()
            env = os.environ.copy()
            env["PYTHONPATH"] = str(REPO_ROOT / "src")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cloneid_agent",
                    "map-to-physicell",
                    "--bundle",
                    str(bundle_path),
                    "--observables",
                    str(observables_path),
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
            self.assertTrue((out_dir / "physicell_mapping.json").exists())
            self.assertTrue((out_dir / "physicell_mapping.md").exists())
            saved = json.loads((out_dir / "physicell_mapping.json").read_text())
            self.assertEqual(saved["selected_lineage_object_id"], "lineage_path::mock_endpoint")

    def test_mapping_flags_excessive_full_supertree_duration(self) -> None:
        bundle = {
            "selected_lineage_object_id": "rooted_trajectory_bundle::too_big",
            "selected_lineage_object_type": "RootedTrajectoryBundle",
            "passaging_records": [
                {"id": "a", "cellLine": "MOCK", "flask": 1, "media": 1, "passage": 1, "date": "2024-01-01 00:00:00", "passaged_from_id1": None, "passaged_from_id2": None},
                {"id": "b", "cellLine": "MOCK", "flask": 1, "media": 1, "passage": 2, "date": "2024-07-29 00:00:00", "passaged_from_id1": "a", "passaged_from_id2": None},
            ],
            "lineage_object_features": {
                "event_count": 2,
                "phenotype_time_span_days": 210.0,
                "terminal_perspective_support": 2,
                "identity_support_count": 0,
            },
            "root_event_ids": ["a"],
            "root_event_id": "a",
            "context_transitions_primary": [],
            "context_transitions_secondary": [],
        }
        mapping = build_physicell_mapping(bundle, {"selected": []})
        self.assertFalse(mapping["timeline"]["within_proof_of_principle_guardrail"])
        self.assertGreater(mapping["timeline"]["planned_max_time_min"], 86400)


if __name__ == "__main__":
    unittest.main()
