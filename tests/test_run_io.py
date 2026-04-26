from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from cloneid_agent.run_io import (
    DEFAULT_DRY_RUN_SUBDIRS,
    ensure_subdirectories,
    generate_run_id,
    initialize_dry_run_tree,
    prepare_run_directory,
    write_json,
    write_markdown,
)


class RunIoTests(unittest.TestCase):
    def test_generate_run_id_uses_prefix(self) -> None:
        run_id = generate_run_id(prefix="inventory")
        self.assertTrue(run_id.startswith("inventory_"))

    def test_prepare_run_directory_refuses_overwrite_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir)
            run_dir = prepare_run_directory(base, run_id="fixed_run")
            self.assertTrue(run_dir.exists())
            with self.assertRaises(FileExistsError):
                prepare_run_directory(base, run_id="fixed_run")

    def test_initialize_dry_run_tree_creates_expected_subdirs(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            run_dir = Path(tmpdir) / "run_a"
            run_dir.mkdir()
            created = initialize_dry_run_tree(run_dir)
            self.assertEqual(set(created.keys()), set(DEFAULT_DRY_RUN_SUBDIRS))
            for subdir in DEFAULT_DRY_RUN_SUBDIRS:
                self.assertTrue((run_dir / subdir).exists())

    def test_write_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            json_path = write_json(tmp / "nested" / "artifact.json", {"a": 1, "b": ["x"]})
            md_path = write_markdown(tmp / "nested" / "artifact.md", "# Title\n")

            self.assertEqual(json.loads(json_path.read_text()), {"a": 1, "b": ["x"]})
            self.assertEqual(md_path.read_text(), "# Title\n")

    def test_ensure_subdirectories_returns_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            created = ensure_subdirectories(tmpdir, ("alpha", "beta"))
            self.assertEqual(set(created.keys()), {"alpha", "beta"})
            self.assertTrue(created["alpha"].exists())
            self.assertTrue(created["beta"].exists())


if __name__ == "__main__":
    unittest.main()
