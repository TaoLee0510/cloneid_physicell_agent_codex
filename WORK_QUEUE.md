# Work Queue

This file is maintained by the agent. It should make unattended progress visible and reviewable.

## Work-loop protocol

For each work block:

1. Re-read coordination files.
2. Pick the highest-priority unblocked task.
3. Execute the task.
4. Run tests or validation if available.
5. Update `STATUS.md`.
6. Update `QUESTION_QUEUE.md`.
7. Re-read `WORK_QUEUE.md`.
8. Continue to the next unblocked safe task unless the stop checklist says to stop.


---

## Ready now

1. Regenerate and verify live selected `LineagePath` / `RootedTrajectoryBundle` artifacts under the corrected `passaged_from_id1` primary-backbone traversal policy.
2. Refresh downstream live artifacts derived from the selected lineage object:
   - observable selection
   - CLONEID-to-PhysiCell mapping
3. After live lineage-object artifacts are refreshed, continue with candidate PhysiCell model-folder generation.

---

## In progress

_None yet._

---

## Waiting for user

1. Confirm the completed persistent-install plus minimal PhysiCell smoke-test branch before I proceed to a repository-coupled PhysiCell smoke test or back to the CLONEID extraction branch.

---

## Done

1. Read the required onboarding, workflow, database, runtime, and schema guidance files.
2. Inspected the repository scaffold, placeholders, and operationally empty folders.
3. Created `docs/derived/repository_map.md`.
4. Created `docs/derived/milestone0_plan.md`.
5. Recorded blocked high-risk branches in `QUESTION_QUEUE.md`.
6. Completed Milestone 0 repository orientation and safe first-work planning.
7. Incorporated the user's answer that CLONEID database access should go through the installed `cloneid` R package.
8. Incorporated the user's answer that first real-data selection should remain score-driven until reviewed.
9. Inspected the installed `cloneid` R package interface and documented a safe read-only inventory approach in `docs/derived/cloneid_package_interface.md`.
10. Added package metadata and a deterministic Python CLI skeleton.
11. Implemented the read-only CLONEID inventory wrapper through `cloneid::connect2DB()` plus explicit `DBI` queries.
12. Added mock/auto/live inventory modes with graceful fallback on live-access failure.
13. Added tests for inventory JSON structure, graceful failure, and mock inventory behavior.
14. Verified the wrapper in mock mode, fallback mode, and live mode.
15. Drafted `docs/derived/cloneid_schema_map.md` from documented notes plus the observed live table/field surface.
16. Added strict schema objects for database inventory artifacts in `src/cloneid_agent/schemas.py`.
17. Added schema validation tests in `tests/test_schemas.py`.
18. Added generic run-folder creation and artifact-writer utilities in `src/cloneid_agent/run_io.py`.
19. Added run-I/O tests in `tests/test_run_io.py`.
20. Added a synthetic CLONEID-like toy fixture and toy round-trip workflow in `src/cloneid_agent/toy_workflow.py`.
21. Added a `toy-roundtrip` CLI entry point and test coverage for emitted artifacts.
22. Implemented the documented 0-to-5 dataset-scoring rule in `src/cloneid_agent/dataset_scoring.py`.
23. Added dataset-scoring tests in `tests/test_dataset_scoring.py`.
24. Implemented higher-level live/mock/auto candidate-dataset inventory in `scripts/cloneid_candidate_inventory.R` and Python CLI wrappers.
25. Added ontology-aware candidate ranking and deterministic top-candidate selection.
26. Added tests for candidate inventory, ranking, and selection behavior.
27. Verified candidate inventory, ranking, and selection in live and offline paths.
28. Replaced the coarse candidate ranker with a fine-grained `0-100` ranking model that favors repeated phenotype trajectories over raw molecular row volume.
29. Added the `fine-rank-candidates` CLI alias and updated `rank-candidates` to use the fine-grained model by default.
30. Re-ranked the saved live candidate inventory and refreshed the selected-candidate artifact under `runs/live_candidate_ranking_20260426T022200/`.
31. Added a concrete PhysiCell runtime plan for the pinned `v1.14.2` backend.
32. Added a local runtime environment check script plus project-owned Docker and Apptainer build definitions for the same pinned backend.
33. Verified the runtime-check script locally; Homebrew `g++-15` is present, Docker CLI is present but the daemon is not reachable from the current context, and Apptainer/Singularity are not installed.
34. Downloaded the official PhysiCell `v1.14.2` release tarball into `/tmp` and unpacked it as `/tmp/PhysiCell-1.14.2-src`.
35. Verified that the default `make` path fails on macOS `clang++` with the expected OpenMP error.
36. Successfully built PhysiCell `v1.14.2` locally with `PHYSICELL_CPP=/opt/homebrew/bin/g++-15`, producing the `heterogeneity` executable.
37. Added a reusable local build wrapper in `scripts/build_physicell_local.sh` and documented the successful build check in `docs/derived/physicell_local_build_check.md`.
38. Promoted the successful PhysiCell build to the persistent location `/Users/4470246/Downloads/PhysiCell-1.14.2`.
39. Ran the first minimal PhysiCell smoke test from the persistent install with a temporary short-run config and 1 OpenMP thread.
40. Confirmed smoke-test output artifacts and documented the result in `docs/derived/physicell_smoke_test_check.md`.
41. Added deterministic TrajectoryBundle discovery scaffolding, mock tests, and a CLI entry point seeded from ranked CandidateSegments.
42. Updated the workflow plan so CandidateSegment ranking remains stage 1 and selected-TrajectoryBundle bundling becomes the modeling-unit branch.
43. Added a deterministic TrajectoryBundle ranking stage with auditable component scores and CLI/test coverage.
44. Added a live TrajectoryBundle discovery pipeline seeded from current ranked CandidateSegments through the approved `cloneid` R interface.
45. Fixed a live candidate-inventory bug that had been corrupting `NULL` context fields to `0` during merge-time NA filling.
46. Verified a live top-seed TrajectoryBundle export, ranking, selection, and first-pass observable selection under `runs/live_trajectory_bundles_20260427T000100/`.
47. Added first-pass CLONEID-to-PhysiCell mapping artifacts from the selected live TrajectoryBundle and selected observables.
48. Corrected TrajectoryBundle connectivity representation to use explicit lineage edges and segment-to-segment transitions rather than timestamp adjacency.
49. Reworked TrajectoryBundle discovery to follow cloneidR-style lineage semantics:
   - `passaged_from_id1` is now the primary traversal backbone
   - `passaged_from_id2` is recorded as secondary support, not traversed by default
   - bundle artifacts now include explicit rooted-subtree and lineage-path fields
   - CandidateSegments are attached as annotations on the lineage graph, not used as graph connectivity
50. Updated selection and mapping layers to preserve the new lineage-object fields.
51. Added and passed deterministic tests for primary-lineage traversal, secondary-edge recording, rooted subtree fields, endpoint path recovery, and selected-bundle field preservation.

---

## Abandoned / superseded

_None yet._

---

## Migration note

Superseded terminology: `selected dataset` / `candidate dataset bundle`.

Current terminology: `CandidateSegment` for local context buckets; `LineagePath` or `RootedTrajectoryBundle` for connected modeling units.
