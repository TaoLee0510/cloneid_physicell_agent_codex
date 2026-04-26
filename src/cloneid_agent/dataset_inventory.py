"""Candidate-dataset inventory wrapper around the approved cloneid R interface."""

from __future__ import annotations

import subprocess
from pathlib import Path

from .db import repository_root


def candidate_inventory_script_path() -> Path:
    """Return the path to the R candidate-inventory wrapper."""
    return repository_root() / "scripts" / "cloneid_candidate_inventory.R"


def run_candidate_inventory(output: str | None = None, run_id: str | None = None, mode: str = "auto") -> int:
    """Run the candidate-dataset inventory wrapper."""
    script = candidate_inventory_script_path()
    if not script.exists():
        raise FileNotFoundError(f"Candidate inventory script not found: {script}")

    cmd = ["Rscript", str(script), "--mode", mode]
    if output:
        cmd.extend(["--output", output])
    if run_id:
        cmd.extend(["--run-id", run_id])

    result = subprocess.run(cmd, cwd=repository_root(), check=False)
    return result.returncode
