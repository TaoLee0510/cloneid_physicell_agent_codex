"""Publication-like compression of CLONEID event-linked history."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from .run_io import write_json, write_markdown


def build_published_like_compressed_view(
    full_record: dict[str, Any],
    history_covariates: dict[str, Any],
    coarse_record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    rows = history_covariates.get("covariate_rows", [])
    harvest_rows = [row for row in rows if row.get("event_type") == "harvest"]
    first = harvest_rows[0] if harvest_rows else (rows[0] if rows else {})
    last = harvest_rows[-1] if harvest_rows else (rows[-1] if rows else {})
    compressed_rows = [
        {
            "summary_record_id": "baseline_summary",
            "coarse_passage": first.get("passage_index"),
            "branch_label": first.get("branch_label"),
            "cell_count": first.get("cell_count"),
            "corrected_count": first.get("corrected_count"),
            "areaOccupied_um2": first.get("areaOccupied_um2"),
            "time_or_passage": "earliest available harvest summary",
            "source_event_ids_removed_in_publication_view": True,
        },
        {
            "summary_record_id": "terminal_summary",
            "coarse_passage": last.get("passage_index"),
            "branch_label": last.get("branch_label"),
            "cell_count": last.get("cell_count"),
            "corrected_count": last.get("corrected_count"),
            "areaOccupied_um2": last.get("areaOccupied_um2"),
            "time_or_passage": "terminal available harvest summary",
            "source_event_ids_removed_in_publication_view": True,
        },
    ]
    perspective_count = len(full_record.get("perspective_records", []))
    missingness = coarse_record.get("missingness_profile", {}) if coarse_record else {}
    removed = [
        "event IDs",
        "parent-child event graph",
        "individual seed/harvest/transfer records",
        "per-event image provenance",
        "per-event confluence",
        "Perspective-to-event linkage",
        "cumulative confluence / crowding history",
        "transfer-event reset and bottleneck semantics as explanatory inputs",
    ]
    return {
        "dataset_regime": "snu668_published_like_compressed",
        "source_dataset_regime": "snu668_full_history",
        "compression_schema_version": "cloneid_publication_like_compressed_v2",
        "data_status": full_record.get("data_status", "deterministic_mock_schema_fixture_not_observed_cloneid_data"),
        "compressed_rows": compressed_rows,
        "coarse_growth_summary": coarse_record.get("coarse_growth_summary", []) if coarse_record else [],
        "terminal_perspective_summary": {
            "perspective_record_count": perspective_count,
            "usage": "endpoint support only; event linkage removed in the compressed view",
        },
        "removed_or_collapsed_information": removed,
        "retained_information": [
            "r/K branch labels",
            "group-level growth summaries",
            "high-level endpoint molecular summary",
            "selection protocol summary",
        ],
        "missingness_profile": missingness,
        "observability_flags": {
            "event_linked_history": False,
            "sparse_publication_view": True,
            "coarse_passage_summary": True,
            "endpoint_support_present": perspective_count > 0,
            "continuous_density_history_present": False,
            "event_level_confluence_removed": True,
        },
    }


def render_compressed_view_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Publication-Level Compressed View",
        "",
        f"- Regime: `{payload['dataset_regime']}`",
        f"- Source regime: `{payload['source_dataset_regime']}`",
        f"- Data status: `{payload.get('data_status')}`",
        "",
        "## Removed Or Collapsed Information",
        "",
    ]
    lines.extend(f"- {item}" for item in payload["removed_or_collapsed_information"])
    lines.extend(["", "## Retained Information", ""])
    lines.extend(f"- {item}" for item in payload["retained_information"])
    lines.append("")
    return "\n".join(lines)


def write_compressed_view(output_dir: str | Path, payload: dict[str, Any]) -> dict[str, Path]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths = {
        "json": write_json(output / "compressed_view.json", payload),
        "md": write_markdown(output / "compressed_view.md", render_compressed_view_markdown(payload)),
    }
    rows = payload.get("compressed_rows", [])
    csv_path = output / "compressed_view.csv"
    if rows:
        with csv_path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
    else:
        csv_path.write_text("")
    paths["csv"] = csv_path
    return paths
