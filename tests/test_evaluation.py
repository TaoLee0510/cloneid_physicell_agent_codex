from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cloneid_agent.evaluation import evaluate_generated_model_candidates


REPO_ROOT = Path(__file__).resolve().parents[1]


class EvaluationTests(unittest.TestCase):
    def test_evaluate_generated_model_candidates_detects_runtime_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            candidate_dir = root / "model_candidates" / "neutral_growth"
            config_dir = candidate_dir / "config"
            runtime_dir = candidate_dir / "simulation_output_runtime_20260428T000000Z"
            config_dir.mkdir(parents=True)
            runtime_dir.mkdir(parents=True)
            (config_dir / "PhysiCell_settings.xml").write_text("<xml />")
            for name in ("initial.xml", "final.xml", "initial.svg", "final.svg"):
                (runtime_dir / name).write_text("")
            payload = evaluate_generated_model_candidates(
                {
                    "selected_lineage_object_id": "rooted_trajectory_bundle::mock",
                    "selected_lineage_object_type": "RootedTrajectoryBundle",
                    "model_candidates": [
                        {
                            "candidate_id": "neutral_growth__mock",
                            "family": "neutral_growth",
                            "candidate_dir": str(candidate_dir),
                            "config_path": str(config_dir / "PhysiCell_settings.xml"),
                        }
                    ],
                }
            )
            self.assertEqual(payload["candidate_evaluations"][0]["runtime_status"], "runtime_executed")

    def test_evaluation_and_report_cli_write_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            generated_models_path = root / "generated_model_candidates.json"
            evaluation_dir = root / "evaluation"
            report_dir = root / "report"
            candidate_dir = root / "model_candidates" / "neutral_growth"
            config_dir = candidate_dir / "config"
            config_dir.mkdir(parents=True)
            (config_dir / "PhysiCell_settings.xml").write_text("<xml />")
            generated_models_path.write_text(
                json.dumps(
                    {
                        "selected_lineage_object_id": "lineage_path::mock",
                        "selected_lineage_object_type": "LineagePath",
                        "model_candidates": [
                            {
                                "candidate_id": "neutral_growth__mock",
                                "family": "neutral_growth",
                                "candidate_dir": str(candidate_dir),
                                "config_path": str(config_dir / "PhysiCell_settings.xml"),
                            }
                        ],
                    }
                )
            )
            lineage_path = root / "selected_lineage_object.json"
            observables_path = root / "selected_observables.json"
            mapping_path = root / "physicell_mapping.json"
            lineage_path.write_text(json.dumps({"selected_lineage_object_id": "lineage_path::mock", "selected_lineage_object_type": "LineagePath", "root_event_id": "root", "lineage_object_features": {"event_count": 2, "event_graph_depth": 1}}))
            observables_path.write_text(json.dumps({"selected": [{"source": "Passaging.correctedCount", "target": "viable cell count", "allowed_uses": ["calibration"]}]}))
            mapping_path.write_text(json.dumps({"mapping_version": "physicell_mapping_v1", "recommended_model_families": ["neutral_growth"]}))

            env = os.environ.copy()
            env["PYTHONPATH"] = str(REPO_ROOT / "src")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cloneid_agent",
                    "evaluate-model-candidates",
                    "--input",
                    str(generated_models_path),
                    "--output-dir",
                    str(evaluation_dir),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((evaluation_dir / "evaluation.json").exists())
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cloneid_agent",
                    "write-run-report",
                    "--lineage-object",
                    str(lineage_path),
                    "--observables",
                    str(observables_path),
                    "--mapping",
                    str(mapping_path),
                    "--generated-models",
                    str(generated_models_path),
                    "--evaluation",
                    str(evaluation_dir / "evaluation.json"),
                    "--output-dir",
                    str(report_dir),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((report_dir / "report.md").exists())


if __name__ == "__main__":
    unittest.main()
