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

---

## What works now

- The project scope, constraints, and unattended-work protocol have been translated into current coordination files.
- Milestone 0 documentation now exists for safe offline progress without touching the real CLONEID database or PhysiCell runtime.
- The repository scaffold has been classified into existing files, placeholders, operationally empty folders, and minimal missing implementation files.

---

## What is blocked

- Real CLONEID database inventory is blocked by missing approved connection details or a sanctioned snapshot.
- PhysiCell smoke testing is blocked by the absence of a binary or build/install instructions in the repository.
- Any real-data scientific branch remains blocked until database inventory exists.

---

## Questions needing user input

See `QUESTION_QUEUE.md`.

---

## Recommended next action when user returns

Answer the database-access and PhysiCell-runtime questions in `QUESTION_QUEUE.md`, then review the Milestone 0 plan and approve the first offline implementation slice: deterministic dry-run scaffolding plus a toy round-trip fixture.

---

## Files most worth reviewing

- `docs/derived/repository_map.md`
- `docs/derived/milestone0_plan.md`
- `QUESTION_QUEUE.md`
- `WORK_QUEUE.md`
- `STATUS.md`
