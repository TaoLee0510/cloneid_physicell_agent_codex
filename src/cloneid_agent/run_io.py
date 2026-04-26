"""Generic run-folder and artifact-writer utilities."""

from __future__ import annotations

from datetime import datetime, UTC
import json
from pathlib import Path
from typing import Any


DEFAULT_DRY_RUN_SUBDIRS = (
    "database_cache",
    "evaluation",
    "figures",
    "model_candidates",
)


def generate_run_id(prefix: str = "run") -> str:
    """Generate a deterministic UTC timestamp-based run identifier."""
    return f"{prefix}_{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}"


def prepare_run_directory(
    base_dir: str | Path = "runs",
    run_id: str | None = None,
    *,
    prefix: str = "run",
    exist_ok: bool = False,
) -> Path:
    """Create a new run directory without overwriting by default."""
    root = Path(base_dir)
    root.mkdir(parents=True, exist_ok=True)
    resolved_run_id = run_id or generate_run_id(prefix=prefix)
    run_dir = root / resolved_run_id
    if run_dir.exists() and not exist_ok:
        raise FileExistsError(f"Run directory already exists: {run_dir}")
    run_dir.mkdir(parents=True, exist_ok=exist_ok)
    return run_dir


def ensure_subdirectories(run_dir: str | Path, subdirs: list[str] | tuple[str, ...]) -> dict[str, Path]:
    """Create a set of named subdirectories under a run directory."""
    root = Path(run_dir)
    created: dict[str, Path] = {}
    for name in subdirs:
        path = root / name
        path.mkdir(parents=True, exist_ok=True)
        created[name] = path
    return created


def initialize_dry_run_tree(run_dir: str | Path) -> dict[str, Path]:
    """Create the common dry-run directory tree."""
    return ensure_subdirectories(run_dir, DEFAULT_DRY_RUN_SUBDIRS)


def write_json(path: str | Path, payload: Any) -> Path:
    """Write JSON with stable formatting."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return target


def write_markdown(path: str | Path, content: str) -> Path:
    """Write Markdown text to disk."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)
    return target
