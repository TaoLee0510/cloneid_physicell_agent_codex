from __future__ import annotations

import unittest
from pathlib import Path

from cloneid_agent.comparative_identifiability import build_comparative_identifiability
from cloneid_agent.compressed_view import build_published_like_compressed_view
from cloneid_agent.external_curated_adapter import load_external_curated_dataset
from cloneid_agent.family_comparison import build_family_comparison
from cloneid_agent.history_ablation import build_history_ablation
from cloneid_agent.history_covariates import build_dry_run_snu668_fixture, build_history_covariates
from cloneid_agent.observability_profile import build_observability_profile


REPO_ROOT = Path(__file__).resolve().parents[1]


class ComparativeIdentifiabilityTests(unittest.TestCase):
    def test_identifiability_marks_sparse_regimes_partially_unresolved(self) -> None:
        dataset = build_dry_run_snu668_fixture()
        covariates = build_history_covariates(dataset)
        compressed = build_published_like_compressed_view(dataset, covariates)
        ablation = build_history_ablation(covariates, compressed)
        external = load_external_curated_dataset(REPO_ROOT / "data/external/nwaa124_curated")
        observability = build_observability_profile(
            history_covariates=covariates,
            compressed_view=compressed,
            external_comparator=external,
        )
        comparison = build_family_comparison(
            observability_profile=observability,
            history_ablation=ablation,
        )
        identifiability = build_comparative_identifiability(
            observability_profile=observability,
            family_comparison=comparison,
            history_ablation=ablation,
        )
        summaries = {item["dataset_regime"]: item for item in identifiability["summaries"]}
        self.assertIn("partially unresolved", summaries["snu668_published_like_compressed"]["resolution_statement"])
        self.assertIn("partially unresolved", summaries["nwaa124_curated_external"]["resolution_statement"])
        self.assertIn("event_id and parent_event_id ledger", identifiability["low_cost_fields_that_rescue_identifiability"])


if __name__ == "__main__":
    unittest.main()
