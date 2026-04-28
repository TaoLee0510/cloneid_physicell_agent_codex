from __future__ import annotations

import unittest

from cloneid_agent.phase_planning import (
    DEFAULT_PROOF_OF_PRINCIPLE_GUARDRAIL_MINUTES,
    DEFAULT_SIMULATED_DURATION_MINUTES,
    build_matched_primary_lineage_interval_phase_plan,
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


if __name__ == "__main__":
    unittest.main()
