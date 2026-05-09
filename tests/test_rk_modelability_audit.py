from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from cloneid_agent.external_comparators.nwaa124 import RECORD_STATUS_LABELS
from cloneid_agent.rk_modelability_audit import AUDIT_DIMENSIONS, build_modelability_audit_rows, write_modelability_audit_csv


class RkModelabilityAuditTests(unittest.TestCase):
    def test_audit_uses_controlled_record_status_labels(self) -> None:
        rows = build_modelability_audit_rows()
        self.assertEqual([row["dimension"] for row in rows], list(AUDIT_DIMENSIONS))
        allowed = set(RECORD_STATUS_LABELS)
        status_columns = [
            "snu668_full_history",
            "snu668_published_like_compressed",
            "nwaa124_curated_external",
        ]
        for row in rows:
            for column in status_columns:
                self.assertIn(row[column], allowed)

    def test_audit_csv_is_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = write_modelability_audit_csv(Path(tmpdir) / "audit.csv")
            text = path.read_text()
            self.assertIn("confluence_proxy", text)
            self.assertIn("not_agent_ready_without_manual_reconstruction", text)


if __name__ == "__main__":
    unittest.main()
