from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET

from cloneid_agent.model_family_specification import build_schedule_aware_model_family_specification
from cloneid_agent.phase_planning import (
    build_milestone_matched_primary_lineage_interval_phase_plan,
    build_primary_lineage_interval_phase_plan,
)
from cloneid_agent.schedule_aware_candidates import (
    DEFAULT_SCHEDULE_AWARE_CANDIDATE_DIR,
    SHARED_EVALUATION_OBJECTIVE,
    generate_schedule_aware_model_candidates,
)
from cloneid_agent.simulation_schedule import (
    build_branch_simulation_schedule,
    build_matched_simulation_schedule,
)


def _branch_payload(prefix: str, terminal_perspectives: int) -> dict[str, object]:
    return {
        "lineage_object_id": f"lineage_path::{prefix}_O2_A7K_harvest",
        "lineage_object_type": "LineagePath",
        "root_event_id": f"{prefix}_root",
        "endpoint_event_ids": [f"{prefix}_O2_A7K_harvest"],
        "lineage_path_event_ids": [
            f"{prefix}_root",
            f"{prefix}_dp_seed",
            f"{prefix}_dp_seedT1",
            f"{prefix}_O2_A1_seed",
            f"{prefix}_O2_A1_seedT1",
            f"{prefix}_O2_A2_seed",
            f"{prefix}_O2_A2_seedT2",
            f"{prefix}_O2_A7K_seed",
            f"{prefix}_O2_A7K_harvest",
        ],
        "passaging_records": [
            {"id": f"{prefix}_root", "date": "2024-01-01 00:00:00", "event": "harvest", "passage": 1, "media": 10, "flask": 1, "cellCount": 100, "correctedCount": 90, "areaOccupied_um2": 1000},
            {"id": f"{prefix}_dp_seed", "date": "2024-01-02 00:00:00", "event": "seeding", "passage": 2, "media": 10, "flask": 1, "cellCount": 120, "correctedCount": 100, "areaOccupied_um2": 1200, "passaged_from_id1": f"{prefix}_root"},
            {"id": f"{prefix}_dp_seedT1", "date": "2024-01-03 00:00:00", "event": "harvest", "passage": 2, "media": 10, "flask": 1, "cellCount": 240, "correctedCount": 220, "areaOccupied_um2": 2400, "passaged_from_id1": f"{prefix}_dp_seed"},
            {"id": f"{prefix}_O2_A1_seed", "date": "2024-01-03 01:00:00", "event": "seeding", "passage": 3, "media": 11, "flask": 2, "cellCount": 80, "correctedCount": 70, "areaOccupied_um2": 800, "passaged_from_id1": f"{prefix}_dp_seedT1"},
            {"id": f"{prefix}_O2_A1_seedT1", "date": "2024-01-04 01:00:00", "event": "harvest", "passage": 3, "media": 11, "flask": 2, "cellCount": 160, "correctedCount": 140, "areaOccupied_um2": 1600, "passaged_from_id1": f"{prefix}_O2_A1_seed"},
            {"id": f"{prefix}_O2_A2_seed", "date": "2024-01-04 02:00:00", "event": "seeding", "passage": 4, "media": 12, "flask": 2, "cellCount": 60, "correctedCount": 50, "areaOccupied_um2": 600, "passaged_from_id1": f"{prefix}_O2_A1_seedT1"},
            {"id": f"{prefix}_O2_A2_seedT2", "date": "2024-01-05 02:00:00", "event": "harvest", "passage": 4, "media": 12, "flask": 2, "cellCount": 140, "correctedCount": 120, "areaOccupied_um2": 1400, "passaged_from_id1": f"{prefix}_O2_A2_seed"},
            {"id": f"{prefix}_O2_A7K_seed", "date": "2024-01-05 03:00:00", "event": "seeding", "passage": 5, "media": 13, "flask": 3, "cellCount": 70, "correctedCount": 60, "areaOccupied_um2": 700, "passaged_from_id1": f"{prefix}_O2_A2_seedT2"},
            {"id": f"{prefix}_O2_A7K_harvest", "date": "2024-01-06 03:00:00", "event": "harvest", "passage": 5, "media": 13, "flask": 3, "cellCount": 180, "correctedCount": 150, "areaOccupied_um2": 1800, "passaged_from_id1": f"{prefix}_O2_A7K_seed"},
        ],
        "perspective_records": [
            {"origin": f"{prefix}_O2_A7K_harvest", "size": 1.0, "whichPerspective": f"p{idx}"}
            for idx in range(terminal_perspectives)
        ],
        "lineage_object_features": {"phenotype_time_span_days": 5.0},
    }


