"""Config-driven runner for the manuscript-facing SNU-668 density-history workflow."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .applications.rk_benchmark import run_rk_benchmark


def load_application_config(path: str | Path) -> dict[str, Any]:
    """Load dependency-free JSON-compatible YAML config."""

    text = Path(path).read_text()
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{path} must be JSON-compatible YAML because PyYAML is not a project dependency"
        ) from exc


def run_application(
    *,
    config_path: str | Path,
    output: str | Path,
    mode: str = "mock",
    external_zip: str | None = None,
    fit: bool = True,
    make_figures: bool = True,
    run_physicell: bool = False,
    physicell_root: str | Path | None = None,
    execute_physicell: bool = False,
    physicell_runtime_max_time: int = 60,
) -> dict[str, Any]:
    """Run the flagship SNU-668 density-history application from a config file."""

    config = load_application_config(config_path)
    resolved_external = external_zip or config.get("external_zip") or config.get("external_comparator", {}).get(
        "source_root_preferred"
    )
    output_dir = run_rk_benchmark(
        external_zip=resolved_external,
        cloneid_root_id=config.get("cloneid_root_id", "auto"),
        mode=mode,
        output=output,
        fit=fit,
        make_figures=make_figures,
        config_path=str(config_path),
        run_physicell=run_physicell,
        physicell_root=physicell_root,
        execute_physicell=execute_physicell,
        physicell_runtime_max_time=physicell_runtime_max_time,
    )
    return {
        "output_dir": str(output_dir),
        "mode": mode,
        "config_path": str(config_path),
        "application": "snu668_density_history",
    }
