from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

from cloneid_agent.rk_publication_record_extraction import extract_nwaa124_publication_record

from rk_fixture_utils import make_nwaa124_fixture_zip


class Nwaa124PublicationRecordTests(unittest.TestCase):
    def test_model_records_capture_figure_9_and_10(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            payload = extract_nwaa124_publication_record(make_nwaa124_fixture_zip(tmp), tmp / "out")
            records = payload["model_records"]
            r2_by_family = {
                row["model_family"]: row["reported_r_squared"]
                for row in records["growth_model_fit_statistics"]
            }
            self.assertEqual(r2_by_family["logistic"], 0.856)
            formulas = {row["population"]: row for row in records["carrying_capacity_logistic_formulas"]}
            self.assertEqual(formulas["r"]["carrying_capacity"], 228280.0)
            self.assertEqual(formulas["K"]["growth_rate_parameter"], 1.0549)

    def test_plot_only_evidence_is_not_misclassified_as_raw_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            extract_nwaa124_publication_record(make_nwaa124_fixture_zip(tmp), tmp / "out")
            competition_path = tmp / "out" / "nwaa124_reconstructed_competition_inputs.csv"
            with competition_path.open(newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertGreaterEqual(len(rows), 3)
            self.assertTrue(all(row["fit_status"] == "embedded_plot_digitization_required" for row in rows))
            self.assertTrue(all(row["record_status"] == "embedded_plot_or_representative_image" for row in rows))


if __name__ == "__main__":
    unittest.main()
