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
                "cloneid_downsampled/publication_level_coarse_record.json",
                "modeling/model_comparison_publication_vs_cloneid.csv",
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
            lowered = report.lower()
            self.assertNotIn("nsr data are bad", lowered)
            self.assertNotIn("nsr paper is flawed", lowered)


if __name__ == "__main__":
    unittest.main()
