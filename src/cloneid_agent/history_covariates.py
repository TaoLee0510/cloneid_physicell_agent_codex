"""Event-linked history covariates for density-selection applications."""

from __future__ import annotations

from datetime import datetime
import csv
from pathlib import Path
from typing import Any

from .run_io import write_json, write_markdown


def build_dry_run_snu668_fixture() -> dict[str, Any]:
    """Return a clearly labeled dry-run fixture shaped like SNU-668 history.

    These records are schema-validation fixtures only. They are never presented
    as observed CLONEID data.
    """
    passaging_records = [
        {"id": "SNU668_P00_seed", "event": "seeding", "passage": 0, "date": "2025-01-01 09:00:00", "cellLine": "SNU-668", "growthType": "density_selection", "cellCount": 100000, "correctedCount": 95000, "areaOccupied_um2": 420000.0, "flask": "T25", "media": "mock_standard", "passaged_from_id1": None},
        {"id": "SNU668_P00_harvest", "event": "harvest", "passage": 0, "date": "2025-01-04 09:00:00", "cellLine": "SNU-668", "growthType": "density_selection", "cellCount": 520000, "correctedCount": 500000, "areaOccupied_um2": 2140000.0, "flask": "T25", "media": "mock_standard", "passaged_from_id1": "SNU668_P00_seed"},
        {"id": "SNU668_P01_seed", "event": "seeding", "passage": 1, "date": "2025-01-04 11:00:00", "cellLine": "SNU-668", "growthType": "density_selection", "cellCount": 115000, "correctedCount": 110000, "areaOccupied_um2": 500000.0, "flask": "T25", "media": "mock_standard", "passaged_from_id1": "SNU668_P00_harvest"},
        {"id": "SNU668_P01_harvest", "event": "harvest", "passage": 1, "date": "2025-01-07 11:00:00", "cellLine": "SNU-668", "growthType": "density_selection", "cellCount": 610000, "correctedCount": 585000, "areaOccupied_um2": 2600000.0, "flask": "T25", "media": "mock_standard", "passaged_from_id1": "SNU668_P01_seed"},
        {"id": "SNU668_P02_seed", "event": "seeding", "passage": 2, "date": "2025-01-07 13:00:00", "cellLine": "SNU-668", "growthType": "density_selection", "cellCount": 130000, "correctedCount": 122000, "areaOccupied_um2": 620000.0, "flask": "T25", "media": "mock_standard", "passaged_from_id1": "SNU668_P01_harvest"},
        {"id": "SNU668_P02_harvest", "event": "harvest", "passage": 2, "date": "2025-01-10 13:00:00", "cellLine": "SNU-668", "growthType": "density_selection", "cellCount": 750000, "correctedCount": 715000, "areaOccupied_um2": 3350000.0, "flask": "T25", "media": "mock_standard", "passaged_from_id1": "SNU668_P02_seed"},
        {"id": "SNU668_P03_seed", "event": "seeding", "passage": 3, "date": "2025-01-10 15:00:00", "cellLine": "SNU-668", "growthType": "density_selection", "cellCount": 140000, "correctedCount": 132000, "areaOccupied_um2": 700000.0, "flask": "T25", "media": "mock_standard", "passaged_from_id1": "SNU668_P02_harvest"},
        {"id": "SNU668_P03_harvest", "event": "harvest", "passage": 3, "date": "2025-01-13 15:00:00", "cellLine": "SNU-668", "growthType": "density_selection", "cellCount": 980000, "correctedCount": 930000, "areaOccupied_um2": 4550000.0, "flask": "T25", "media": "mock_standard", "passaged_from_id1": "SNU668_P03_seed"},
    ]
    perspective_records = [
        {
            "origin": "SNU668_P03_harvest",
            "whichPerspective": "terminal_mock_perspective",
            "size": 1.0,
            "state": "late_passaged_support",
            "evidence_class": "endpoint_support_only",
        }
    ]
    return {
        "dataset_regime": "snu668_full_history",
        "dataset_id": "snu668_density_history_dry_run_fixture",
        "lineage_object_id": "lineage_path::snu668_density_history_dry_run_fixture",
        "lineage_object_type": "LineagePath",
        "data_status": "mock_schema_fixture_not_observed_cloneid_data",
        "passaging_records": passaging_records,
        "perspective_records": perspective_records,
        "identity_records": [
            {
                "cloneID": "mock_identity_late_support",
                "origin": "SNU668_P03_harvest",
                "state": "inferred_secondary_support",
                "evidence_class": "inferred_identity_not_direct_phenotype",
            }
        ],
        "provenance_policy": {
            "database_source_of_truth": True,
            "dry_run_fixture": True,
            "no_database_writes": True,
            "perspective_usage": "endpoint support only",
            "identity_usage": "inferred secondary support only",
        },
    }


