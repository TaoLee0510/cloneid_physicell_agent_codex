"""Inventory command wrapper around the approved cloneid R interface."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from .db import inventory_script_path


def run_inventory(output: str | None = None, run_id: str | None = None, mode: str = "auto") -> int:
    """Run the read-only CLONEID inventory wrapper.

    Parameters are forwarded to ``scripts/cloneid_inventory.R``. The R script
    is responsible for live-vs-mock behavior, JSON/Markdown output generation,
    and graceful fallback when the live database is unavailable.
    """
    script = inventory_script_path()
    if not script.exists():
        raise FileNotFoundError(f"Inventory script not found: {script}")

    cmd = ["Rscript", str(script), "--mode", mode]
    if output:
        cmd.extend(["--output", output])
    if run_id:
        cmd.extend(["--run-id", run_id])

    result = subprocess.run(cmd, cwd=script.parent.parent, check=False)
    return result.returncode


def inventory_output_dir(output: str | None, run_id: str | None) -> Path:
    """Resolve the run directory that the inventory script will write to."""
    repo_root = inventory_script_path().parent.parent
    if output:
        return Path(output)
    return repo_root / "runs" / (run_id or "<generated-run-id>")


def main(argv: list[str] | None = None) -> int:
    """Entry point for ad hoc module execution."""
    from .cli import main as cli_main

    return cli_main(argv)


if __name__ == "__main__":
    sys.exit(main())
