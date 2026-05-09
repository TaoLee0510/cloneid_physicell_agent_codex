from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from cloneid_agent.applications.rk_benchmark import run_rk_benchmark
from cloneid_agent.cloneid_live_rk_extraction import (
    convert_live_rk_payload_to_full_record,
    parse_cloneid_root_ids,
)

from rk_fixture_utils import make_nwaa124_fixture_zip


def _live_payload() -> dict:
    return {
        "connection_method": "cloneid::connect2DB()",
        "root_ids": ["SNU-668_r2_A9_seed", "SNU-668_K3_A9_seed"],
        "passaging": [
            {
                "id": "SNU-668_r2_A9_seed",
                "event": "seeding",
                "passaged_from_id1": None,
                "passaged_from_id2": None,
                "cellLine": "SNU-668",
                "growthType": "r-selection",
                "passage": 9,
                "cellCount": 100,
                "correctedCount": 100,
                "date": "2024-01-01 00:00:00",
                "media": "RPMI",
                "flask": "T25",
                "areaOccupied_um2": 1000.0,
                "cellSize_um2": 10.0,
            },
            {
                "id": "SNU-668_r2_A9_harvest",
                "event": "harvest",
                "passaged_from_id1": "SNU-668_r2_A9_seed",
                "passaged_from_id2": None,
                "cellLine": "SNU-668",
                "growthType": "r-selection",
                "passage": 9,
                "cellCount": 200,
                "correctedCount": 190,
                "date": "2024-01-03 00:00:00",
                "media": "RPMI",
                "flask": "T25",
                "areaOccupied_um2": 2000.0,
                "cellSize_um2": 11.0,
            },
            {
                "id": "SNU-668_K3_A9_seed",
                "event": "seeding",
                "passaged_from_id1": None,
                "passaged_from_id2": None,
                "cellLine": "SNU-668",
                "growthType": "K-selection",
                "passage": 9,
                "cellCount": 100,
                "correctedCount": 100,
                "date": "2024-01-01 00:00:00",
                "media": "RPMI",
                "flask": "T25",
                "areaOccupied_um2": 1500.0,
                "cellSize_um2": 10.0,
            },
            {
                "id": "SNU-668_K3_A9_harvest",
                "event": "harvest",
                "passaged_from_id1": "SNU-668_K3_A9_seed",
                "passaged_from_id2": None,
                "cellLine": "SNU-668",
                "growthType": "K-selection",
                "passage": 9,
                "cellCount": 260,
                "correctedCount": 250,
                "date": "2024-01-03 00:00:00",
                "media": "RPMI",
                "flask": "T25",
                "areaOccupied_um2": 3000.0,
                "cellSize_um2": 11.0,
            },
        ],
        "flask": [{"id": "T25", "dishSurfaceArea_cm2": 25.0}],
        "qupath": [{"id": "SNU-668_r2_A9_seed", "image_uri": "cloneid://image/r"}],
        "perspective": [
            {
                "cloneID": "persp_r",
                "origin": "SNU-668_r2_A9_harvest",
                "whichPerspective": "KaryotypePerspective",
                "size": 1,
                "sampleSource": "SNU-668_r2_A9_harvest",
            }
        ],
        "identity": [{"cloneID": "identity_r", "sampleSource": "SNU-668_r2_A9_harvest"}],
    }


class CloneidLiveRkExtractionTests(unittest.TestCase):
    def test_parse_cloneid_root_ids_accepts_comma_or_space(self) -> None:
        self.assertEqual(
            parse_cloneid_root_ids("SNU-668_r2_A9_seed,SNU-668_K3_A9_seed"),
            ["SNU-668_r2_A9_seed", "SNU-668_K3_A9_seed"],
        )

    def test_convert_live_payload_to_full_record_preserves_branches(self) -> None:
        full = convert_live_rk_payload_to_full_record(
            _live_payload(),
            requested_root_ids=["SNU-668_r2_A9_seed", "SNU-668_K3_A9_seed"],
        )
        self.assertEqual(full["data_status"], "live_read_only_cloneid_extraction")
        events = {row["event_id"]: row for row in full["passaging_records"]}
        self.assertEqual(events["SNU-668_r2_A9_seed"]["branch_label"], "r")
        self.assertEqual(events["SNU-668_K3_A9_seed"]["branch_label"], "K")
        self.assertEqual(events["SNU-668_r2_A9_harvest"]["event_type"], "harvest")
        self.assertIsNotNone(events["SNU-668_K3_A9_seed"]["confluence_proxy"])
        self.assertEqual(full["perspective_records"][0]["assay_event_id"], "SNU-668_r2_A9_harvest")
        self.assertEqual(full["identity_records"][0]["usage"], "secondary inferred support only")

    def test_run_rk_benchmark_live_uses_live_extractor(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            full = convert_live_rk_payload_to_full_record(
                _live_payload(),
                requested_root_ids=["SNU-668_r2_A9_seed", "SNU-668_K3_A9_seed"],
            )
            with patch(
                "cloneid_agent.applications.rk_benchmark.load_live_cloneid_rk_record",
                return_value=full,
            ):
                output = run_rk_benchmark(
                    external_zip=str(make_nwaa124_fixture_zip(tmp)),
                    cloneid_root_id="SNU-668_r2_A9_seed,SNU-668_K3_A9_seed",
                    mode="live",
                    output=tmp / "run",
                    fit=True,
                    make_figures=False,
                )
            manifest = (output / "application_manifest.json").read_text()
            self.assertIn("live_read_only_cloneid_extraction_succeeded", manifest)
            subtree = (output / "cloneid_full" / "subtree_records.json").read_text()
            self.assertIn("SNU-668_r2_A9_seed", subtree)
            self.assertIn("SNU-668_K3_A9_seed", subtree)


if __name__ == "__main__":
    unittest.main()
