"""Mock CLONEID SNU-668 native records and publication-level downsampling."""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
import math
from statistics import mean, pstdev
from typing import Any


FLASK_AREA_CM2 = 25.0


def _confluence(area_occupied_um2: float, flask_area_cm2: float = FLASK_AREA_CM2) -> float:
    flask_area_um2 = flask_area_cm2 * 100_000_000.0
    return round(area_occupied_um2 / flask_area_um2, 6)


def _event(
    *,
    event_id: str,
    parent_event_id: str | None,
    event_type: str,
    branch_label: str,
    replicate_id: str,
    passage_number: int,
    date_time: str,
    cell_count: int,
    corrected_count: int,
    area_occupied_um2: float,
    cell_size_um2: float,
    selection_regime: str,
) -> dict[str, Any]:
    return {
        "event_id": event_id,
        "id": event_id,
        "parent_event_id": parent_event_id,
        "passaged_from_id1": parent_event_id,
        "event_type": event_type,
        "event": event_type,
        "date_time": date_time,
        "date": date_time,
        "cell_line": "SNU-668",
        "cellLine": "SNU-668",
        "root_id": "SNU668_rK_mock_root",
        "branch_label": branch_label,
        "replicate_id": replicate_id,
        "passage_number": passage_number,
        "passage": passage_number,
        "selection_regime": selection_regime,
        "media": "RPMI_10FBS_mock",
        "flask_id": "T25_mock",
        "flask": "T25_mock",
        "flask_area_cm2": FLASK_AREA_CM2,
        "cellCount": cell_count,
        "correctedCount": corrected_count,
        "areaOccupied_um2": area_occupied_um2,
        "cellSize_um2": cell_size_um2,
        "confluence_proxy": _confluence(area_occupied_um2),
        "image_uri": f"mock://SNU668/{event_id}.png",
        "field_position": "center",
        "magnification": "10x",
        "segmentation_version": "mock_segmentation_v1",
        "image_QC_flag": "pass",
        "notes": "Deterministic mock record for CLONEID-LTE r/K benchmark.",
    }


