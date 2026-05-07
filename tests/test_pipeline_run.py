from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


class PipelineRunTests(unittest.TestCase):
    def test_one_command_dry_run_generates_required_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir) / "run"
            env = os.environ.copy()
            env["PYTHONPATH"] = str(REPO_ROOT / "src")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cloneid_agent",
                    "run",
                    "--config",
                    "configs/applications/snu668_density_history.yaml",
                    "--output",
                    str(output_dir),
                    "--mode",
                    "dry-run",
                ],
                cwd=REPO_ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            required = [
                "agent_plan.json",
                "database_inventory.json",
                "selected_dataset.json",
                "selected_lineage_object.json",
                "selected_observables.json",
                "history_covariates.json",
                "history_ablation.json",
                "compressed_view.json",
                "external_comparator.json",
                "physicell_mapping.json",
                "generated_model_candidates/neutral_growth/candidate_manifest.json",
                "observability_matrix.json",
                "observability_matrix.csv",
                "dataset_missingness.md",
                "family_comparison.json",
                "family_comparison.csv",
                "rejection_report.md",
                "comparative_identifiability_report.md",
                "family_discrimination_summary.md",
                "model_selection_report.md",
                "manuscript_facing_summary.md",
                "figure_data/family_comparison.csv",
            ]
            for rel in required:
                self.assertTrue((output_dir / rel).exists(), rel)


if __name__ == "__main__":
    unittest.main()
