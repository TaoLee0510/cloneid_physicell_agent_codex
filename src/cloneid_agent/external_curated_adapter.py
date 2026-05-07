"""Load semi-structured curated external comparator datasets."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


REQUIRED_TABLES = (
    "competition_over_time.csv",
    "growth_capacity_summary.csv",
    "phenotype_support.csv",
)
OPTIONAL_TABLES = ("observational_evidence.csv",)
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


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    missing_columns = [column for column in PROVENANCE_COLUMNS if column not in (rows[0].keys() if rows else [])]
    if missing_columns:
        raise ValueError(f"{path} is missing required provenance columns: {missing_columns}")
    return rows


def _table_missingness(table_name: str, rows: list[dict[str, str]]) -> dict[str, Any]:
    missing_by_column = {
        column: sum(1 for row in rows if not (row.get(column) or "").strip())
        for column in PROVENANCE_COLUMNS
    }
    unavailable_rows = [
        idx
        for idx, row in enumerate(rows, start=1)
        if "unavailable" in (row.get("notes", "") + " " + row.get("value", "")).lower()
        or "figure-only" in (row.get("notes", "") + " " + row.get("value", "")).lower()
    ]
    return {
        "table": table_name,
        "row_count": len(rows),
        "missing_by_column": missing_by_column,
        "rows_marked_unavailable_or_figure_only": unavailable_rows,
    }


def load_external_curated_dataset(root: str | Path) -> dict[str, Any]:
    """Load the curated comparator and preserve explicit missingness.

    The returned object intentionally does not coerce these rows into a
    CLONEID-like event ledger. That absence is part of the comparator.
    """
    root = Path(root)
    manifest_path = root / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Curated manifest not found: {manifest_path}")
    manifest = json.loads(manifest_path.read_text())

    tables: dict[str, list[dict[str, str]]] = {}
    table_status: dict[str, dict[str, Any]] = {}
    for table_name in REQUIRED_TABLES + OPTIONAL_TABLES:
        path = root / table_name
        if path.exists():
            rows = _read_csv(path)
            tables[table_name] = rows
            table_status[table_name] = {
                "present": True,
                "path": str(path),
                "row_count": len(rows),
            }
        elif table_name in REQUIRED_TABLES:
            table_status[table_name] = {
                "present": False,
                "path": str(path),
                "row_count": 0,
            }
        else:
            table_status[table_name] = {
                "present": False,
                "path": str(path),
                "row_count": 0,
                "optional": True,
            }

    missing_required_tables = [
        name for name in REQUIRED_TABLES if not table_status.get(name, {}).get("present")
    ]
    if missing_required_tables:
        raise FileNotFoundError(f"Missing required curated tables: {missing_required_tables}")

    all_rows = [
        {**row, "curated_table": table_name}
        for table_name, rows in tables.items()
        for row in rows
    ]
    missingness = {
        "table_missingness": [
            _table_missingness(table_name, rows) for table_name, rows in tables.items()
        ],
        "dataset_level_missingness": [
            "no CLONEID-style event_id / parent_event_id ledger",
            "no continuous event-linked crowding history",
            "no exact text-tabulated competition time-series points",
            "no direct SNU-668 biological equivalence",
        ],
    }
    unsupported_assumptions = list(manifest.get("unsupported_assumptions", []))
    unsupported_assumptions.extend(
        [
            "continuous density history cannot be reconstructed from the curated external supplement alone",
            "terminal omics or pathway evidence cannot be treated as longitudinal density phenotype",
        ]
    )

    return {
        "dataset_regime": "nwaa124_curated_external",
        "dataset_type": "semi_structured_external_comparator",
        "manifest": manifest,
        "table_status": table_status,
        "tables": tables,
        "records": all_rows,
        "missingness": missingness,
        "unsupported_assumptions": sorted(set(unsupported_assumptions)),
        "observability_flags": {
            "event_linked_history": False,
            "sparse_published_view": True,
            "competition_summaries_present": bool(tables.get("competition_over_time.csv")),
            "growth_capacity_summaries_present": bool(tables.get("growth_capacity_summary.csv")),
            "phenotype_support_present": bool(tables.get("phenotype_support.csv")),
            "exact_time_series_points_present": False,
            "external_cell_line": "HeLa",
        },
    }


def summarize_external_curated_dataset(dataset: dict[str, Any]) -> str:
    lines = [
        "# External Comparator",
        "",
        f"- Regime: `{dataset['dataset_regime']}`",
        f"- Dataset type: `{dataset['dataset_type']}`",
        f"- Source root: `{dataset['manifest'].get('source_root')}`",
        "",
        "## Tables",
        "",
    ]
    for name, status in dataset["table_status"].items():
        lines.append(f"- `{name}`: present `{status['present']}`, rows `{status['row_count']}`")
    lines.extend(["", "## Missingness", ""])
    for item in dataset["missingness"]["dataset_level_missingness"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Unsupported assumptions", ""])
    for item in dataset["unsupported_assumptions"]:
        lines.append(f"- {item}")
    return "\n".join(lines) + "\n"
