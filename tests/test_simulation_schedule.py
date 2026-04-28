from __future__ import annotations

import unittest

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


class SimulationScheduleTests(unittest.TestCase):
    def test_branch_schedule_separates_initial_growth_and_transfer(self) -> None:
        anchor_plan = build_primary_lineage_interval_phase_plan(_branch_payload("SUM159_4N", 2), branch_id="SUM159_4N_O2")
        comparison_plan = build_primary_lineage_interval_phase_plan(
            _branch_payload("SUM159_2N", 1),
            branch_id="SUM159_2N_O2",
        )
        milestone = build_milestone_matched_primary_lineage_interval_phase_plan(
            anchor_plan=anchor_plan,
            comparison_plan=comparison_plan,
        )
        schedule = build_branch_simulation_schedule(
            phase_plan=anchor_plan,
            milestone_matched_plan=milestone,
            branch_role="anchor",
        )
        self.assertEqual(schedule["initial_condition"]["milestone_label"], "O2_A1_seed")
        self.assertEqual(schedule["growth_episodes"][0]["milestone_label"], "O2_A1_seedT1")
        self.assertEqual(schedule["transfer_events"][0]["milestone_label"], "O2_A2_seed")
        self.assertEqual(schedule["growth_episodes"][0]["simulated_duration_minutes"], 1440)
        self.assertEqual(schedule["transfer_events"][0]["simulated_duration_minutes"], 0)
        self.assertTrue(schedule["validation"]["O2_A1_seed_used_as_initial_condition_not_growth_endpoint"])
        self.assertTrue(schedule["validation"]["seed_to_harvest_intervals_labeled_growth_episode"])
        self.assertTrue(schedule["validation"]["harvest_to_seed_intervals_labeled_transfer_event"])
        self.assertTrue(schedule["validation"]["transfer_events_not_assigned_growth_duration"])
        self.assertEqual(
            schedule["growth_episodes"][0]["observables"]["Passaging.correctedCount"]["evidence_class"],
            "derived_event_linked_phenotype",
        )
        self.assertEqual(
            schedule["growth_episodes"][0]["observables"]["Passaging.areaOccupied_um2"]["evidence_class"],
            "derived_event_linked_phenotype",
        )

    def test_matched_schedule_aligns_growth_episodes_by_milestone(self) -> None:
        anchor_plan = build_primary_lineage_interval_phase_plan(_branch_payload("SUM159_4N", 2), branch_id="SUM159_4N_O2")
        comparison_plan = build_primary_lineage_interval_phase_plan(
            _branch_payload("SUM159_2N", 3),
            branch_id="SUM159_2N_O2",
        )
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
        labels = [item["milestone_label"] for item in matched_schedule["matched_growth_episodes"]]
        self.assertEqual(labels, ["O2_A1_seedT1", "O2_A2_seedT2", "O2_A7K_harvest"])
        self.assertTrue(matched_schedule["endpoint_alignment"]["both_branches_contain_A7K_harvest"])
        self.assertTrue(matched_schedule["endpoint_alignment"]["both_A7K_harvest_endpoints_have_perspective_support"])
        self.assertTrue(matched_schedule["validation"]["phase_index_matching_not_primary_alignment"])


if __name__ == "__main__":
    unittest.main()
