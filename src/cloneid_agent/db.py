"""Database access notes and helpers for the CLONEID-PhysiCell agent.

The current approved CLONEID access path uses the installed ``cloneid`` R
package. The first inventory wrapper shells out to an R script that calls
``cloneid::connect2DB()`` and executes explicit read-only ``DBI`` queries.

This module remains intentionally small for now because the initial database
inventory is implemented through that R interface rather than a direct Python
SQLAlchemy client.
"""

from __future__ import annotations

from pathlib import Path


def repository_root() -> Path:
    """Return the repository root from the installed source layout."""
    return Path(__file__).resolve().parents[2]


def inventory_script_path() -> Path:
    """Return the path to the R inventory wrapper."""
    return repository_root() / "scripts" / "cloneid_inventory.R"
