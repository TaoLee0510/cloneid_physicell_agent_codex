"""Deterministic candidate-dataset scoring rules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateDatasetSummary:
    dataset_id: str
    event_history_available: bool
    repeated_phenotype_measurements: bool
    endpoint_molecular_readout: bool
    sufficient_context_for_initialization: bool
    multiple_plausible_mechanisms: bool


@dataclass(frozen=True)
class DatasetScore:
    dataset_id: str
    score: int
    reasons: list[str]


def score_candidate_dataset(summary: CandidateDatasetSummary) -> DatasetScore:
    """Score a candidate dataset from 0 to 5 using documented modelability rules."""
    score = 0
    reasons: list[str] = []

    if summary.event_history_available:
        score += 1
        reasons.append("event history available")
    if summary.repeated_phenotype_measurements:
        score += 1
        reasons.append("repeated phenotype measurements available")
    if summary.endpoint_molecular_readout:
        score += 1
        reasons.append("endpoint Perspective or Identity available")
    if summary.sufficient_context_for_initialization:
        score += 1
        reasons.append("experimental context sufficient for initialization")
    if summary.multiple_plausible_mechanisms:
        score += 1
        reasons.append("multiple plausible mechanisms distinguishable")

    return DatasetScore(dataset_id=summary.dataset_id, score=score, reasons=reasons)


def rank_candidate_datasets(candidates: list[CandidateDatasetSummary]) -> list[DatasetScore]:
    """Score and rank datasets by descending score, then dataset_id."""
    scored = [score_candidate_dataset(candidate) for candidate in candidates]
    return sorted(scored, key=lambda item: (-item.score, item.dataset_id))
