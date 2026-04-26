# Repository Map

## Purpose

This repository is currently a scaffold for a constrained CLONEID-to-PhysiCell workflow. It contains project guidance, empty run/data/report locations, placeholder Python source, and placeholder PhysiCell model-family folders.

## Top-level layout

- `README.md`
  - Project overview, intended dry-run CLI, expected run outputs, and scientific endpoint.
- `CODEX_INSTRUCTIONS.md`
  - Implementation brief and non-negotiable constraints for the coding agent.
- `SUPERVISED_AUTONOMY.md`
  - Decision-risk framework and coordination-file protocol.
- `ONBOARDING_AND_SCOPE.md`
  - Milestone sequence and explicit first-stage non-goals.
- `AGENT_WORKFLOW.md`
  - Scientific workflow, scoring logic, mapping targets, and required report contents.
- `DATABASE_ACCESS.md`
  - Read-only database policy, adapter expectations, provenance requirements, and first-pass table targets.
- `RUNTIME_AND_HPC.md`
  - Dry-run, local-test, and HPC execution tiers.
- `QUESTION_QUEUE.md`, `WORK_QUEUE.md`, `STATUS.md`
  - Live coordination files.
- `docs/`
  - `CLONEID_SCHEMA_NOTES.md`: schema-level notes for the handshake.
  - `derived/`: derived notes and planning artifacts, including Milestone 0 outputs.
- `src/cloneid_agent/`
  - `__init__.py`: package placeholder only.
  - `db.py`: database-access placeholder only.
- `model_templates/physicell/`
  - One folder per allowed model family, each containing only a README placeholder.
- `data/`
  - `README.md`: explains that live DB is the primary input.
  - `database_snapshots/`: scaffold only.
  - `processed/`: scaffold only.
- `runs/`
  - Empty run-output scaffold.
- `reports/`
  - Empty report-output scaffold.
- `tests/`
  - Empty test scaffold.

## Existing implementation-bearing files

At the moment, the repository contains documentation and only two Python package files:

- `src/cloneid_agent/__init__.py`
- `src/cloneid_agent/db.py`

Neither contains working logic yet.

## Placeholder source files

- `src/cloneid_agent/__init__.py`
  - Package placeholder docstring only.
- `src/cloneid_agent/db.py`
  - Placeholder module with a single `placeholder()` function raising `NotImplementedError`.

## Placeholder model-template folders

These folders exist, but each currently contains only a README instructing Codex to place template files or stubs there:

- `model_templates/physicell/neutral_growth/`
- `model_templates/physicell/fixed_state_fitness/`
- `model_templates/physicell/density_dependent_growth/`
- `model_templates/physicell/resource_limited_growth/`
- `model_templates/physicell/event_history_aware/`

## Operationally empty scaffold folders

These folders are present but contain no working artifacts beyond `.gitkeep` or structural intent:

- `data/database_snapshots/`
- `data/processed/`
- `reports/`
- `runs/`
- `tests/`

## Minimal missing files before implementation can begin

The repository can begin implementation without choosing a scientific direction, but it is missing core deterministic scaffolding:

- Python packaging / entrypoint:
  - `pyproject.toml` or equivalent packaging metadata
  - `src/cloneid_agent/__main__.py`
  - `src/cloneid_agent/cli.py`
- Deterministic workflow modules:
  - `src/cloneid_agent/schemas.py`
  - `src/cloneid_agent/inventory.py`
  - `src/cloneid_agent/dataset_scoring.py`
  - `src/cloneid_agent/observable_selection.py`
  - `src/cloneid_agent/physicell_mapping.py`
  - `src/cloneid_agent/simulation_runner.py`
  - `src/cloneid_agent/evaluation.py`
  - `src/cloneid_agent/report.py`
- Test scaffolding:
  - at least one test module under `tests/`
- Toy / fixture assets:
  - synthetic CLONEID-like fixture data for a toy round trip
  - minimal dry-run template/config stub format for candidate model folders

## External prerequisites not present in the repository

- Real CLONEID access details are not present:
  - no checked-in `.env`
  - no live `CLONEID_DB_READONLY_URL`
  - no database snapshot fixture
- PhysiCell runtime assets are not present:
  - no binary path
  - no build/install instructions
  - no checked-in example configuration or executable wrapper

## Risk classification notes

- Level 0
  - Documenting the existing scaffold and planning deterministic offline work.
- Level 2
  - Choosing the first real CLONEID dataset before inventory exists.
- Level 3
  - Inventing database credentials, schema behavior not evidenced by docs, or a manuscript-driving biological direction.