def build_mock_cloneid_full_record(root_id: str | None = None) -> dict[str, Any]:
    """Build a deterministic event-linked SNU-668 r/K mock record."""

    resolved_root = root_id if root_id and root_id != "auto" else "SNU668_rK_mock_root"
    root_event = _event(
        event_id="SNU668_root_seed",
        parent_event_id=None,
        event_type="seeding",
        branch_label="IN",
        replicate_id="root",
        passage_number=0,
        date_time="2024-01-01 08:00:00",
        cell_count=100_000,
        corrected_count=98_000,
        area_occupied_um2=95_000_000.0,
        cell_size_um2=950.0,
        selection_regime="initial expansion",
    )
    root_event["root_id"] = resolved_root

    branch_specs = {
        "r": {
            "replicate_id": "SNU668_r_rep1",
            "selection_regime": "r-selection low-density transfer",
            "seed_counts": [50_000, 62_000, 70_000, 76_000],
            "harvest_counts": [303_000, 244_000, 179_000, 126_000],
            "seed_dates": ["2024-01-02 08:00:00", "2024-01-05 10:00:00", "2024-01-08 12:00:00", "2024-01-11 14:00:00"],
            "harvest_dates": ["2024-01-05 08:00:00", "2024-01-08 10:00:00", "2024-01-11 12:00:00", "2024-01-14 14:00:00"],
            "cell_size": [930.0, 980.0, 1050.0, 1120.0],
        },
        "K": {
            "replicate_id": "SNU668_K_rep1",
            "selection_regime": "K-selection high-density transfer",
            "seed_counts": [50_000, 70_000, 92_000, 118_000],
            "harvest_counts": [331_000, 348_000, 343_000, 330_000],
            "seed_dates": ["2024-01-02 08:30:00", "2024-01-05 10:30:00", "2024-01-08 12:30:00", "2024-01-11 14:30:00"],
            "harvest_dates": ["2024-01-05 08:30:00", "2024-01-08 10:30:00", "2024-01-11 12:30:00", "2024-01-14 14:30:00"],
            "cell_size": [900.0, 920.0, 940.0, 960.0],
        },
    }

    events = [root_event]
    for branch_label, spec in branch_specs.items():
        parent = root_event["event_id"]
        for idx, seed_count in enumerate(spec["seed_counts"], start=1):
            harvest_count = spec["harvest_counts"][idx - 1]
            seed_cell_size = spec["cell_size"][idx - 1]
            harvest_cell_size = spec["cell_size"][idx - 1] + (160.0 if branch_label == "r" else 70.0)
            flask_area_um2 = FLASK_AREA_CM2 * 100_000_000.0
            density_factor = 5.0 + idx * 2.0
            seed_area = min(seed_count * seed_cell_size * density_factor, flask_area_um2 * 0.92)
            harvest_area = min(harvest_count * harvest_cell_size * (density_factor + 1.5), flask_area_um2 * 0.96)
            seed_event_id = f"SNU668_{branch_label}_P{idx}_seed"
            harvest_event_id = f"SNU668_{branch_label}_P{idx}_harvest"
            seed = _event(
                event_id=seed_event_id,
                parent_event_id=parent,
                event_type="seeding",
                branch_label=branch_label,
                replicate_id=spec["replicate_id"],
                passage_number=idx,
                date_time=spec["seed_dates"][idx - 1],
                cell_count=seed_count,
                corrected_count=round(seed_count * 0.98),
                area_occupied_um2=seed_area,
                cell_size_um2=seed_cell_size,
                selection_regime=spec["selection_regime"],
            )
            harvest = _event(
                event_id=harvest_event_id,
                parent_event_id=seed_event_id,
                event_type="harvest",
                branch_label=branch_label,
                replicate_id=spec["replicate_id"],
                passage_number=idx,
                date_time=spec["harvest_dates"][idx - 1],
                cell_count=harvest_count,
                corrected_count=round(harvest_count * (0.91 if branch_label == "r" else 0.96)),
                area_occupied_um2=harvest_area,
                cell_size_um2=harvest_cell_size,
                selection_regime=spec["selection_regime"],
            )
            seed["root_id"] = resolved_root
            harvest["root_id"] = resolved_root
            events.extend([seed, harvest])
            parent = harvest_event_id

    perspectives = [
        {
            "Perspective_id": "SNU668_r_endpoint_karyotype",
            "assay_event_id": "SNU668_r_P4_harvest",
            "upstream_event_id": "SNU668_r_P4_seed",
            "branch_label": "r",
            "whichPerspective": "KaryotypePerspective",
            "clone_or_state_weights": {"r_like": 0.78, "K_like": 0.22},
            "feature_matrix_pointer": "mock://perspective/SNU668_r_endpoint/features.csv",
            "raw_data_pointer": "mock://perspective/SNU668_r_endpoint/raw",
            "QC_flag": "pass",
        },
        {
            "Perspective_id": "SNU668_K_endpoint_karyotype",
            "assay_event_id": "SNU668_K_P4_harvest",
            "upstream_event_id": "SNU668_K_P4_seed",
            "branch_label": "K",
            "whichPerspective": "KaryotypePerspective",
            "clone_or_state_weights": {"r_like": 0.19, "K_like": 0.81},
            "feature_matrix_pointer": "mock://perspective/SNU668_K_endpoint/features.csv",
            "raw_data_pointer": "mock://perspective/SNU668_K_endpoint/raw",
            "QC_flag": "pass",
        },
    ]
    identity = [
        {
            "cloneID": "SNU668_identity_secondary_r",
            "sampleSource": "SNU668_r_P4_harvest",
            "branch_label": "r",
            "size": 0.78,
            "usage": "secondary inferred support only",
        },
        {
            "cloneID": "SNU668_identity_secondary_K",
            "sampleSource": "SNU668_K_P4_harvest",
            "branch_label": "K",
            "size": 0.81,
            "usage": "secondary inferred support only",
        },
    ]
    return {
        "source": "deterministic_mock",
        "cell_line": "SNU-668",
        "root_id": resolved_root,
        "passaging_records": events,
        "perspective_records": perspectives,
        "identity_records": identity,
        "usage_rules": [
            "Transfer/passaging events are not biological growth episodes.",
            "Endpoint Perspective is validation/support only, not fitting.",
            "Identity is inferred secondary support only.",
        ],
    }


