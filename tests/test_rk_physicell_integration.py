from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cloneid_agent.rk_downsampling import (
    build_event_schedule,
    build_growth_episode_table,
    build_mock_cloneid_full_record,
    build_perspective_endpoint_table,
    downsample_cloneid_record,
)
from cloneid_agent.rk_physicell_integration import build_physicell_analysis, write_physicell_analysis
from cloneid_agent.rk_publication_record_extraction import extract_nwaa124_publication_record

from rk_fixture_utils import make_nwaa124_fixture_zip


class RkPhysiCellIntegrationTests(unittest.TestCase):
    def test_physicell_analysis_marks_density_history_as_full_history_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            full = build_mock_cloneid_full_record("SNU-668_r2_A9_seed,SNU-668_K3_A9_seed")
            growth = build_growth_episode_table(full["passaging_records"])
            event_schedule = build_event_schedule(full["passaging_records"])
            perspective = build_perspective_endpoint_table(full["perspective_records"])
            coarse = downsample_cloneid_record(full)
            nsr = extract_nwaa124_publication_record(make_nwaa124_fixture_zip(tmp), tmp / "external")

            payload = build_physicell_analysis(
                growth_episodes=growth,
                event_schedule=event_schedule,
                perspective_table=perspective,
                coarse_record=coarse,
                external_record=nsr,
            )

            by_regime = {row["dataset_regime"]: row for row in payload["regimes"]}
            full_density = next(
                row
                for row in by_regime["snu668_full_history"]["families"]
                if row["family_id"] == "density_dependent_growth"
            )
            compressed_density = next(
                row
                for row in by_regime["snu668_published_like_compressed"]["families"]
                if row["family_id"] == "density_dependent_growth"
            )
            nsr_density = next(
                row
                for row in by_regime["nwaa124_curated_external"]["families"]
                if row["family_id"] == "density_dependent_growth"
            )

            self.assertEqual(full_density["encoding_status"], "physicell_event_schedule_configurable")
            self.assertEqual(
                compressed_density["encoding_status"],
                "not_identifiable_for_physicell_density_history",
            )
            self.assertEqual(nsr_density["encoding_status"], "not_identifiable_for_physicell_density_history")
            self.assertGreater(
                by_regime["snu668_full_history"]["physicell_input_score"],
                by_regime["snu668_published_like_compressed"]["physicell_input_score"],
            )

    def test_write_physicell_analysis_outputs_reports_and_candidates(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            full = build_mock_cloneid_full_record()
            payload = build_physicell_analysis(
                growth_episodes=build_growth_episode_table(full["passaging_records"]),
                event_schedule=build_event_schedule(full["passaging_records"]),
                perspective_table=build_perspective_endpoint_table(full["perspective_records"]),
                coarse_record=downsample_cloneid_record(full),
                external_record=extract_nwaa124_publication_record(make_nwaa124_fixture_zip(tmp), tmp / "external"),
            )
            out = tmp / "physicell"
            write_physicell_analysis(out, payload)

            self.assertTrue((out / "physicell_input_manifest.json").exists())
            self.assertTrue((out / "model_family_physicell_comparison.csv").exists())
            self.assertTrue((out / "required_data_for_physicell.md").exists())
            self.assertTrue(
                (
                    out
                    / "candidate_configs"
                    / "snu668_full_history"
                    / "density_dependent_growth"
                    / "candidate_manifest.json"
                ).exists()
            )
            manifest = json.loads((out / "physicell_input_manifest.json").read_text())
            self.assertEqual(manifest["analysis_version"], "rk_physicell_integration_v1")
            summary = (out / "physicell_summary.md").read_text()
            self.assertIn("event-linked seed/harvest episodes", summary)
            self.assertIn("Runtime execution is not interpreted as calibrated biological evidence", summary)

    def test_physicell_candidate_uses_matching_project_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            physicell_root = tmp / "PhysiCell"
            (physicell_root / "sample_projects" / "heterogeneity" / "config").mkdir(parents=True)
            (physicell_root / "config").mkdir()
            (physicell_root / "heterogeneity").write_text("")
            project_config = physicell_root / "sample_projects" / "heterogeneity" / "config" / "PhysiCell_settings.xml"
            project_config.write_text(
                """<PhysiCell_settings>
  <overall><max_time>10</max_time></overall>
  <parallel><omp_num_threads>4</omp_num_threads></parallel>
  <save><folder>output</folder></save>
  <cell_definitions><cell_definition name="default" ID="0" /></cell_definitions>
  <user_parameters>
    <tumor_radius type="double" units="micron">250</tumor_radius>
    <oncoprotein_mean type="double" units="">1</oncoprotein_mean>
    <oncoprotein_sd type="double" units="">0.25</oncoprotein_sd>
    <oncoprotein_min type="double" units="">0</oncoprotein_min>
    <oncoprotein_max type="double" units="">2</oncoprotein_max>
  </user_parameters>
</PhysiCell_settings>"""
            )
            root_config = physicell_root / "config" / "PhysiCell_settings.xml"
            root_config.write_text("<PhysiCell_settings><user_parameters /></PhysiCell_settings>")

            full = build_mock_cloneid_full_record()
            payload = build_physicell_analysis(
                growth_episodes=build_growth_episode_table(full["passaging_records"]),
                event_schedule=build_event_schedule(full["passaging_records"]),
                perspective_table=build_perspective_endpoint_table(full["perspective_records"]),
                coarse_record=downsample_cloneid_record(full),
                external_record=extract_nwaa124_publication_record(make_nwaa124_fixture_zip(tmp), tmp / "external"),
                physicell_root=physicell_root,
            )
            self.assertEqual(Path(payload["physicell_source_config_resolved"]), project_config)

            out = tmp / "physicell"
            write_physicell_analysis(out, payload)
            candidate_config = (
                out
                / "candidate_configs"
                / "snu668_full_history"
                / "neutral_growth"
                / "config"
                / "PhysiCell_settings.xml"
            )
            text = candidate_config.read_text()
            self.assertIn("<tumor_radius", text)
            self.assertIn("<oncoprotein_mean", text)
            self.assertIn("<number_of_cells", text)
            manifest = json.loads(
                (
                    out
                    / "candidate_configs"
                    / "snu668_full_history"
                    / "neutral_growth"
                    / "candidate_manifest.json"
                ).read_text()
            )
            self.assertEqual(Path(manifest["source_config_path"]).resolve(), project_config.resolve())
            self.assertEqual(Path(manifest["physicell_executable"]).resolve(), (physicell_root / "heterogeneity").resolve())


if __name__ == "__main__":
    unittest.main()
