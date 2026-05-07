"""Published-like compression for internal CLONEID history views."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .run_io import write_json, write_markdown


def build_published_like_compressed_view(
    dataset: dict[str, Any],
    history_covariates: dict[str, Any],
) -> dict[str, Any]:
    rows = history_covariates.get("covariate_rows", [])
    harvest_rows = [row for row in rows if row.get("event_type") == "harvest"]
    first = harvest_rows[0] if harvest_rows else (rows[0] if rows else {})
    last = harvest_rows[-1] if harvest_rows else (rows[-1] if rows else {})
    compressed_rows = [
        {
            "summary_record_id": "baseline_summary",
            "coarse_passage": first.get("passage_index"),
            "cell_count": first.get("cell_count"),
            "corrected_count": first.get("corrected_count"),
            "areaOccupied_um2": first.get("areaOccupied_um2"),
            "time_or_passage": "earliest available harvest summary",
            "source_event_ids": first.get("event_id"),
        },
        {
            "summary_record_id": "terminal_summary",
            "coarse_passage": last.get("passage_index"),
            "cell_count": last.get("cell_count"),
            "corrected_count": last.get("corrected_count"),
            "areaOccupied_um2": last.get("areaOccupied_um2"),
            "time_or_passage": "terminal available harvest summary",
            "source_event_ids": last.get("event_id"),
        },
    ]
    perspective_count = len(dataset.get("perspective_records", []))
    return {
        "dataset_regime": "snu668_published_like_compressed",
        "source_dataset_regime": dataset.get("dataset_regime", "snu668_full_history"),
        "compression_schema_version": "published_like_compressed_v1",
        "data_status": dataset.get("data_status", "unknown"),
        "compressed_rows": compressed_rows,
        "terminal_perspective_summary": {
            "perspective_record_count": perspective_count,
            "usage": "endpoint support only",
        },
        "removed_or_collapsed_information": [
            "explicit event-order context beyond coarse passage index",
            "cumulative confluence / crowding history",
            "transfer-event reset and bottleneck semantics as explanatory inputs",
            "continuous pre-assay history",
            "parent_event_id graph traversal context",
        ],
        "retained_information": [
            "coarse baseline and terminal phenotype summaries",
            "terminal Perspective support count",
            "cell-line label and broad density-selection context",
        ],
        "observability_flags": {
            "event_linked_history": False,
            "sparse_published_view": True,
            "coarse_passage_summary": True,
            "endpoint_support_present": perspective_count > 0,
            "continuous_density_history_present": False,
        },
    }


def render_compressed_view_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Published-Like Compressed View",
        "",
        f"- Regime: `{payload['dataset_regime']}`",
        f"- Source regime: `{payload['source_dataset_regime']}`",
        f"- Data status: `{payload.get('data_status')}`",
        "",
        "## Removed or collapsed information",
        "",
    ]
    for item in payload["removed_or_collapsed_information"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Retained information", ""])
    for item in payload["retained_information"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"


def write_compressed_view(output_dir: str | Path, payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    write_json(output_dir / "compressed_view.json", payload)
    write_markdown(output_dir / "compressed_view.md", render_compressed_view_markdown(payload))
    rows = payload.get("compressed_rows", [])
    if rows:
        with (output_dir / "compressed_view.csv").open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
