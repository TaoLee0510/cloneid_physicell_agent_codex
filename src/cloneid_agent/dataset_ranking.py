"""Ontology-aware ranking over candidate-dataset inventory records."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .dataset_scoring import CandidateDatasetSummary, DatasetScore, rank_candidate_datasets
from .run_io import write_json, write_markdown


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value in (0, 0.0, None, "", "FALSE", "False", "false"):
        return False
    return True


def summary_from_candidate_record(record: dict[str, Any]) -> CandidateDatasetSummary:
    """Map a grouped candidate-inventory record into the documented 0-to-5 summary."""
    dataset_id = str(record["dataset_id"])

    passaging_rows = int(record.get("passaging_rows", 0) or 0)
    harvest_events = int(record.get("harvest_events", 0) or 0)
    distinct_dates = int(record.get("distinct_dates", 0) or 0)
    lineage_link_rows = int(record.get("lineage_link_rows", 0) or 0)
    corrected_count_rows = int(record.get("corrected_count_rows", 0) or 0)
    area_rows = int(record.get("area_rows", 0) or 0)
    qupath_rows = int(record.get("qupath_rows", 0) or 0)
    perspective_rows = int(record.get("perspective_rows", 0) or 0)
    distinct_perspectives = int(record.get("distinct_perspectives", 0) or 0)
    distinct_perspective_states = int(record.get("distinct_perspective_states", 0) or 0)
    context_complete = _bool(record.get("context_complete", False))

    event_history_available = passaging_rows >= 2 and (lineage_link_rows >= 1 or harvest_events >= 1)

    repeated_phenotype_measurements = (
        distinct_dates >= 2
        and (
            corrected_count_rows >= 2
            or area_rows >= 2
            or qupath_rows >= 2
        )
    )

    endpoint_molecular_readout = perspective_rows > 0 or distinct_perspectives > 0

    # First-pass assumption: grouped context is sufficient when the grouping keys are present.
    sufficient_context_for_initialization = context_complete

    multiple_plausible_mechanisms = (
        repeated_phenotype_measurements
        and endpoint_molecular_readout
        and (
            distinct_perspective_states >= 2
            or area_rows >= 2
            or corrected_count_rows >= 2
            or qupath_rows >= 2
        )
    )

    return CandidateDatasetSummary(
        dataset_id=dataset_id,
        event_history_available=event_history_available,
        repeated_phenotype_measurements=repeated_phenotype_measurements,
        endpoint_molecular_readout=endpoint_molecular_readout,
        sufficient_context_for_initialization=sufficient_context_for_initialization,
        multiple_plausible_mechanisms=multiple_plausible_mechanisms,
    )


def rank_candidates_from_inventory_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Rank candidate datasets from a candidate-inventory payload."""
    candidates = payload.get("candidates", [])
    summaries = [summary_from_candidate_record(record) for record in candidates]
    ranked_scores = rank_candidate_datasets(summaries)

    score_map = {item.dataset_id: item for item in ranked_scores}
    ranked_candidates = []
    for record in candidates:
        score = score_map[record["dataset_id"]]
        ranked_candidates.append(
            {
                **record,
                "score": score.score,
                "score_reasons": score.reasons,
            }
        )

    ranked_candidates.sort(key=lambda item: (-item["score"], item["dataset_id"]))
    return {
        "source_run_id": payload.get("run_id"),
        "generated_from": "dataset_inventory.json",
        "grouping_definition": payload.get("grouping_definition"),
        "candidate_count": len(ranked_candidates),
        "ranked_candidates": ranked_candidates,
        "warnings": [
            "Ranking uses first-pass ontology-aware heuristics over grouped candidate inventory records.",
            "Perspective is treated as endpoint molecular evidence, not repeated phenotype.",
            "Identity is not yet included in first-pass ranking because the linkage rule remains unresolved in code.",
        ],
    }


def rank_candidates_from_file(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text())
    return rank_candidates_from_inventory_payload(payload)


def write_ranked_candidates(output_dir: str | Path, ranked_payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    write_json(output_dir / "ranked_candidates.json", ranked_payload)

    lines = [
        "# Ranked Candidates",
        "",
        f"- Candidate count: `{ranked_payload['candidate_count']}`",
        "",
        "| Rank | Dataset ID | Score | Reasons |",
        "|---:|---|---:|---|",
    ]
    for idx, record in enumerate(ranked_payload["ranked_candidates"], start=1):
        lines.append(
            f"| {idx} | `{record['dataset_id']}` | {record['score']} | {'; '.join(record['score_reasons'])} |"
        )
    if ranked_payload.get("warnings"):
        lines.extend(["", "## Warnings", ""])
        lines.extend([f"- {warning}" for warning in ranked_payload["warnings"]])
    write_markdown(output_dir / "ranked_candidates.md", "\n".join(lines) + "\n")
