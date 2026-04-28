from __future__ import annotations

import unittest

from cloneid_agent.phase_planning import (
    DEFAULT_PROOF_OF_PRINCIPLE_GUARDRAIL_MINUTES,
    DEFAULT_SIMULATED_DURATION_MINUTES,
    build_matched_primary_lineage_interval_phase_plan,
    build_milestone_matched_primary_lineage_interval_phase_plan,
    build_primary_lineage_interval_phase_plan,
)


def lineage_payload(
    *,
    lineage_object_id: str,
    branch_prefix: str,
    phase_count: int,
    endpoint_perspective_records: int,
) -> dict[str, object]:
    event_ids = [f"{branch_prefix}_{idx}" for idx in range(phase_count + 1)]
    passaging_records = []
    for idx, event_id in enumerate(event_ids):
        record = {
            "id": event_id,
            "cellLine": "SUM-159",
            "date": f"2024-01-{idx + 1:02d} 00:00:00",
            "event": "harvest" if idx == len(event_ids) - 1 else "seed",
            "passage": idx + 1,
            "media": 100 + idx,
            "flask": 2,
            "cellCount": 1000 + idx,
            "correctedCount": 900 + idx,
            "areaOccupied_um2": 100000 + idx,
        }
        if idx > 0:
            record["passaged_from_id1"] = event_ids[idx - 1]
        passaging_records.append(record)
    perspective_records = [
        {
            "origin": event_ids[-1],
            "size": 0.5,
            "whichPerspective": f"perspective_{idx}",
        }
        for idx in range(endpoint_perspective_records)
    ]
    return {
        "lineage_object_id": lineage_object_id,
        "lineage_object_type": "LineagePath",
        "root_event_id": event_ids[0],
        "endpoint_event_ids": [event_ids[-1]],
        "lineage_path_event_ids": event_ids,
        "passaging_records": passaging_records,
        "perspective_records": perspective_records,
        "lineage_object_features": {
            "phenotype_time_span_days": float(phase_count),
        },
    }