def _parse_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))


def build_history_covariates(dataset: dict[str, Any]) -> dict[str, Any]:
    records = sorted(
        dataset.get("passaging_records", []),
        key=lambda item: (_parse_datetime(item.get("date")) or datetime.min, str(item.get("id"))),
    )
    by_id = {record.get("id"): record for record in records}
    max_area = max(
        [float(record.get("areaOccupied_um2") or 0.0) for record in records] or [0.0]
    )
    max_count = max(
        [float(record.get("correctedCount") or record.get("cellCount") or 0.0) for record in records] or [0.0]
    )
    cumulative_area = 0.0
    cumulative_count = 0.0
    rows: list[dict[str, Any]] = []
    for order, record in enumerate(records):
        parent = by_id.get(record.get("passaged_from_id1"))
        date = _parse_datetime(record.get("date"))
        parent_date = _parse_datetime(parent.get("date")) if parent else None
        duration_hours = None
        if date and parent_date:
            duration_hours = round((date - parent_date).total_seconds() / 3600.0, 3)
        area = float(record.get("areaOccupied_um2") or 0.0)
        count = float(record.get("correctedCount") or record.get("cellCount") or 0.0)
        density_proxy = round(area / max_area, 6) if max_area else None
        count_proxy = round(count / max_count, 6) if max_count else None
        row = {
            "event_id": record.get("id"),
            "parent_event_id": record.get("passaged_from_id1"),
            "event_order_index": order,
            "timestamp": record.get("date"),
            "event_type": record.get("event"),
            "passage_index": record.get("passage"),
            "duration_hours_since_parent": duration_hours,
            "cell_count": record.get("cellCount"),
            "corrected_count": record.get("correctedCount"),
            "areaOccupied_um2": record.get("areaOccupied_um2"),
            "density_proxy_relative_area": density_proxy,
            "count_proxy_relative_max": count_proxy,
            "cumulative_area_history_proxy_before_event": round(cumulative_area, 6),
            "cumulative_count_history_proxy_before_event": round(cumulative_count, 6),
            "transfer_reset_semantics": bool(parent and parent.get("event") == "harvest" and record.get("event") == "seeding"),
            "derived_phenotype_provenance": "Passaging.areaOccupied_um2 and correctedCount are event-linked derived phenotype proxies when present; fixture values are mock in dry-run mode.",
        }
        rows.append(row)
        if density_proxy is not None:
            cumulative_area += density_proxy
        if count_proxy is not None:
            cumulative_count += count_proxy
    return {
        "dataset_regime": dataset.get("dataset_regime", "snu668_full_history"),
        "dataset_id": dataset.get("dataset_id"),
        "data_status": dataset.get("data_status", "unknown"),
        "covariate_schema_version": "history_covariates_v1",
        "covariate_rows": rows,
        "summary": {
            "event_count": len(records),
            "events_with_areaOccupied_um2": sum(1 for row in rows if row["areaOccupied_um2"] not in (None, "")),
            "events_with_correctedCount": sum(1 for row in rows if row["corrected_count"] not in (None, "")),
            "transfer_reset_count": sum(1 for row in rows if row["transfer_reset_semantics"]),
            "has_continuous_event_order_context": bool(rows),
            "has_cumulative_crowding_history_proxy": any(row["cumulative_area_history_proxy_before_event"] for row in rows),
        },
        "provenance": dataset.get("provenance_policy", {}),
    }


def render_history_covariates_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# History Covariates",
        "",
        f"- Dataset regime: `{payload.get('dataset_regime')}`",
        f"- Dataset id: `{payload.get('dataset_id')}`",
        f"- Data status: `{payload.get('data_status')}`",
        f"- Event count: `{payload['summary']['event_count']}`",
        f"- Transfer resets: `{payload['summary']['transfer_reset_count']}`",
        f"- Has cumulative crowding proxy: `{payload['summary']['has_cumulative_crowding_history_proxy']}`",
        "",
        "## Provenance note",
        "",
        "Perspective records are not longitudinal phenotype; Identity records are inferred secondary support only.",
    ]
    return "\n".join(lines) + "\n"


def write_history_covariates(output_dir: str | Path, payload: dict[str, Any]) -> None:
    output_dir = Path(output_dir)
    write_json(output_dir / "history_covariates.json", payload)
    write_markdown(output_dir / "history_covariates.md", render_history_covariates_markdown(payload))
    csv_path = output_dir / "history_covariates.csv"
    rows = payload.get("covariate_rows", [])
    if rows:
        with csv_path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)
