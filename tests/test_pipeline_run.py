from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class PipelineRunTests(unittest.TestCase):
    def test_config_driven_rk_benchmark_generates_merged_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "run"
            env = os.environ.copy()
            env["PYTHONPATH"] = str(REPO_ROOT / "src")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cloneid_agent.cli",
                    "run-rk-benchmark",
                    "--config",
                    "configs/applications/snu668_density_history.yaml",
                    "--external-zip",
                    "/mnt/data/nwaa124_supplement_file.zip",
                    "--output",
                    str(output_dir),
                    "--mode",
                    "mock",
                    "--fit",
                    "--make-figures",
                ],
                cwd=REPO_ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            required = [
                "application_manifest.json",
                "cloneid_full/history_covariates.json",
                "cloneid_full/history_covariates.csv",
                "cloneid_downsampled/history_ablation.json",
                "cloneid_downsampled/history_ablation.md",
                "modeling/observability_profile.json",
                "modeling/observability_profile.csv",
                "modeling/family_comparison.json",
                "modeling/family_comparison.csv",
                "modeling/rejection_report.md",
                "modeling/comparative_identifiability_report.json",
                "modeling/comparative_identifiability_report.md",
                "model_selection_report.md",
                "MANUSCRIPT_INSERT.md",
            ]
            for rel in required:
                self.assertTrue((output_dir / rel).exists(), rel)

    def test_run_compatibility_wrapper_delegates_to_rk_benchmark(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "run"
            env = os.environ.copy()
            env["PYTHONPATH"] = str(REPO_ROOT / "src")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cloneid_agent.cli",
                    "run",
                    "--config",
                    "configs/applications/snu668_density_history.yaml",
                    "--output",
                    str(output_dir),
                    "--mode",
                    "dry-run",
                    "--fit",
                ],
                cwd=REPO_ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((output_dir / "modeling" / "observability_profile.json").exists())


if __name__ == "__main__":
    unittest.main()
