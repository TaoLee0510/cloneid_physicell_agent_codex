from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

from cloneid_agent.model_candidate import generate_model_candidates


REPO_ROOT = Path(__file__).resolve().parents[1]


BASE_CONFIG = """<PhysiCell_settings>
  <overall><max_time units="min">64800</max_time></overall>
  <parallel><omp_num_threads>6</omp_num_threads></parallel>
  <save><folder>output</folder></save>
</PhysiCell_settings>
"""


class ModelCandidateTests(unittest.TestCase):
    def _fake_physicell_root(self, root: Path) -> Path:
        physicell_root = root / "PhysiCell"
        config_dir = physicell_root / "config"
        config_dir.mkdir(parents=True)
        (config_dir / "PhysiCell_settings.xml").write_text(BASE_CONFIG)
        executable = physicell_root / "heterogeneity"
        executable.write_text("#!/usr/bin/env bash\nexit 0\n")
        executable.chmod(executable.stat().st_mode | stat.S_IXUSR)
        return physicell_root

    def test_generate_model_candidates_writes_family_directories_and_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            physicell_root = self._fake_physicell_root(root)
            output_dir = root / "run"
            payload = generate_model_candidates(
                selected_lineage_object_payload={
                    "selected_lineage_object_id": "rooted_trajectory_bundle::mock_root",
                    "selected_lineage_object_type": "RootedTrajectoryBundle",
                },
                selected_observables_payload={"selected": [{"source": "Passaging.correctedCount"}]},
                mapping_payload={
                    "mapping_version": "physicell_mapping_v1",
                    "selected_lineage_object_id": "rooted_trajectory_bundle::mock_root",
                    "selected_lineage_object_type": "RootedTrajectoryBundle",
                    "timeline": {"phenotype_time_span_days": 2.0},
                    "traversal_policy": {"primary_backbone": "passaged_from_id1"},
                    "recommended_model_families": ["neutral_growth", "fixed_state_fitness"],
                },
                output_dir=output_dir,
                physicell_root=physicell_root,
            )
            self.assertEqual(len(payload["model_candidates"]), 2)
            config_path = output_dir / "model_candidates" / "neutral_growth" / "config" / "PhysiCell_settings.xml"
            self.assertTrue(config_path.exists())
            root_xml = ET.parse(config_path).getroot()
            self.assertEqual(root_xml.find("./overall/max_time").text, "2880")
            self.assertEqual(root_xml.find("./parallel/omp_num_threads").text, "1")
            self.assertIn("simulation_output", root_xml.find("./save/folder").text)

    def test_generate_model_candidates_cli_writes_index_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            physicell_root = self._fake_physicell_root(root)
            lineage_path = root / "selected_lineage_object.json"
            observables_path = root / "selected_observables.json"
            mapping_path = root / "physicell_mapping.json"
            out_dir = root / "generated"
            lineage_path.write_text(
                json.dumps(
                    {
                        "selected_lineage_object_id": "lineage_path::mock_endpoint",
                        "selected_lineage_object_type": "LineagePath",
                    }
                )
            )
            observables_path.write_text(json.dumps({"selected": [{"source": "Passaging.correctedCount"}]}))
            mapping_path.write_text(
                json.dumps(
                    {
                        "mapping_version": "physicell_mapping_v1",
                        "selected_lineage_object_id": "lineage_path::mock_endpoint",
                        "selected_lineage_object_type": "LineagePath",
                        "timeline": {"phenotype_time_span_days": 1.0},
                        "recommended_model_families": ["neutral_growth"],
                    }
                )
            )
            env = os.environ.copy()
            env["PYTHONPATH"] = str(REPO_ROOT / "src")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cloneid_agent",
                    "generate-model-candidates",
                    "--lineage-object",
                    str(lineage_path),
                    "--observables",
                    str(observables_path),
                    "--mapping",
                    str(mapping_path),
                    "--output-dir",
                    str(out_dir),
                    "--physicell-root",
                    str(physicell_root),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((out_dir / "generated_model_candidates.json").exists())
            self.assertTrue((out_dir / "generated_model_candidates.md").exists())


if __name__ == "__main__":
    unittest.main()
