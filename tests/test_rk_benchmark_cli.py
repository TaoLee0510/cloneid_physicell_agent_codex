from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cloneid_agent.cli import main

from rk_fixture_utils import make_nwaa124_fixture_zip


class RkBenchmarkCliTests(unittest.TestCase):
    def test_run_rk_benchmark_cli_writes_required_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            zip_path = make_nwaa124_fixture_zip(tmp)
            output = tmp / "run"
            status = main(
                [
                    "run-rk-benchmark",
                    "--external-zip",
                    str(zip_path),
                    "--mode",
                    "mock",
                    "--output",
                    str(output),
                    "--fit",
                    "--make-figures",
                ]
            )
            self.assertEqual(status, 0)
            required = [
                "application_manifest.json",
                "external_comparator/nwaa124_archive_inventory.json",
                "external_comparator/nwaa124_modelability_audit.csv",
                "cloneid_full/event_graph.json",
                "cloneid_full/growth_episode_table.csv",
                "cloneid_full/history_covariates.json",
                "cloneid_full/history_covariates.csv",
                "cloneid_downsampled/publication_level_coarse_record.json",
                "cloneid_downsampled/history_ablation.json",
                "cloneid_downsampled/history_ablation.md",
                "modeling/model_comparison_publication_vs_cloneid.csv",
                "modeling/observability_profile.json",
                "modeling/observability_profile.csv",
                "modeling/family_comparison.json",
                "modeling/family_comparison.csv",
                "modeling/rejection_report.md",
                "modeling/comparative_identifiability_report.json",
                "modeling/comparative_identifiability_report.md",
                "standards/CLONEID_LTE_minimum_standard.md",
                "figures/model_comparison_publication_vs_cloneid.png",
                "model_selection_report.md",
                "MANUSCRIPT_INSERT.md",
            ]
            for rel in required:
                self.assertTrue((output / rel).exists(), rel)
            manifest = json.loads((output / "application_manifest.json").read_text())
            self.assertEqual(manifest["external_file_count"], 6)

    def test_reports_contain_overclaim_guardrails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            output = tmp / "run"
            main(
                [
                    "run-rk-benchmark",
                    "--external-zip",
                    str(make_nwaa124_fixture_zip(tmp)),
                    "--mode",
                    "mock",
                    "--output",
                    str(output),
                    "--fit",
                ]
            )
            report = (output / "model_selection_report.md").read_text()
            self.assertIn("NSR is a strong biological comparator, not a weak dataset.", report)
            self.assertIn("not whether the original paper was correct", report)
            self.assertIn("Manuscript numerical interpretation requires live read-only CLONEID extraction", report)
            self.assertIn("HeLa biology is not equated with SNU-668 biology", report)
            lowered = report.lower()
            self.assertNotIn("nsr data are bad", lowered)
            self.assertNotIn("nsr paper is flawed", lowered)


if __name__ == "__main__":
    unittest.main()
