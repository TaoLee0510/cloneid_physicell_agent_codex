from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from cloneid_agent.trajectory_bundle_ranking import (
    rank_trajectory_bundle_payloads,
    score_trajectory_bundle_payload,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def build_bundle(
    *,
    bundle_id: str,
    connected_segment_count: int,
    event_graph_depth: int,
    event_count: int,
    transition_count: int,
    phenotype_observation_count: int,
    phenotype_time_span_days: float,
    terminal_perspective_support: int,
    calibration_validation_split_possible: bool,
    trajectory_bundle_complexity_penalty: int,
    has_branching: bool = False,
    has_longitudinal_context_change: bool = True,
) -> dict[str, object]:
    return {
        "bundle_id": bundle_id,
        "seed_candidate_segment_id": bundle_id.split("::")[-1],
        "perspective_records": [{"cloneID": "p1"}] if terminal_perspective_support else [],
        "trajectory_bundle_features": {
            "connected_segment_count": connected_segment_count,
            "event_graph_depth": event_graph_depth,
            "event_count": event_count,
            "transition_count": transition_count,
            "has_branching": has_branching,
            "has_longitudinal_context_change": has_longitudinal_context_change,
            "phenotype_observation_count": phenotype_observation_count,
            "phenotype_time_span_days": phenotype_time_span_days,
            "terminal_perspective_support": terminal_perspective_support,
            "identity_support_count": 0,
            "calibration_validation_split_possible": calibration_validation_split_possible,
            "trajectory_bundle_complexity_penalty": trajectory_bundle_complexity_penalty,
            "root_event_count": 1,
            "leaf_event_count": 1,
        },
    }


class TrajectoryBundleRankingTests(unittest.TestCase):
    def test_score_prefers_connected_phenotype_rich_bundle(self) -> None:
        strong = score_trajectory_bundle_payload(
            build_bundle(
                bundle_id="trajectory_bundle::strong",
                connected_segment_count=4,
                event_graph_depth=4,
                event_count=10,
                transition_count=4,
                phenotype_observation_count=8,
                phenotype_time_span_days=18.0,
                terminal_perspective_support=3,
                calibration_validation_split_possible=True,
                trajectory_bundle_complexity_penalty=1,
            )
        )
        sparse = score_trajectory_bundle_payload(
            build_bundle(
                bundle_id="trajectory_bundle::sparse",
                connected_segment_count=2,
                event_graph_depth=2,
                event_count=4,
                transition_count=1,
                phenotype_observation_count=2,
                phenotype_time_span_days=3.0,
                terminal_perspective_support=1,
                calibration_validation_split_possible=False,
                trajectory_bundle_complexity_penalty=0,
            )
        )
        self.assertGreater(
            strong["trajectory_bundle_score"],
            sparse["trajectory_bundle_score"],
        )
        self.assertGreater(
            strong["trajectory_bundle_score_components"]["phenotype_trajectory_strength"],
            sparse["trajectory_bundle_score_components"]["phenotype_trajectory_strength"],
        )

    def test_rank_payloads_sorts_descending_score(self) -> None:
        ranked = rank_trajectory_bundle_payloads(
            [
                build_bundle(
                    bundle_id="trajectory_bundle::low",
                    connected_segment_count=1,
                    event_graph_depth=1,
                    event_count=3,
                    transition_count=0,
                    phenotype_observation_count=2,
                    phenotype_time_span_days=2.0,
                    terminal_perspective_support=0,
                    calibration_validation_split_possible=False,
                    trajectory_bundle_complexity_penalty=0,
                ),
                build_bundle(
                    bundle_id="trajectory_bundle::high",
                    connected_segment_count=5,
                    event_graph_depth=4,
                    event_count=12,
                    transition_count=6,
                    phenotype_observation_count=10,
                    phenotype_time_span_days=21.0,
                    terminal_perspective_support=3,
                    calibration_validation_split_possible=True,
                    trajectory_bundle_complexity_penalty=2,
                ),
            ]
        )
        self.assertEqual(
            ranked["ranked_trajectory_bundles"][0]["bundle_id"],
            "trajectory_bundle::high",
        )
        self.assertEqual(ranked["score_model"], "trajectory_bundle_v1")

    def test_ranking_recomputes_stale_embedded_features(self) -> None:
        payload = build_bundle(
            bundle_id="trajectory_bundle::stale",
            connected_segment_count=1,
            event_graph_depth=1,
            event_count=3,
            transition_count=0,
            phenotype_observation_count=2,
            phenotype_time_span_days=2.0,
            terminal_perspective_support=0,
            calibration_validation_split_possible=False,
            trajectory_bundle_complexity_penalty=0,
        )
        payload["passaging_records"] = [
            {"id": "a", "passaged_from_id1": None, "passaged_from_id2": None, "correctedCount": 1, "date": "2024-01-01 00:00:00"},
            {"id": "b", "passaged_from_id1": "a", "passaged_from_id2": None, "correctedCount": 1, "date": "2024-01-02 00:00:00"},
            {"id": "c", "passaged_from_id1": "b", "passaged_from_id2": None, "correctedCount": 1, "date": "2024-01-03 00:00:00"},
        ]
        payload["context_transitions"] = []
        payload["perspective_records"] = []
        payload["identity_records"] = []
        payload["connected_candidate_segments"] = [{"dataset_id": "x"}]
        payload["phenotype_time_span_days"] = 2.0
        payload["trajectory_bundle_features"] = dict(payload["trajectory_bundle_features"])
        payload["trajectory_bundle_features"]["event_graph_depth"] = 0

        scored = score_trajectory_bundle_payload(payload)
        self.assertEqual(scored["trajectory_bundle_features"]["event_graph_depth"], 2)

    def test_rank_trajectory_bundles_cli_writes_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            first = Path(tmpdir) / "bundle_a.json"
            second = Path(tmpdir) / "bundle_b.json"
            out_dir = Path(tmpdir) / "ranked"
            out_dir.mkdir()
            first.write_text(
                json.dumps(
                    build_bundle(
                        bundle_id="trajectory_bundle::a",
                        connected_segment_count=2,
                        event_graph_depth=2,
                        event_count=5,
                        transition_count=1,
                        phenotype_observation_count=3,
                        phenotype_time_span_days=5.0,
                        terminal_perspective_support=1,
                        calibration_validation_split_possible=False,
                        trajectory_bundle_complexity_penalty=0,
                    )
                )
            )
            second.write_text(
                json.dumps(
                    build_bundle(
                        bundle_id="trajectory_bundle::b",
                        connected_segment_count=4,
                        event_graph_depth=4,
                        event_count=9,
                        transition_count=4,
                        phenotype_observation_count=7,
                        phenotype_time_span_days=15.0,
                        terminal_perspective_support=2,
                        calibration_validation_split_possible=True,
                        trajectory_bundle_complexity_penalty=1,
                    )
                )
            )
            env = os.environ.copy()
            env["PYTHONPATH"] = str(REPO_ROOT / "src")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "cloneid_agent",
                    "rank-trajectory-bundles",
                    "--input",
                    str(first),
                    str(second),
                    "--output-dir",
                    str(out_dir),
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(result.returncode, 0, msg=result.stderr)
            self.assertTrue((out_dir / "ranked_trajectory_bundles.json").exists())
            self.assertTrue((out_dir / "ranked_trajectory_bundles.md").exists())
            payload = json.loads((out_dir / "ranked_trajectory_bundles.json").read_text())
            self.assertEqual(payload["ranked_trajectory_bundles"][0]["bundle_id"], "trajectory_bundle::b")


if __name__ == "__main__":
    unittest.main()