class PhasePlanningTests(unittest.TestCase):
    def test_primary_lineage_phase_plan_preserves_order_and_labels(self) -> None:
        payload = lineage_payload(
            lineage_object_id="lineage_path::SUM159_NLS_4N_O2_A7K_harvest",
            branch_prefix="sum4n",
            phase_count=3,
            endpoint_perspective_records=2,
        )
        plan = build_primary_lineage_interval_phase_plan(payload, branch_id="SUM159_4N_O2")
        self.assertEqual(plan["summary"]["phase_count"], 3)
        self.assertTrue(plan["validation"]["phases_follow_passaged_from_id1_order"])
        self.assertTrue(plan["validation"]["fixed_simulated_duration_per_interval"])
        self.assertTrue(plan["validation"]["real_elapsed_time_retained_not_runtime"])
        self.assertEqual(plan["summary"]["terminal_perspective_supported_event_count"], 1)
        self.assertEqual(plan["summary"]["terminal_perspective_record_count"], 2)
        self.assertEqual(
            plan["observable_definitions"]["Passaging.correctedCount"]["evidence_class"],
            "derived_event_linked_phenotype",
        )
        self.assertEqual(
            plan["observable_definitions"]["Passaging.areaOccupied_um2"]["evidence_class"],
            "derived_event_linked_phenotype",
        )
        self.assertEqual(
            plan["observable_definitions"]["Perspective.size"]["evidence_class"],
            "perspective_molecular",
        )
        self.assertEqual(
            plan["phases"][0]["simulated_duration_minutes"],
            DEFAULT_SIMULATED_DURATION_MINUTES,
        )
        self.assertEqual(plan["phases"][-1]["perspective_record_count_at_child_event"], 2)

    def test_guardrail_validation_uses_simulated_not_raw_time(self) -> None:
        payload = lineage_payload(
            lineage_object_id="lineage_path::SUM159_NLS_2N_O2_A7K_harvest",
            branch_prefix="sum2n",
            phase_count=24,
            endpoint_perspective_records=1,
        )
        plan = build_primary_lineage_interval_phase_plan(payload, branch_id="SUM159_2N_O2")
        self.assertEqual(plan["summary"]["total_simulated_duration_minutes"], 24 * DEFAULT_SIMULATED_DURATION_MINUTES)
        self.assertTrue(
            plan["summary"]["total_simulated_duration_minutes"] < DEFAULT_PROOF_OF_PRINCIPLE_GUARDRAIL_MINUTES
        )
        self.assertTrue(plan["validation"]["total_simulated_duration_within_guardrail"])

    def test_matched_phase_plan_aligns_by_phase_index_and_reports_unmatched(self) -> None:
        anchor = build_primary_lineage_interval_phase_plan(
            lineage_payload(
                lineage_object_id="lineage_path::SUM159_NLS_4N_O2_A7K_harvest",
                branch_prefix="sum4n",
                phase_count=3,
                endpoint_perspective_records=2,
            ),
            branch_id="SUM159_4N_O2",
        )
        comparison = build_primary_lineage_interval_phase_plan(
            lineage_payload(
                lineage_object_id="lineage_path::SUM159_NLS_2N_O2_A7K_harvest",
                branch_prefix="sum2n",
                phase_count=4,
                endpoint_perspective_records=1,
            ),
            branch_id="SUM159_2N_O2",
        )
        matched = build_matched_primary_lineage_interval_phase_plan(
            anchor_plan=anchor,
            comparison_plan=comparison,
        )
        self.assertEqual(len(matched["matched_phases"]), 3)
        self.assertEqual(len(matched["unmatched_anchor_phases"]), 0)
        self.assertEqual(len(matched["unmatched_comparison_phases"]), 1)
        self.assertTrue(matched["validation"]["simulated_duration_fixed_at_1440_minutes"])
        self.assertTrue(matched["validation"]["real_elapsed_time_not_used_as_runtime"])

    def test_milestone_matched_plan_aligns_terminal_a7k_harvest(self) -> None:
        anchor = build_primary_lineage_interval_phase_plan(
            {
                "lineage_object_id": "lineage_path::SUM159_NLS_4N_O2_A7K_harvest",
                "lineage_object_type": "LineagePath",
                "root_event_id": "SUM-159_4N_NLS_mCherry",
                "endpoint_event_ids": ["SUM159_NLS_4N_O2_A7K_harvest"],
                "lineage_path_event_ids": [
                    "SUM-159_4N_NLS_mCherry",
                    "SUM-159_NLS_4N_dp_seed",
                    "SUM-159_NLS_4N_dp_seedT1",
                    "SUM-159_NLS_4N_O2_A1_seed",
                    "SUM-159_NLS_4N_O2_A1_seedT1",
                    "SUM-159_NLS_4N_O2_A7_seed",
                    "SUM-159_NLS_4N_O2_A7_seedT2",
                    "SUM-159_NLS_4N_O2_A7K_seed",
                    "SUM159_NLS_4N_O2_A7K_harvest",
                ],
                "passaging_records": [
                    {"id": "SUM-159_4N_NLS_mCherry", "date": "2024-01-01 00:00:00", "event": "harvest", "passage": 1, "cellCount": 1},
                    {"id": "SUM-159_NLS_4N_dp_seed", "date": "2024-01-02 00:00:00", "event": "seed", "passage": 2, "cellCount": 2, "passaged_from_id1": "SUM-159_4N_NLS_mCherry"},
                    {"id": "SUM-159_NLS_4N_dp_seedT1", "date": "2024-01-03 00:00:00", "event": "harvest", "passage": 2, "cellCount": 3, "passaged_from_id1": "SUM-159_NLS_4N_dp_seed"},
                    {"id": "SUM-159_NLS_4N_O2_A1_seed", "date": "2024-01-04 00:00:00", "event": "seed", "passage": 3, "cellCount": 4, "passaged_from_id1": "SUM-159_NLS_4N_dp_seedT1"},
                    {"id": "SUM-159_NLS_4N_O2_A1_seedT1", "date": "2024-01-05 00:00:00", "event": "harvest", "passage": 3, "cellCount": 5, "passaged_from_id1": "SUM-159_NLS_4N_O2_A1_seed"},
                    {"id": "SUM-159_NLS_4N_O2_A7_seed", "date": "2024-01-06 00:00:00", "event": "seed", "passage": 4, "cellCount": 6, "passaged_from_id1": "SUM-159_NLS_4N_O2_A1_seedT1"},
                    {"id": "SUM-159_NLS_4N_O2_A7_seedT2", "date": "2024-01-07 00:00:00", "event": "harvest", "passage": 4, "cellCount": 7, "passaged_from_id1": "SUM-159_NLS_4N_O2_A7_seed"},
                    {"id": "SUM-159_NLS_4N_O2_A7K_seed", "date": "2024-01-08 00:00:00", "event": "seed", "passage": 5, "cellCount": 8, "passaged_from_id1": "SUM-159_NLS_4N_O2_A7_seedT2"},
                    {"id": "SUM159_NLS_4N_O2_A7K_harvest", "date": "2024-01-09 00:00:00", "event": "harvest", "passage": 5, "cellCount": 9, "passaged_from_id1": "SUM-159_NLS_4N_O2_A7K_seed"},
                ],
                "perspective_records": [{"origin": "SUM159_NLS_4N_O2_A7K_harvest", "size": 1.0}],
                "lineage_object_features": {"phenotype_time_span_days": 8.0},
            },
            branch_id="SUM159_4N_O2",
        )
        comparison = build_primary_lineage_interval_phase_plan(
            {
                "lineage_object_id": "lineage_path::SUM159_NLS_2N_O2_A7K_harvest",
                "lineage_object_type": "LineagePath",
                "root_event_id": "SUM-159_NLS_mCherry",
                "endpoint_event_ids": ["SUM159_NLS_2N_O2_A7K_harvest"],
                "lineage_path_event_ids": [
                    "SUM-159_NLS_mCherry",
                    "SUM-159_NLS_2N_A3_seed",
                    "SUM-159_NLS_2N_dp_seed",
                    "SUM-159_NLS_2N_dp_seedT1",
                    "SUM-159_NLS_2N_O2_A1_seed",
                    "SUM-159_NLS_2N_O2_A1_seedT1",
                    "SUM-159_NLS_2N_O2_A7_seed",
                    "SUM-159_NLS_2N_O2_A7_seedT2",
                    "SUM-159_NLS_2N_O2_A7K_seed",
                    "SUM159_NLS_2N_O2_A7K_harvest",
                ],
                "passaging_records": [
                    {"id": "SUM-159_NLS_mCherry", "date": "2024-01-01 00:00:00", "event": "harvest", "passage": 1, "cellCount": 1},
                    {"id": "SUM-159_NLS_2N_A3_seed", "date": "2024-01-02 00:00:00", "event": "seed", "passage": 2, "cellCount": 2, "passaged_from_id1": "SUM-159_NLS_mCherry"},
                    {"id": "SUM-159_NLS_2N_dp_seed", "date": "2024-01-03 00:00:00", "event": "seed", "passage": 3, "cellCount": 3, "passaged_from_id1": "SUM-159_NLS_2N_A3_seed"},
                    {"id": "SUM-159_NLS_2N_dp_seedT1", "date": "2024-01-04 00:00:00", "event": "harvest", "passage": 3, "cellCount": 4, "passaged_from_id1": "SUM-159_NLS_2N_dp_seed"},
                    {"id": "SUM-159_NLS_2N_O2_A1_seed", "date": "2024-01-05 00:00:00", "event": "seed", "passage": 4, "cellCount": 5, "passaged_from_id1": "SUM-159_NLS_2N_dp_seedT1"},
                    {"id": "SUM-159_NLS_2N_O2_A1_seedT1", "date": "2024-01-06 00:00:00", "event": "harvest", "passage": 4, "cellCount": 6, "passaged_from_id1": "SUM-159_NLS_2N_O2_A1_seed"},
                    {"id": "SUM-159_NLS_2N_O2_A7_seed", "date": "2024-01-07 00:00:00", "event": "seed", "passage": 5, "cellCount": 7, "passaged_from_id1": "SUM-159_NLS_2N_O2_A1_seedT1"},
                    {"id": "SUM-159_NLS_2N_O2_A7_seedT2", "date": "2024-01-08 00:00:00", "event": "harvest", "passage": 5, "cellCount": 8, "passaged_from_id1": "SUM-159_NLS_2N_O2_A7_seed"},
                    {"id": "SUM-159_NLS_2N_O2_A7K_seed", "date": "2024-01-09 00:00:00", "event": "seed", "passage": 6, "cellCount": 9, "passaged_from_id1": "SUM-159_NLS_2N_O2_A7_seedT2"},
                    {"id": "SUM159_NLS_2N_O2_A7K_harvest", "date": "2024-01-10 00:00:00", "event": "harvest", "passage": 6, "cellCount": 10, "passaged_from_id1": "SUM-159_NLS_2N_O2_A7K_seed"},
                ],
                "perspective_records": [{"origin": "SUM159_NLS_2N_O2_A7K_harvest", "size": 1.0}],
                "lineage_object_features": {"phenotype_time_span_days": 9.0},
            },
            branch_id="SUM159_2N_O2",
        )
        milestone = build_milestone_matched_primary_lineage_interval_phase_plan(
            anchor_plan=anchor,
            comparison_plan=comparison,
        )
        labels = [x["milestone_label"] for x in milestone["matched_milestone_phases"]]
        self.assertIn("O2_A7K_harvest", labels)
        a7k = next(x for x in milestone["matched_milestone_phases"] if x["milestone_label"] == "O2_A7K_harvest")
        self.assertEqual(a7k["anchor_phase"]["child_event_id"], "SUM159_NLS_4N_O2_A7K_harvest")
        self.assertEqual(a7k["comparison_phase"]["child_event_id"], "SUM159_NLS_2N_O2_A7K_harvest")
        self.assertTrue(milestone["endpoint_alignment"]["both_branches_contain_A7K_harvest"])
        self.assertTrue(milestone["endpoint_alignment"]["both_A7K_harvest_endpoints_have_perspective_support"])
        self.assertTrue(milestone["validation"]["terminal_A7K_harvest_endpoints_aligned"])
        self.assertTrue(milestone["validation"]["phase_index_matching_not_primary_alignment"])
        self.assertGreater(len(milestone["unmatched_pre_o2_phases"]["anchor"]), 0)
        self.assertGreater(len(milestone["unmatched_pre_o2_phases"]["comparison"]), 0)


if __name__ == "__main__":
    unittest.main()
