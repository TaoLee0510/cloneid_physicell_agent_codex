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
- Replaced the coarse candidate ranker with a fine-grained `0-100` score model that better separates repeated phenotype trajectories from sparse molecular-heavy candidates.
- Added a `fine-rank-candidates` CLI alias while switching `rank-candidates` itself to the new fine-grained model.
- Re-ranked the saved live candidate inventory and refreshed the selected-candidate artifact in `runs/live_candidate_ranking_20260426T022200/`.
- Incorporated the user's pinned PhysiCell backend decision across runtime and coordination docs.
- Added a concrete repo-owned PhysiCell planning scaffold for the pinned `v1.14.2` backend:
  - `docs/derived/physicell_runtime_plan.md`
  - `scripts/check_physicell_runtime.sh`
  - `docker/physicell-v1.14.2/Dockerfile`
  - `docker/physicell-v1.14.2/README.md`
  - `containers/apptainer/physicell-v1.14.2.def`
- Verified the planning scaffold locally with a shell syntax check and runtime environment check.
- Downloaded the official PhysiCell `v1.14.2` source release into `/tmp/PhysiCell-1.14.2-src`.
- Verified the expected macOS default-compiler failure mode:
  - plain `make` uses the default compiler path and fails on `-fopenmp`
- Successfully built PhysiCell `v1.14.2` locally with:
  - `env PHYSICELL_CPP=/opt/homebrew/bin/g++-15 make`
- Added a reusable local build wrapper:
  - `scripts/build_physicell_local.sh`
- Documented the successful local build check in:
  - `docs/derived/physicell_local_build_check.md`

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
- `python -m cloneid_agent fine-rank-candidates --input ... --output-dir ...` now aliases the same fine-grained ranking model.
- `python -m cloneid_agent select-candidate --input ... --output-dir ...` now selects the top-ranked dataset while preserving top-score ties for review.
- The saved live ranking is now materially more discriminative: the current `runs/live_candidate_ranking_20260426T022200/ranked_candidates.json` has `923` unique scores across `1519` candidates, instead of many coarse ties.
- The PhysiCell runtime decision is now fixed: use official PhysiCell core `v1.14.2`, run automated workflows through command-line template-generated jobs, avoid PhysiCell Studio as an execution dependency, and keep Docker and optional Apptainer/Singularity environments pinned to the same backend.
- A concrete pinned runtime scaffold now exists in-repo for all three supported backend surfaces:
  - local source build
  - project-owned Docker image
  - optional Apptainer/Singularity image
- Local runtime-check results on this machine are now documented by execution rather than assumption:
  - Homebrew `g++-15` is available
  - `make`, `clang++`, `cmake`, and Docker CLI are available
  - Docker daemon is not reachable from the current context
  - Apptainer and Singularity are not installed
- The first actual PhysiCell backend-execution branch is now validated:
  - official `v1.14.2` source can be downloaded successfully
  - the build succeeds on this machine when `PHYSICELL_CPP=/opt/homebrew/bin/g++-15` is set
  - the resulting executable path is:
    - `/tmp/PhysiCell-1.14.2-src/heterogeneity`

---

## What is blocked

- PhysiCell smoke testing still requires actual runtime assets to be downloaded or built locally.
- Docker-based execution remains blocked until the Docker daemon is reachable from the current context.
- Apptainer/Singularity execution remains blocked until one of those runtimes is installed.
- A stable persistent PhysiCell install location has not been chosen yet; the current successful build lives in `/tmp`.

---

## Questions needing user input

See `QUESTION_QUEUE.md`.

---

## Recommended next action when user returns

Await user confirmation on the completed first actual PhysiCell backend branch, then either:
- promote the successful build to a persistent location and run a first minimal PhysiCell smoke test, or
- switch back to the CLONEID extraction branch.

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
- `runs/live_candidate_ranking_20260426T022200/ranked_candidates.json`
- `runs/live_candidate_ranking_20260426T022200/selected_candidate.json`
- `docs/derived/physicell_runtime_plan.md`
- `docs/derived/physicell_local_build_check.md`
- `scripts/check_physicell_runtime.sh`
- `scripts/build_physicell_local.sh`
- `docker/physicell-v1.14.2/Dockerfile`
- `containers/apptainer/physicell-v1.14.2.def`
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
   - Completed the first actual PhysiCell backend-execution branch by downloading official PhysiCell `v1.14.2`, verifying the expected default-compiler failure, building successfully with `PHYSICELL_CPP=/opt/homebrew/bin/g++-15`, and adding a reusable local build wrapper plus a build-check note.
2. What safe next task did I identify?
   - Either run a first minimal PhysiCell smoke test from the successful local build, or switch back to the CLONEID extraction branch.
3. Is that next task read-only, reversible, deterministic, and not dependent on user judgment?
   - The smoke-test branch is reversible but not read-only because it would execute the built simulator and create outputs. The CLONEID extraction branch remains read-only, but the user asked me to stay on the PhysiCell branch until this checkpoint was ready.
4. If yes, why am I not doing it now?
   - I am stopping here because the user explicitly asked me to proceed to the next PhysiCell branch and then have them confirm once ready.
5. Am I blocked by:
   - missing credentials? no
   - missing permissions? not for the completed local build branch; future Docker or live DB work may still require them
   - risk of modifying the real database? no
   - scientific judgment requiring user input? no
   - Level 2 or Level 3 ambiguity? no
6. If I am not blocked, continue working instead of stopping.
   - I am stopping here only because the user requested confirmation before proceeding beyond this PhysiCell branch.

## Git state

- Current branch: `main`
- Last commit hash: `cc93d27`
- Tests run this session:
  - `bash -n scripts/check_physicell_runtime.sh`
  - `scripts/check_physicell_runtime.sh`
  - `bash -n scripts/build_physicell_local.sh`
  - `scripts/build_physicell_local.sh /tmp/PhysiCell-1.14.2-src`
  - `make` in `/tmp/PhysiCell-1.14.2-src` (expected OpenMP/compiler failure on default path)
  - `env PHYSICELL_CPP=/opt/homebrew/bin/g++-15 make` in `/tmp/PhysiCell-1.14.2-src`
- Work committed yet for the latest unit: no
- Uncommitted / user-side files currently present:
  - modified: `CODEX_INSTRUCTIONS.md`
  - modified: `ONBOARDING_AND_SCOPE.md`
  - modified: `README.md`
  - modified: `RUNTIME_AND_HPC.md`
  - modified: `SUPERVISED_AUTONOMY.md`
  - untracked: `GIT_WORKFLOW.md`
  - untracked: `ONTOLOGY_FOR_DATASET_RANKING.md`
  - untracked: `docs/CLONEID_paper.pdf`
