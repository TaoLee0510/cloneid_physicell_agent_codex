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

1. Implement higher-level candidate-dataset inventory and scoring on top of the table-level wrapper.
2. Extend the toy workflow with more explicit report/figure stub generation if needed.
3. Add unit tests for dataset scoring and candidate-dataset inventory behavior.

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

---

## Abandoned / superseded

_None yet._
