# Status checkpoint

This file is maintained by the agent. It should be updated at the end of each work session or before stopping.

---

## What changed since last checkpoint

- Read the required project guidance set:
  - `README.md`
  - `CODEX_INSTRUCTIONS.md`
  - `SUPERVISED_AUTONOMY.md`
  - `ONBOARDING_AND_SCOPE.md`
  - `AGENT_WORKFLOW.md`
  - `DATABASE_ACCESS.md`
  - `RUNTIME_AND_HPC.md`
  - `docs/CLONEID_SCHEMA_NOTES.md`
- Inspected the repository scaffold, source placeholders, model-template folders, and coordination files.
- Created Milestone 0 planning artifacts:
  - `docs/derived/repository_map.md`
  - `docs/derived/milestone0_plan.md`
- Updated `WORK_QUEUE.md` and `QUESTION_QUEUE.md` with blocked branches and safe offline work.
- Incorporated the user's new answers from `QUESTION_QUEUE.md`.
- Inspected the installed `cloneid` R package interface and documented the read-only inventory path.
- Implemented the read-only CLONEID inventory wrapper in R plus a Python CLI entry point.
- Added tests for mock inventory, graceful live-failure fallback, and report/JSON output structure.
- Verified the wrapper in mock mode, fallback mode, and live mode.
- Drafted the derived CLONEID schema map from documentation plus live table/field inspection.
- Added strict schema objects for inventory artifacts and validated them against generated mock output.

---

## What works now

- The project scope, constraints, and unattended-work protocol have been translated into current coordination files.
- Milestone 0 documentation now exists for safe offline progress without touching the real CLONEID database or PhysiCell runtime.
- The repository scaffold has been classified into existing files, placeholders, operationally empty folders, and minimal missing implementation files.
- The approved database access path is now known: use the installed `cloneid` R package with preconfigured credentials.
- The first real-data selection policy is now fixed: keep it score-driven until reviewed.
- The package interface note now documents the actual connection helper, visible tables, snapshot row counts, core fields, and the recommended read-only `DBI` inventory pattern.
- A manual inventory entry point now exists in both forms:
  - `Rscript scripts/cloneid_inventory.R ...`
  - `python -m cloneid_agent inventory ...`
- The wrapper writes:
  - `runs/<run_id>/database_inventory.json`
  - `runs/<run_id>/database_inventory.md`
- `--mode mock` works offline.
- `--mode auto` gracefully falls back to mock output when sandboxed live access fails.
- `--mode live` has been verified with network-capable execution against the live CLONEID database.
- A first derived schema map now exists in `docs/derived/cloneid_schema_map.md`, including the first-pass join graph and table roles for the agent.
- `src/cloneid_agent/schemas.py` now validates database inventory artifacts and rejects malformed structure.

---

## What is blocked

- PhysiCell smoke testing is blocked pending an installation/runtime decision.
- The next real-data branch still needs candidate-dataset inventory and dataset scoring logic beyond the table-level wrapper.
- Any scientific dataset-selection branch remains blocked until higher-level inventory/scoring exists.

---

## Questions needing user input

See `QUESTION_QUEUE.md`.

---

## Recommended next action when user returns

Review the inventory wrapper, schema map, and artifact schemas, then continue the deterministic database-first slice with generic run-folder writers and higher-level candidate-dataset inventory/scoring.

---

## Files most worth reviewing

- `docs/derived/repository_map.md`
- `docs/derived/milestone0_plan.md`
- `docs/derived/cloneid_package_interface.md`
- `docs/derived/cloneid_schema_map.md`
- `scripts/cloneid_inventory.R`
- `src/cloneid_agent/cli.py`
- `src/cloneid_agent/inventory.py`
- `src/cloneid_agent/schemas.py`
- `tests/test_inventory_cli.py`
- `tests/test_schemas.py`
- `QUESTION_QUEUE.md`
- `WORK_QUEUE.md`
- `STATUS.md`
