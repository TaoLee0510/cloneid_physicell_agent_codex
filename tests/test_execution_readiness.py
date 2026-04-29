from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cloneid_agent.execution_readiness import (
    build_execution_readiness_report,
    build_model_to_data_scaling_contract,
)
from cloneid_agent.model_family_specification import build_schedule_aware_model_family_specification
from cloneid_agent.phase_planning import (
    build_milestone_matched_primary_lineage_interval_phase_plan,
    build_primary_lineage_interval_phase_plan,
)
from cloneid_agent.schedule_aware_candidates import generate_schedule_aware_model_candidates
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
            {"id": f"{prefix}_root", "date": "2024-01-01 00:00:00", "event": "harvest", "passage": 1, "media": 10, "flask": 1, "cellCount": 1000000, "correctedCount": 900000, "areaOccupied_um2": 1000},
            {"id": f"{prefix}_dp_seed", "date": "2024-01-02 00:00:00", "event": "seeding", "passage": 2, "media": 10, "flask": 1, "cellCount": 1200000, "correctedCount": 1000000, "areaOccupied_um2": 1200, "passaged_from_id1": f"{prefix}_root"},
            {"id": f"{prefix}_dp_seedT1", "date": "2024-01-03 00:00:00", "event": "harvest", "passage": 2, "media": 10, "flask": 1, "cellCount": 2400000, "correctedCount": 2200000, "areaOccupied_um2": 2400, "passaged_from_id1": f"{prefix}_dp_seed"},
            {"id": f"{prefix}_O2_A1_seed", "date": "2024-01-03 01:00:00", "event": "seeding", "passage": 3, "media": 11, "flask": 2, "cellCount": 800000, "correctedCount": 700000, "areaOccupied_um2": 800, "passaged_from_id1": f"{prefix}_dp_seedT1"},
            {"id": f"{prefix}_O2_A1_seedT1", "date": "2024-01-04 01:00:00", "event": "harvest", "passage": 3, "media": 11, "flask": 2, "cellCount": 1600000, "correctedCount": 1400000, "areaOccupied_um2": 1600, "passaged_from_id1": f"{prefix}_O2_A1_seed"},
            {"id": f"{prefix}_O2_A2_seed", "date": "2024-01-04 02:00:00", "event": "seeding", "passage": 4, "media": 12, "flask": 2, "cellCount": 600000, "correctedCount": 500000, "areaOccupied_um2": 600, "passaged_from_id1": f"{prefix}_O2_A1_seedT1"},
            {"id": f"{prefix}_O2_A2_seedT2", "date": "2024-01-05 02:00:00", "event": "harvest", "passage": 4, "media": 12, "flask": 2, "cellCount": 1400000, "correctedCount": 1200000, "areaOccupied_um2": 1400, "passaged_from_id1": f"{prefix}_O2_A2_seed"},
            {"id": f"{prefix}_O2_A7K_seed", "date": "2024-01-05 03:00:00", "event": "seeding", "passage": 5, "media": 13, "flask": 3, "cellCount": 700000, "correctedCount": 600000, "areaOccupied_um2": 700, "passaged_from_id1": f"{prefix}_O2_A2_seedT2"},
            {"id": f"{prefix}_O2_A7K_harvest", "date": "2024-01-06 03:00:00", "event": "harvest", "passage": 5, "media": 13, "flask": 3, "cellCount": 1800000, "correctedCount": 1500000, "areaOccupied_um2": 1800, "passaged_from_id1": f"{prefix}_O2_A7K_seed"},
        ],
        "perspective_records": [
            {"origin": f"{prefix}_O2_A7K_harvest", "size": 1.0, "whichPerspective": f"p{idx}"}
            for idx in range(terminal_perspectives)
        ],
        "lineage_object_features": {"phenotype_time_span_days": 5.0},
    }


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


def _fixture():
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


class ExecutionReadinessTests(unittest.TestCase):
    def test_scaling_contract_and_readiness_share_objective(self) -> None:
        anchor_schedule, comparison_schedule, matched_schedule, specification = _fixture()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            physicell_root = _make_fake_physicell_root(tmp_path / "physicell")
            generated = generate_schedule_aware_model_candidates(
                anchor_schedule=anchor_schedule,
                comparison_schedule=comparison_schedule,
                matched_schedule=matched_schedule,
                specification_payload=specification,
                output_dir=tmp_path / "run",
                physicell_root=physicell_root,
            )
            candidate_root = Path(generated["candidate_root"])
            families = ["neutral_growth", "fixed_state_fitness", "density_dependent_growth"]
            evaluation_plans = {
                family: json.loads((candidate_root / family / "evaluation_plan.json").read_text())
                for family in families
            }
            parameter_payloads = {
                family: json.loads((candidate_root / family / "parameter_placeholders.json").read_text())
                for family in families
            }
            scaling = build_model_to_data_scaling_contract(
                anchor_schedule=anchor_schedule,
                comparison_schedule=comparison_schedule,
                matched_schedule=matched_schedule,
                evaluation_plans=evaluation_plans,
                parameter_placeholders=parameter_payloads,
            )
            readiness = build_execution_readiness_report(
                candidate_root=candidate_root,
                scaling_contract=scaling,
            )
            self.assertGreaterEqual(scaling["cells_per_agent"], 1)
            self.assertTrue(scaling["within_agent_count_guardrail"])
            self.assertEqual(
                scaling["shared_objective_reference"]["neutral_growth"]["primary_shared_objective"],
                scaling["shared_objective_reference"]["fixed_state_fitness"]["primary_shared_objective"],
            )
            self.assertEqual(
                scaling["shared_objective_reference"]["neutral_growth"]["primary_shared_objective"],
                scaling["shared_objective_reference"]["density_dependent_growth"]["primary_shared_objective"],
            )
            self.assertFalse(
                scaling["shared_objective_reference"]["neutral_growth"]["endpoint_validation"]["fitting_targets"]
            )
            self.assertTrue(readiness["shared_objective_invariants"]["primary_fit_targets_identical_across_families"])
            self.assertTrue(readiness["shared_objective_invariants"]["primary_fit_target_weights_identical_across_families"])
            self.assertTrue(readiness["shared_objective_invariants"]["endpoint_perspective_size_not_used_for_fitting"])
            self.assertTrue(readiness["shared_objective_invariants"]["schedule_mapping_identical_across_candidates"])
            self.assertTrue(readiness["shared_objective_invariants"]["prehistory_context_non_executable"])
            self.assertTrue(readiness["shared_objective_invariants"]["transfer_events_have_non_positive_simulated_duration"])
            self.assertTrue(readiness["family_readiness"]["neutral_growth"]["ready_for_syntax_dry_run"])
            self.assertFalse(readiness["family_readiness"]["neutral_growth"]["ready_for_biological_simulation"])
            self.assertTrue(readiness["family_readiness"]["fixed_state_fitness"]["family_specific_parameters_present"])
            self.assertTrue(readiness["family_readiness"]["density_dependent_growth"]["density_proxy_handling_specified"])


if __name__ == "__main__":
    unittest.main()
