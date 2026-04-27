# Intermittent-supervision operating protocol

Before doing any implementation, read `SUPERVISED_AUTONOMY.md` and `ONBOARDING_AND_SCOPE.md`. The user will only review progress intermittently, usually around noon and in the evening.

You must:

1. Keep working on safe independent tasks when blocked.
2. Stop only the dependent branch when a high-risk answer is missing.
3. Maintain `QUESTION_QUEUE.md`, `WORK_QUEUE.md`, and `STATUS.md`.
4. Classify uncertainties as Level 0, 1, 2, or 3 according to `SUPERVISED_AUTONOMY.md`.
5. Never go deep into a speculative path for more than 30–45 minutes without producing an artifact, documenting the uncertainty, and moving to another task.
6. At every checkpoint, leave a concise status report that allows the user to resume supervision quickly.

Default behavior: act like a careful, deadline-driven scientist. Preserve provenance, avoid irreversible assumptions, and accumulate precise questions with recommended answers.

---

## Instruction refresh rule

At the start of every work session, and before stopping, re-read the active coordination files:

- `SUPERVISED_AUTONOMY.md`
- `WORK_QUEUE.md`
- `STATUS.md`
- `QUESTION_QUEUE.md`

Also re-read the domain-specific file most relevant to the current task.

Do not assume that earlier instructions are still fully loaded in context.

## No premature stop rule

Do not stop after identifying a safe next step. If a next task is safe, reversible, deterministic, and does not require user judgment, execute it before stopping.

Before stopping, update `STATUS.md` with the stop checklist from `SUPERVISED_AUTONOMY.md`.

---

When you identify a safe next implementation step, do it. Do not stop at “next safe step identified.” Stop only when the next available branch is blocked by Level 2 or Level 3 uncertainty, unsafe database mutation, unavailable permissions, or scientific judgment requiring user input.

---
## Git discipline

Read `GIT_WORKFLOW.md` before editing files.

Use Git conservatively:

- check status before starting,
- do not overwrite user changes,
- commit after coherent tested work units,
- do not commit broken work unless explicitly instructed,
- create branches only for risky/exploratory work,
- never push or rewrite history unless explicitly instructed.

Before stopping, update `STATUS.md` with the current branch, uncommitted files, last commit hash, tests run, and whether the work was committed.


---

# Codex implementation instructions

## Objective

Build a constrained, auditable CLONEID–PhysiCell agent workflow. The agent should not be implemented as an open-ended chatbot. It should be implemented as a deterministic pipeline with optional LLM-assisted planning and strict JSON outputs.

The system should use the **full CLONEID database** as its primary source of truth. It should not assume that the user has manually prepared individual exports for each dataset. Exports or snapshots are allowed only as optional caches, fixtures, or reproducibility artifacts.

The system should:

1. Connect to the CLONEID database in read-only mode.
2. Inventory `CandidateSegment` objects across the full database.
3. Score `CandidateSegment` objects as first-stage local signals.
4. Construct the explicit lineage graph and discover lineage objects:
   - `LineagePath`
   - `RootedTrajectoryBundle`
5. Rank lineage objects for mechanistic modelability.
6. Select one lineage object unless a user override is provided.
7. Select observables and constraints.
8. Select predefined PhysiCell model families.
9. Generate PhysiCell candidate model folders.
10. Run PhysiCell or validate in dry-run mode.
11. Evaluate candidate models against observed data.
12. Produce a reproducible report and figures.

Use official PhysiCell core `v1.14.2` as the pinned simulation backend. Automated workflow execution should use command-line PhysiCell runs generated from repository-managed templates. PhysiCell Studio may be used for human inspection or manual XML editing, but it must not be a required runtime dependency. If containers are used, build project-owned Docker and optional Apptainer/Singularity environments from the same pinned `v1.14.2` release.

## Non-negotiable constraints

The agent must not:

- write to, update, delete, or mutate the CLONEID database,
- modify source records,
- invent unavailable data,
- silently impute critical fields,
- invent arbitrary mechanisms outside the approved model library,
- treat inferred `Identity` records as directly observed phenotype,
- claim that a simulation match proves a biological mechanism,
- overwrite previous runs.

The agent must:

- use a read-only database account or enforce read-only transactions,
- record SQL queries or query templates used for provenance,
- record database host/database name/schema version when available,
- record missing data,
- record excluded datasets and observables,
- distinguish calibration data from validation data,
- distinguish observed data from inferred data,
- preserve provenance from source CLONEID records to model files and final report,
- write all planning decisions to `agent_plan.json`.

## Preferred implementation style

Use Python for the first implementation.

Recommended modules:

```text
src/cloneid_agent/
├── __init__.py
├── cli.py
├── db.py
├── inventory.py
├── dataset_scoring.py
├── observable_selection.py
├── hypothesis_library.py
├── physicell_mapping.py
├── simulation_runner.py
├── evaluation.py
├── report.py
└── schemas.py
```

The first version should use deterministic rule-based planning. Add LLM-assisted planning only after the deterministic workflow passes tests.

## Database-first implementation

Implement a database access layer before implementing model logic.

The access layer should:

- load `CLONEID_DB_READONLY_URL` from the environment or `.env`,
- connect using a MySQL-compatible client such as SQLAlchemy + PyMySQL,
- run only SELECT queries,
- expose typed query functions for events, context, Perspectives, Identities, and image-derived phenotype data,
- return pandas DataFrames or typed Pydantic models,
- record query provenance in each run folder.

Do not hard-code credentials.

Do not require individual user-prepared exports.

## First milestone

Implement dry-run mode using a live or local CLONEID database connection. Dry-run mode should create the full run folder structure, generated plans, candidate model configuration stubs, evaluation placeholders, and a report without requiring a PhysiCell binary.

## Second milestone

Implement local-test mode. Local-test mode should run small PhysiCell simulations if a PhysiCell executable is provided. The run should be small enough for a workstation or laptop.

## Third milestone

Implement HPC job preparation. The workflow should prepare independent jobs over model families, parameter sets, and stochastic replicates. Use job arrays rather than assuming distributed-memory parallelization inside a single PhysiCell run.

## CLI requirements

Primary dry-run command:

```bash
python -m cloneid_agent run \
  --db-url "$CLONEID_DB_READONLY_URL" \
  --templates model_templates/physicell \
  --output runs/test_dry_run \
  --mode dry-run
```

Equivalent command using `.env`:

```bash
python -m cloneid_agent run \
  --templates model_templates/physicell \
  --output runs/test_dry_run \
  --mode dry-run
```

Optional user override:

```bash
python -m cloneid_agent run \
  --dataset-id HGC27_density_selection_candidate_001 \
  --templates model_templates/physicell \
  --output runs/HGC27_density_selection_candidate_001 \
  --mode dry-run
```

Optional snapshot command:

```bash
python -m cloneid_agent snapshot \
  --db-url "$CLONEID_DB_READONLY_URL" \
  --output data/database_snapshots/snapshot_YYYYMMDD
```

## Definition of done

A fresh user should be able to run one command and obtain:

1. database inventory,
2. selected lineage object,
3. structured agent plan,
4. generated candidate model folders,
5. simulation outputs or dry-run outputs,
6. quantitative model comparison,
7. reproducible report,
8. publication-style figure stubs or generated plots.
