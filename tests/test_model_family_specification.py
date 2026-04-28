from __future__ import annotations

import unittest

from cloneid_agent.model_family_specification import build_schedule_aware_model_family_specification
from cloneid_agent.phase_planning import (
    build_milestone_matched_primary_lineage_interval_phase_plan,
    build_primary_lineage_interval_phase_plan,
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


class ModelFamilySpecificationTests(unittest.TestCase):
    def test_family_spec_has_expected_families_and_targets(self) -> None:
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
        spec = build_schedule_aware_model_family_specification(
            anchor_schedule=anchor_schedule,
            comparison_schedule=comparison_schedule,
            matched_schedule=matched_schedule,
        )
        families = {item["family_id"]: item for item in spec["families"]}
        self.assertEqual(set(families), {"neutral_growth", "fixed_state_fitness", "density_dependent_growth"})
        self.assertEqual(families["neutral_growth"]["primary_calibration_target"], "Passaging.cellCount")
        self.assertEqual(families["fixed_state_fitness"]["primary_calibration_target"], "Passaging.correctedCount")
        self.assertEqual(families["density_dependent_growth"]["primary_calibration_target"], "Passaging.areaOccupied_um2")
        self.assertIn("Perspective.size", families["neutral_growth"]["secondary_validation_targets"])
        self.assertTrue(spec["no_fitted_parameter_values_yet"])
        self.assertGreaterEqual(len(spec["candidate_differentiation_checklist"]), 3)


if __name__ == "__main__":
    unittest.main()