def _build_fixture():
    anchor_plan = build_primary_lineage_interval_phase_plan(_branch_payload("SUM159_4N", 2), branch_id="SUM159_4N_O2")
    comparison_plan = build_primary_lineage_interval_phase_plan(_branch_payload("SUM159_2N", 1), branch_id="SUM159_2N_O2")
    milestone = build_milestone_matched_primary_lineage_interval_phase_plan(
        anchor_plan=anchor_plan,
        comparison_plan=comparison_plan,
    )
    anchor_schedule = build_branch_simulation_schedule(
        phase_plan=anchor_plan,
        milestone_matched_plan=milestone,
        branch_role="anchor",
    )
    comparison_schedule = build_branch_simulation_schedule(
        phase_plan=comparison_plan,
        milestone_matched_plan=milestone,
        branch_role="comparison",
    )
    matched_schedule = build_matched_simulation_schedule(
        anchor_schedule=anchor_schedule,
        comparison_schedule=comparison_schedule,
        milestone_matched_plan=milestone,
    )
    specification = build_schedule_aware_model_family_specification(
        anchor_schedule=anchor_schedule,
        comparison_schedule=comparison_schedule,
        matched_schedule=matched_schedule,
    )
    return anchor_schedule, comparison_schedule, matched_schedule, specification


def _make_fake_physicell_root(root: Path) -> Path:
    config_dir = root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (root / "heterogeneity").write_text("fake")
    xml = """<PhysiCell_settings>
<overall><max_time>60</max_time></overall>
<parallel><omp_num_threads>1</omp_num_threads></parallel>
<save><folder>output</folder></save>
<user_parameters></user_parameters>
</PhysiCell_settings>
"""
    (config_dir / "PhysiCell_settings.xml").write_text(xml)
    return root