def build_event_graph(passaging_records: list[dict[str, Any]]) -> dict[str, Any]:
    nodes = [
        {
            "event_id": row["event_id"],
            "event_type": row["event_type"],
            "branch_label": row["branch_label"],
            "passage_number": row["passage_number"],
            "date_time": row["date_time"],
        }
        for row in passaging_records
    ]
    edges = [
        {"source": row["parent_event_id"], "target": row["event_id"], "edge_type": "passaged_from_id1"}
        for row in passaging_records
        if row.get("parent_event_id")
    ]
    return {"nodes": nodes, "edges": edges}


def _parse_datetime(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


def build_growth_episode_table(passaging_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_parent: dict[str, list[dict[str, Any]]] = {}
    by_id = {row["event_id"]: row for row in passaging_records}
    for row in passaging_records:
        parent = row.get("parent_event_id")
        if parent:
            by_parent.setdefault(parent, []).append(row)

    episodes: list[dict[str, Any]] = []
    for seed in passaging_records:
        if seed["event_type"] != "seeding":
            continue
        harvests = [child for child in by_parent.get(seed["event_id"], []) if child["event_type"] == "harvest"]
        for harvest in harvests:
            start = _parse_datetime(seed["date_time"])
            end = _parse_datetime(harvest["date_time"])
            duration_hours = (end - start).total_seconds() / 3600.0
            start_count = float(seed.get("correctedCount") or 0.0)
            end_count = float(harvest.get("correctedCount") or 0.0)
            if duration_hours <= 0 or start_count <= 0 or end_count <= 0:
                continue
            growth_rate = math.log(end_count / start_count) / duration_hours if start_count > 0 and end_count > 0 else 0.0
            episodes.append(
                {
                    "episode_id": f"{seed['event_id']}__to__{harvest['event_id']}",
                    "seed_event_id": seed["event_id"],
                    "harvest_event_id": harvest["event_id"],
                    "branch_label": seed["branch_label"],
                    "replicate_id": seed["replicate_id"],
                    "passage_number": seed["passage_number"],
                    "duration_hours": duration_hours,
                    "seeded_cell_count": seed["cellCount"],
                    "harvested_cell_count": harvest["cellCount"],
                    "seed_corrected_count": seed["correctedCount"],
                    "harvest_corrected_count": harvest["correctedCount"],
                    "seed_areaOccupied_um2": seed["areaOccupied_um2"],
                    "harvest_areaOccupied_um2": harvest["areaOccupied_um2"],
                    "seed_cellSize_um2": seed["cellSize_um2"],
                    "harvest_cellSize_um2": harvest["cellSize_um2"],
                    "seed_confluence_proxy": seed["confluence_proxy"],
                    "harvest_confluence_proxy": harvest["confluence_proxy"],
                    "growth_rate_per_hour": growth_rate,
                    "selection_regime": seed["selection_regime"],
                    "record_status": "structured_numeric_table",
                }
            )
    return episodes


def build_event_schedule(passaging_records: list[dict[str, Any]]) -> dict[str, Any]:
    sorted_events = sorted(passaging_records, key=lambda row: row["date_time"])
    schedule_events: list[dict[str, Any]] = []
    for row in sorted_events:
        parent = row.get("parent_event_id")
        classification = row["event_type"]
        if row["event_type"] == "seeding" and parent:
            classification = "transfer_or_bottleneck"
        schedule_events.append(
            {
                "event_id": row["event_id"],
                "parent_event_id": parent,
                "event_type": row["event_type"],
                "schedule_classification": classification,
                "branch_label": row["branch_label"],
                "date_time": row["date_time"],
                "cellCount": row["cellCount"],
                "correctedCount": row["correctedCount"],
                "confluence_proxy": row["confluence_proxy"],
            }
        )
    return {
        "events": schedule_events,
        "rule": "Transfer/passaging events are explicit schedule resets and are not fitted as biological growth episodes.",
    }


def build_spatial_phenotype_table(passaging_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "event_id": row["event_id"],
            "branch_label": row["branch_label"],
            "event_type": row["event_type"],
            "cellCount": row["cellCount"],
            "correctedCount": row["correctedCount"],
            "areaOccupied_um2": row["areaOccupied_um2"],
            "cellSize_um2": row["cellSize_um2"],
            "flask_area_cm2": row["flask_area_cm2"],
            "confluence_proxy": row["confluence_proxy"],
            "image_uri": row["image_uri"],
            "segmentation_version": row["segmentation_version"],
            "image_QC_flag": row["image_QC_flag"],
            "record_status": "structured_numeric_table",
        }
        for row in passaging_records
    ]


def build_perspective_endpoint_table(perspective_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in perspective_records:
        rows.append(
            {
                "Perspective_id": record["Perspective_id"],
                "assay_event_id": record["assay_event_id"],
                "upstream_event_id": record["upstream_event_id"],
                "branch_label": record["branch_label"],
                "whichPerspective": record["whichPerspective"],
                "clone_or_state_weights": record["clone_or_state_weights"],
                "feature_matrix_pointer": record["feature_matrix_pointer"],
                "raw_data_pointer": record["raw_data_pointer"],
                "QC_flag": record["QC_flag"],
                "usage": "endpoint validation/support only, not fitting",
                "record_status": "structured_numeric_table",
            }
        )
    return rows


def downsample_cloneid_record(full_record: dict[str, Any]) -> dict[str, Any]:
    """Collapse native CLONEID records to a publication-level coarse summary."""

    episodes = build_growth_episode_table(full_record["passaging_records"])
    by_branch: dict[str, list[dict[str, Any]]] = {}
    for episode in episodes:
        by_branch.setdefault(episode["branch_label"], []).append(episode)

    growth_summary: list[dict[str, Any]] = []
    for branch, branch_episodes in sorted(by_branch.items()):
        rates = [float(row["growth_rate_per_hour"]) for row in branch_episodes]
        folds = [
            float(row["harvest_corrected_count"]) / float(row["seed_corrected_count"])
            for row in branch_episodes
            if float(row["seed_corrected_count"]) > 0
        ]
        growth_summary.append(
            {
                "branch_label": branch,
                "episode_count": len(branch_episodes),
                "mean_growth_rate_per_hour": mean(rates),
                "sd_growth_rate_per_hour": pstdev(rates) if len(rates) > 1 else 0.0,
                "mean_fold_change": mean(folds),
                "record_status": "structured_numeric_table",
            }
        )

    endpoint_summary = [
        {
            "branch_label": record["branch_label"],
            "whichPerspective": record["whichPerspective"],
            "clone_or_state_weights": record["clone_or_state_weights"],
            "record_status": "method_text_only",
        }
        for record in full_record["perspective_records"]
    ]
    missingness = {
        "event_ids_removed": True,
        "parent_child_event_graph_removed": True,
        "seed_harvest_transfer_records_removed": True,
        "per_event_image_provenance_removed": True,
        "per_event_confluence_removed": True,
        "Perspective_to_event_linkage_removed": True,
        "density_models_status": "not_identifiable_due_to_missing_event_level_density_or_event_graph",
    }
    return {
        "source": "CLONEID full native record downsampled to publication-level coarse record",
        "cell_line": full_record["cell_line"],
        "branch_labels": sorted(by_branch),
        "selection_protocol_summary": {
            "r": "low-density transfer summary retained",
            "K": "high-density transfer summary retained",
            "record_status": "method_text_only",
        },
        "coarse_growth_summary": growth_summary,
        "endpoint_molecular_summary": endpoint_summary,
        "missingness_profile": missingness,
        "guardrail": "No event IDs, event graph, per-event image provenance, confluence proxy, or Perspective-event linkage are retained.",
    }


def write_csv_rows(path: str | Path, rows: list[dict[str, Any]]) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        target.write_text("")
        return target
    fieldnames = list(rows[0].keys())
    with target.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return target
