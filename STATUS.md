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
- Promoted the successful PhysiCell build to the persistent location:
  - `/Users/4470246/Downloads/PhysiCell-1.14.2`
- Ran the first minimal PhysiCell smoke test from the persistent install with:
  - `scripts/run_physicell_smoke_test.sh /Users/4470246/Downloads/PhysiCell-1.14.2 60 1`
- Added a smoke-test result note:
  - `docs/derived/physicell_smoke_test_check.md`
- Switched the CLONEID extraction plan from selected-dataset bundling to selected-TrajectoryBundle bundling.
- Added deterministic TrajectoryBundle discovery scaffolding:
  - `src/cloneid_agent/trajectory_bundles.py`
  - `python -m cloneid_agent discover-trajectory-bundle ...`
- Added mock TrajectoryBundle discovery tests and updated the toy workflow to emit `trajectory_bundle.json`.
- Updated workflow and ontology notes so CandidateSegment ranking remains a first-stage screen and TrajectoryBundle discovery/ranking is the preferred modeling-unit path.
- Added a deterministic TrajectoryBundle ranking stage with:
  - `src/cloneid_agent/trajectory_bundle_ranking.py`
  - `python -m cloneid_agent rank-trajectory-bundles ...`
- Added mock ranking tests for connected-history scoring and ranking artifact output.

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
- The next PhysiCell branch is also validated:
  - the build was promoted to a persistent local install at `/Users/4470246/Downloads/PhysiCell-1.14.2`
  - a minimal command-line smoke test completed successfully
  - expected output artifacts were generated under:
    - `/Users/4470246/Downloads/PhysiCell-1.14.2/output_smoke_20260427T014616Z`
- A deterministic offline TrajectoryBundle scaffold now exists for connected-history discovery from a seed CandidateSegment:
  - upstream/downstream expansion through `Passaging.passaged_from_id1/2`
  - context-transition recording across local segment boundaries
  - direct `Perspective.origin` attachment
  - `Identity` attachment only as inferred secondary support
- The toy round-trip and CLI scaffold can now emit:
  - `trajectory_bundle.json`
  - `trajectory_bundle.md`
- A deterministic second-stage ranking scaffold now exists for discovered TrajectoryBundles:
  - auditable component scores
  - explicit tractability penalties
  - `ranked_trajectory_bundles.json`
  - `ranked_trajectory_bundles.md`

---

## What is blocked

- Docker-based execution remains blocked until the Docker daemon is reachable from the current context.
- Apptainer/Singularity execution remains blocked until one of those runtimes is installed.
- Repository-coupled PhysiCell smoke testing has not been implemented yet; the successful smoke run used the upstream `heterogeneity` sample project.
- Live TrajectoryBundle discovery and bundling over the selected CLONEID seed candidate have not been executed yet in this branch.

---

## Questions needing user input

See `QUESTION_QUEUE.md`.

---

## Recommended next action when user returns

Proceed with the CLONEID extraction branch by using the existing ranked CandidateSegments as seeds for live TrajectoryBundle discovery, then bundle one reviewed TrajectoryBundle for observable extraction.

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
- `docs/derived/physicell_smoke_test_check.md`
- `scripts/check_physicell_runtime.sh`
- `scripts/build_physicell_local.sh`
- `scripts/install_physicell_persistent.sh`
- `scripts/run_physicell_smoke_test.sh`
- `docker/physicell-v1.14.2/Dockerfile`
- `containers/apptainer/physicell-v1.14.2.def`
- `src/cloneid_agent/dataset_selection.py`
- `src/cloneid_agent/trajectory_bundles.py`
- `src/cloneid_agent/trajectory_bundle_ranking.py`
- `tests/test_inventory_cli.py`
- `tests/test_schemas.py`
- `tests/test_run_io.py`
- `tests/test_toy_workflow.py`
- `tests/test_trajectory_bundles.py`
- `tests/test_trajectory_bundle_ranking.py`
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
   - Completed the persistent-install plus minimal PhysiCell smoke-test branch by promoting the successful build to `/Users/4470246/Downloads/PhysiCell-1.14.2`, running a 60-minute/1-thread smoke test, confirming output artifacts, and documenting the result.
   - Corrected the CLONEID extraction plan so ranked CandidateSegments remain stage 1 only, and added deterministic TrajectoryBundle discovery scaffolding plus mock tests.
   - Added deterministic TrajectoryBundle ranking so connected histories can be compared before any live selected-bundle extraction branch starts.
2. What safe next task did I identify?
   - Use top-ranked CandidateSegments as seeds for live TrajectoryBundle discovery, rank the discovered TrajectoryBundles, then prepare selected-TrajectoryBundle bundling for observable extraction.
3. Is that next task read-only, reversible, deterministic, and not dependent on user judgment?
   - Yes for live TrajectoryBundle discovery and bundling, provided read-only DB access remains available. Observable-selection policy is already resolved as `Perspective`-first with `Identity` secondary.
4. If yes, why am I not doing it now?
   - I am stopping at the end of the requested pre-bundling planning/scaffolding branch so you can confirm before I start live selected-TrajectoryBundle extraction.
5. Am I blocked by:
   - missing credentials? no
   - missing permissions? not for the completed branch; future Docker or live DB work may still require them
   - risk of modifying the real database? no
   - scientific judgment requiring user input? no
   - Level 2 or Level 3 ambiguity? no
6. If I am not blocked, continue working instead of stopping.
   - I am stopping here only because the user requested confirmation at this checkpoint.

## Git state

- Current branch: `main`
- Last committed work unit hashes:
  - `faf35bc` `feat(trajectory): add bundle ranking stage`
  - `7d25bbb` `feat(trajectory): add bundle discovery scaffold`
  - `b1c5721` `feat(runtime): add persistent install and smoke test wrappers`
- Tests run this session:
  - `bash -n scripts/check_physicell_runtime.sh`
  - `scripts/check_physicell_runtime.sh`
  - `bash -n scripts/build_physicell_local.sh`
  - `scripts/build_physicell_local.sh /tmp/PhysiCell-1.14.2-src`
  - `make` in `/tmp/PhysiCell-1.14.2-src` (expected OpenMP/compiler failure on default path)
  - `env PHYSICELL_CPP=/opt/homebrew/bin/g++-15 make` in `/tmp/PhysiCell-1.14.2-src`
  - `bash -n scripts/install_physicell_persistent.sh`
  - `bash -n scripts/run_physicell_smoke_test.sh`
  - `scripts/install_physicell_persistent.sh /tmp/PhysiCell-1.14.2-src /Users/4470246/Downloads/PhysiCell-1.14.2`
  - `scripts/run_physicell_smoke_test.sh /Users/4470246/Downloads/PhysiCell-1.14.2 60 1`
  - `PYTHONPATH=src python3 -m unittest tests/test_trajectory_bundles.py tests/test_toy_workflow.py`
  - `PYTHONPATH=src python3 -m unittest tests/test_trajectory_bundles.py tests/test_trajectory_bundle_ranking.py tests/test_toy_workflow.py`
- Work committed yet for the latest unit: yes
- Uncommitted / user-side files currently present:
  - modified: `CODEX_INSTRUCTIONS.md`
  - modified: `ONBOARDING_AND_SCOPE.md`
  - modified: `README.md`
  - modified: `RUNTIME_AND_HPC.md`
  - modified: `SUPERVISED_AUTONOMY.md`
  - untracked: `GIT_WORKFLOW.md`
  - untracked: `ONTOLOGY_FOR_DATASET_RANKING.md`
  - untracked: `docs/CLONEID_paper.pdf`