class ScheduleAwareCandidateTests(unittest.TestCase):
    def test_candidates_are_differentiated_and_share_objective(self) -> None:
        anchor_schedule, comparison_schedule, matched_schedule, specification = _build_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            physicell_root = _make_fake_physicell_root(tmp_path / "physicell")
            payload = generate_schedule_aware_model_candidates(
                anchor_schedule=anchor_schedule,
                comparison_schedule=comparison_schedule,
                matched_schedule=matched_schedule,
                specification_payload=specification,
                output_dir=tmp_path / "run",
                physicell_root=physicell_root,
            )
            root = Path(payload["candidate_root"])
            self.assertEqual(root.name, DEFAULT_SCHEDULE_AWARE_CANDIDATE_DIR)
            families = ["neutral_growth", "fixed_state_fitness", "density_dependent_growth"]
            xml_texts = {}
            manifests = {}
            evaluation_plans = {}
            parameter_payloads = {}
            for family in families:
                family_dir = root / family
                self.assertTrue((family_dir / "config" / "PhysiCell_settings.xml").exists())
                self.assertTrue((family_dir / "candidate_manifest.json").exists())
                self.assertTrue((family_dir / "README.md").exists())
                self.assertTrue((family_dir / "schedule_mapping.json").exists())
                self.assertTrue((family_dir / "evaluation_plan.json").exists())
                self.assertTrue((family_dir / "parameter_placeholders.json").exists())
                xml_texts[family] = (family_dir / "config" / "PhysiCell_settings.xml").read_text()
                manifests[family] = json.loads((family_dir / "candidate_manifest.json").read_text())
                evaluation_plans[family] = json.loads((family_dir / "evaluation_plan.json").read_text())
                parameter_payloads[family] = json.loads((family_dir / "parameter_placeholders.json").read_text())

            self.assertNotEqual(xml_texts["neutral_growth"], xml_texts["fixed_state_fitness"])
            self.assertNotEqual(xml_texts["neutral_growth"], xml_texts["density_dependent_growth"])
            self.assertNotEqual(xml_texts["fixed_state_fitness"], xml_texts["density_dependent_growth"])

            self.assertNotEqual(manifests["neutral_growth"]["family_rule_mode"], manifests["fixed_state_fitness"]["family_rule_mode"])
            self.assertNotEqual(manifests["neutral_growth"]["family_rule_mode"], manifests["density_dependent_growth"]["family_rule_mode"])
            self.assertEqual(manifests["neutral_growth"]["shared_evaluation_objective"], SHARED_EVALUATION_OBJECTIVE)
            self.assertEqual(manifests["fixed_state_fitness"]["shared_evaluation_objective"], SHARED_EVALUATION_OBJECTIVE)
            self.assertEqual(manifests["density_dependent_growth"]["shared_evaluation_objective"], SHARED_EVALUATION_OBJECTIVE)

            self.assertEqual(
                evaluation_plans["neutral_growth"]["primary_shared_objective"],
                evaluation_plans["fixed_state_fitness"]["primary_shared_objective"],
            )
            self.assertEqual(
                evaluation_plans["neutral_growth"]["primary_shared_objective"],
                evaluation_plans["density_dependent_growth"]["primary_shared_objective"],
            )
            self.assertFalse(manifests["neutral_growth"]["perspective_size_used_for_fitting"])
            self.assertFalse(manifests["fixed_state_fitness"]["perspective_size_used_for_fitting"])
            self.assertFalse(manifests["density_dependent_growth"]["perspective_size_used_for_fitting"])

            neutral_params = set(parameter_payloads["neutral_growth"]["placeholder_parameters"])
            fixed_params = set(parameter_payloads["fixed_state_fitness"]["placeholder_parameters"])
            density_params = set(parameter_payloads["density_dependent_growth"]["placeholder_parameters"])
            self.assertFalse(any("_2N" in p or "_4N" in p for p in neutral_params))
            self.assertTrue(any("_2N" in p or "_4N" in p for p in fixed_params))
            self.assertTrue(any("density" in p or "area_proxy" in p for p in density_params))

            schedule_mapping = json.loads((root / "neutral_growth" / "schedule_mapping.json").read_text())
            self.assertTrue(schedule_mapping["prehistory_context_policy"]["excluded_from_primary_runtime"])
            self.assertEqual(schedule_mapping["transfer_event_policy"]["simulated_duration_minutes"], 0)

    def test_config_parameters_reflect_family_rules(self) -> None:
        anchor_schedule, comparison_schedule, matched_schedule, specification = _build_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            physicell_root = _make_fake_physicell_root(tmp_path / "physicell")
            payload = generate_schedule_aware_model_candidates(
                anchor_schedule=anchor_schedule,
                comparison_schedule=comparison_schedule,
                matched_schedule=matched_schedule,
                specification_payload=specification,
                output_dir=tmp_path / "run",
                physicell_root=physicell_root,
            )
            root = Path(payload["candidate_root"])
            neutral_xml = ET.parse(root / "neutral_growth" / "config" / "PhysiCell_settings.xml").getroot()
            fixed_xml = ET.parse(root / "fixed_state_fitness" / "config" / "PhysiCell_settings.xml").getroot()
            density_xml = ET.parse(root / "density_dependent_growth" / "config" / "PhysiCell_settings.xml").getroot()
            neutral_user = neutral_xml.find("./user_parameters")
            fixed_user = fixed_xml.find("./user_parameters")
            density_user = density_xml.find("./user_parameters")
            self.assertIsNotNone(neutral_user.find("shared_proliferation_rate"))
            self.assertIsNone(neutral_user.find("proliferation_rate_2N"))
            self.assertIsNone(neutral_user.find("proliferation_rate_4N"))
            self.assertIsNotNone(fixed_user.find("proliferation_rate_2N"))
            self.assertIsNotNone(fixed_user.find("proliferation_rate_4N"))
            self.assertIsNone(fixed_user.find("density_response_threshold"))
            self.assertIsNotNone(density_user.find("density_response_threshold"))
            self.assertIsNotNone(density_user.find("density_response_slope"))


if __name__ == "__main__":
    unittest.main()
