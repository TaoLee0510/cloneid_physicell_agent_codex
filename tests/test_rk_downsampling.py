from __future__ import annotations

import json
import unittest

from cloneid_agent.rk_downsampling import build_event_graph, build_growth_episode_table, build_mock_cloneid_full_record, downsample_cloneid_record


class RkDownsamplingTests(unittest.TestCase):
    def test_downsampling_removes_event_linkage(self) -> None:
        full = build_mock_cloneid_full_record("auto")
        graph = build_event_graph(full["passaging_records"])
        episodes = build_growth_episode_table(full["passaging_records"])
        coarse = downsample_cloneid_record(full)

        self.assertGreater(len(graph["edges"]), 0)
        self.assertGreater(len(episodes), 0)
        self.assertTrue(coarse["missingness_profile"]["event_ids_removed"])
        self.assertTrue(coarse["missingness_profile"]["parent_child_event_graph_removed"])
        self.assertNotIn("SNU668_r_P1_seed", json.dumps(coarse))
        self.assertEqual(
            coarse["missingness_profile"]["density_models_status"],
            "not_identifiable_due_to_missing_event_level_density_or_event_graph",
        )


if __name__ == "__main__":
    unittest.main()
