from __future__ import annotations

import unittest

from cloneid_agent.dataset_scoring import (
    CandidateDatasetSummary,
    rank_candidate_datasets,
    score_candidate_dataset,
)


class DatasetScoringTests(unittest.TestCase):
    def test_score_candidate_dataset_uses_documented_five_point_scale(self) -> None:
        summary = CandidateDatasetSummary(
            dataset_id="toy_dataset_001",
            event_history_available=True,
            repeated_phenotype_measurements=True,
            endpoint_molecular_readout=True,
            sufficient_context_for_initialization=True,
            multiple_plausible_mechanisms=True,
        )
        scored = score_candidate_dataset(summary)
        self.assertEqual(scored.score, 5)
        self.assertEqual(len(scored.reasons), 5)

    def test_rank_candidate_datasets_sorts_descending_score(self) -> None:
        low = CandidateDatasetSummary(
            dataset_id="dataset_b",
            event_history_available=True,
            repeated_phenotype_measurements=False,
            endpoint_molecular_readout=False,
            sufficient_context_for_initialization=False,
            multiple_plausible_mechanisms=False,
        )
        high = CandidateDatasetSummary(
            dataset_id="dataset_a",
            event_history_available=True,
            repeated_phenotype_measurements=True,
            endpoint_molecular_readout=True,
            sufficient_context_for_initialization=False,
            multiple_plausible_mechanisms=True,
        )
        ranked = rank_candidate_datasets([low, high])
        self.assertEqual([item.dataset_id for item in ranked], ["dataset_a", "dataset_b"])
        self.assertEqual([item.score for item in ranked], [4, 1])


if __name__ == "__main__":
    unittest.main()
