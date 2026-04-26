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
- Added generic run-folder and artifact-writer helpers with passing tests.
- Added a synthetic CLONEID-like toy fixture and toy round-trip workflow with passing tests.
- Implemented the documented dataset-scoring rule with passing tests.
- Implemented higher-level candidate-dataset inventory, ontology-aware ranking, and deterministic top-candidate selection with passing tests.

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
- `src/cloneid_agent/run_io.py` now creates run directories, initializes dry-run subdirectories, and writes JSON/Markdown artifacts without overwriting run directories by default.
- `python -m cloneid_agent toy-roundtrip --output <dir>` now emits a minimal dry-run artifact bundle without real database access or a PhysiCell binary.
- `src/cloneid_agent/dataset_scoring.py` now encodes the documented 0-to-5 modelability rule and ranks candidate datasets deterministically.
- `python -m cloneid_agent candidate-inventory --mode live|auto|mock ...` now writes `dataset_inventory.json` and `dataset_inventory.md`.
- `python -m cloneid_agent rank-candidates --input ... --output-dir ...` now produces ontology-aware ranked candidate artifacts.
- `python -m cloneid_agent select-candidate --input ... --output-dir ...` now selects the top-ranked dataset while preserving top-score ties for review.

---

## What is blocked

- PhysiCell smoke testing is blocked pending an installation/runtime decision.
- The next meaningful branch, observable extraction from selected live datasets, is blocked by a Level 2 ambiguity: whether first-pass calibration/validation should rely on Perspective, Identity, or a specific split between them.
- Scientific dataset interpretation beyond score-driven ranking is blocked until that observable-policy ambiguity is resolved.

---

## Questions needing user input

See `QUESTION_QUEUE.md`.

---

## Recommended next action when user returns

Review the candidate inventory, ranking, and selection outputs, then answer the new observable-policy question before implementing selected-dataset record bundling and observable extraction.

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
- `src/cloneid_agent/run_io.py`
- `src/cloneid_agent/toy_workflow.py`
- `src/cloneid_agent/dataset_scoring.py`
- `src/cloneid_agent/dataset_inventory.py`
- `src/cloneid_agent/dataset_ranking.py`
- `src/cloneid_agent/dataset_selection.py`
- `tests/test_inventory_cli.py`
- `tests/test_schemas.py`
- `tests/test_run_io.py`
- `tests/test_toy_workflow.py`
- `tests/test_dataset_scoring.py`
- `tests/test_dataset_inventory_cli.py`
- `tests/test_dataset_ranking.py`
- `tests/test_dataset_selection.py`
- `QUESTION_QUEUE.md`
- `WORK_QUEUE.md`
- `STATUS.md`

---

## Stop checklist

1. What did I complete?
   - Implemented live/mock/auto candidate inventory, ontology-aware ranking, and deterministic top-candidate selection.
2. What safe next task did I identify?
   - Selected-dataset record bundling and observable extraction.
3. Is that next task read-only, reversible, deterministic, and not dependent on user judgment?
   - Not fully. The record-bundling mechanics are deterministic, but first-pass observable policy depends on how Perspective versus Identity should be used in calibration and validation.
4. If yes, why am I not doing it now?
   - Not applicable; the next branch is blocked by Level 2 ambiguity.
5. Am I blocked by:
   - missing credentials? no
   - missing permissions? no for the implemented branch; yes for default-sandbox live DB access, but escalation works
   - risk of modifying the real database? no, all implemented work is read-only
   - scientific judgment requiring user input? yes, for observable-policy interpretation
   - Level 2 or Level 3 ambiguity? yes, Level 2
6. If I am not blocked, continue working instead of stopping.
   - Current immediate branch is blocked, so this stop is justified.

## Git state

- Current branch: `main`
- Last completed commit before this status update: `e74b652`
- Tests run this session:
  - `PYTHONPATH=src python3 -m unittest tests/test_dataset_inventory_cli.py tests/test_dataset_ranking.py tests/test_dataset_selection.py tests/test_dataset_scoring.py tests/test_inventory_cli.py tests/test_schemas.py tests/test_run_io.py tests/test_toy_workflow.py`
- Work committed yet for the latest unit: not yet; status files are being updated before the final commit
