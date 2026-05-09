"""Compatibility adapter for publication-level external comparator summaries."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


PROVENANCE_COLUMNS = (
    "source_file",
    "source_location",
    "assay_or_context",
    "selection_regime",
    "metric",
    "value",
    "units",
    "time_or_passage",
    "replicate_scope",
    "confidence",
    "notes",
)


def load_external_curated_dataset(root: str | Path) -> dict[str, Any]:
    """Load a 5.4-style curated comparator directory when present.

    The 5.5 flagship path extracts NSR records directly from docx/zip. This
    adapter remains available for validation/fallback curated CSVs and preserves
    explicit missingness instead of coercing the comparator into CLONEID format.
    """

    root = Path(root)
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        return publication_level_external_stub(source_root=root)
    manifest = json.loads(manifest_path.read_text())
    tables: dict[str, list[dict[str, str]]] = {}
    table_status: dict[str, dict[str, Any]] = {}
    for table_name in (
        "competition_over_time.csv",
        "growth_capacity_summary.csv",
        "phenotype_support.csv",
        "observational_evidence.csv",
    ):
        path = root / table_name
        if path.exists():
            with path.open(newline="") as handle:
                rows = list(csv.DictReader(handle))
            missing = [col for col in PROVENANCE_COLUMNS if rows and col not in rows[0]]
            if missing:
                raise ValueError(f"{path} is missing required provenance columns: {missing}")
            tables[table_name] = rows
            table_status[table_name] = {"present": True, "path": str(path), "row_count": len(rows)}
        else:
            table_status[table_name] = {"present": False, "path": str(path), "row_count": 0}
    all_rows = [
        {**row, "curated_table": table_name}
        for table_name, rows in tables.items()
        for row in rows
    ]
    payload = publication_level_external_stub(source_root=root)
    payload.update(
        {
            "manifest": manifest,
            "table_status": table_status,
            "tables": tables,
            "records": all_rows,
        }
    )
    return payload


def publication_level_external_stub(source_root: str | Path | None = None) -> dict[str, Any]:
    return {
        "dataset_regime": "nwaa124_curated_external",
        "dataset_type": "publication_level_external_comparator",
        "source_root": str(source_root) if source_root else "",
        "records": [],
        "missingness": {
            "dataset_level_missingness": [
                "no CLONEID-style event_id / parent_event_id ledger",
                "no continuous event-linked crowding history",
                "no native seed-harvest-transfer event schedule",
            ]
        },
        "unsupported_assumptions": [
            "continuous density history cannot be inferred from the publication-level supplement alone",
            "embedded plots are not raw numeric time-series tables without deterministic digitization",
            "HeLa and SNU-668 are not treated as biologically equivalent",
        ],
        "observability_flags": {
            "event_linked_history": False,
            "sparse_publication_view": True,
            "competition_summaries_present": True,
            "growth_capacity_summaries_present": True,
            "phenotype_support_present": True,
            "exact_time_series_points_present": False,
        },
    }


def summarize_external_curated_dataset(dataset: dict[str, Any]) -> str:
    lines = [
        "# External Comparator",
        "",
        f"- Regime: `{dataset['dataset_regime']}`",
        f"- Dataset type: `{dataset['dataset_type']}`",
        "",
        "## Missingness",
        "",
    ]
    for item in dataset["missingness"]["dataset_level_missingness"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Unsupported Assumptions", ""])
    for item in dataset["unsupported_assumptions"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)
