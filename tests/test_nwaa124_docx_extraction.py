from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from cloneid_agent.external_comparators.nwaa124 import inventory_external_archive
from cloneid_agent.rk_publication_record_extraction import extract_nwaa124_publication_record

from rk_fixture_utils import make_nwaa124_fixture_zip


class Nwaa124DocxExtractionTests(unittest.TestCase):
    def test_zip_inventory_detects_uploaded_file_classes(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = make_nwaa124_fixture_zip(Path(tmpdir))
            inventory = inventory_external_archive(zip_path)
            self.assertEqual(inventory["file_count"], 6)
            self.assertEqual(inventory["kind_counts"], {"docx": 2, "txt": 3, "vcf": 1})

    def test_table_5_and_figure_captions_are_extracted(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            zip_path = make_nwaa124_fixture_zip(tmp)
            extract_nwaa124_publication_record(zip_path, tmp / "out")
            table_path = tmp / "out" / "nwaa124_extracted_tables" / "supplementary_table_5_growth_rate_samples.csv"
            with table_path.open(newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(list(rows[0].keys()), ["Samples", "IN_G", "IN_R", "G3K", "R1K", "G3r", "R1r"])

            figure_index = json.loads((tmp / "out" / "nwaa124_supplement_figure_index.json").read_text())
            figure_numbers = {row["figure_number"] for row in figure_index}
            self.assertTrue({1, 4, 5, 9, 10, 13, 15}.issubset(figure_numbers))
            fig4 = next(row for row in figure_index if row["figure_number"] == 4)
            self.assertTrue(fig4["relevant_to_model_reconstruction"])


if __name__ == "__main__":
    unittest.main()
