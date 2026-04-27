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

1. Implement selected-dataset record bundling and observable extraction for the top fine-ranked candidate using `Perspective`-first endpoint constraints and `Identity` as secondary interpretive support.

---

## In progress

_None yet._

---

## Waiting for user

1. Decision on how PhysiCell should be installed and run in this environment.

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

---

## Abandoned / superseded

_None yet._
