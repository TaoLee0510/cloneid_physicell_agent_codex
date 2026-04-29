# CLONEID–PhysiCell Agent Proof-of-Principle

This repository is a Codex-ready scaffold for building a constrained, auditable agentic workflow that connects the **full CLONEID database** to PhysiCell mechanistic simulations.

The agent is **not** an unconstrained chatbot. It should behave as a bounded workflow that:

1. connects to the CLONEID database in read-only mode,
2. inventories candidate datasets from the full database,
3. selects a dataset suitable for mechanistic simulation,
4. selects usable observables and constraints,
5. chooses a small set of predefined PhysiCell model templates,
6. instantiates and runs candidate models,
7. compares simulated outputs to observed CLONEID data,
8. produces an auditable model-selection report.

The database is the source of truth. Exports, CSVs, JSON files, and snapshots may be used only as optional caches, fixtures, or debugging artifacts.

The simulation backend should be pinned to official PhysiCell core `v1.14.2`:

- release source: <https://github.com/MathCancer/PhysiCell/releases/tag/1.14.2>
- use command-line PhysiCell runs generated from templates for automated workflow execution
- do not depend on PhysiCell Studio for automation
- if containers are used, build a project-owned Docker image from the official `v1.14.2` release and reuse that pinned environment for optional Apptainer/Singularity HPC execution

## Read first

Codex should start with these files, in order:

1. [`CODEX_INSTRUCTIONS.md`](CODEX_INSTRUCTIONS.md) — implementation brief and rules for Codex.
2. [`DATABASE_ACCESS.md`](DATABASE_ACCESS.md) — how the workflow should connect to and query the CLONEID database.
3. [`AGENT_WORKFLOW.md`](AGENT_WORKFLOW.md) — scientific and technical workflow specification.
4. [`RUNTIME_AND_HPC.md`](RUNTIME_AND_HPC.md) — local, workstation, and HPC execution strategy.
5. [`docs/CLONEID_SCHEMA_NOTES.md`](docs/CLONEID_SCHEMA_NOTES.md) — schema concepts relevant to the CLONEID-to-PhysiCell handshake.

## Intended first implementation

The first version should support a minimal proof of principle using a live or local read-only CLONEID database connection:

```bash
python -m cloneid_agent run \
  --db-url "$CLONEID_DB_READONLY_URL" \
  --templates model_templates/physicell \
  --output runs/test_dry_run \
  --mode dry-run
```

The command should also support loading the database URL from `.env`:

```bash
python -m cloneid_agent run \
  --templates model_templates/physicell \
  --output runs/test_dry_run \
  --mode dry-run
```

The first successful run should generate:

```text
runs/<run_id>/agent_plan.json
runs/<run_id>/database_inventory.json
runs/<run_id>/dataset_inventory.json
runs/<run_id>/selected_dataset.json
runs/<run_id>/observables.json
runs/<run_id>/model_candidates/
runs/<run_id>/evaluation/model_comparison.csv
runs/<run_id>/model_selection_report.md
runs/<run_id>/figures/
```

## Optional database snapshots

The workflow may support snapshots for testing and reproducibility:

```bash
python -m cloneid_agent snapshot \
  --db-url "$CLONEID_DB_READONLY_URL" \
  --output data/database_snapshots/snapshot_YYYYMMDD
```

Snapshots are not the primary interface. They are optional, versioned representations of the database state used for tests, reproducibility, or offline development.

## Scientific endpoint

The desired manuscript-facing figure should show:

```text
CLONEID database
→ agent inventories modelable datasets
→ agent selects one dataset and observables
→ agent maps CLONEID records to PhysiCell inputs
→ candidate PhysiCell models are instantiated and run
→ simulated outputs are compared to observed CLONEID data
→ one model family is supported while alternatives are rejected under tested assumptions
```

Use restrained interpretation language: “supports,” “is sufficient to recapitulate,” “is inconsistent with,” and “rejected under tested assumptions.” Avoid “proves” or “discovers the true mechanism.”

## Supervised autonomy

This project is intended to be worked on by an AI coding agent with intermittent human supervision. Before starting implementation, read:

- `SUPERVISED_AUTONOMY.md` — how to keep working while the user is unavailable, when to stop and ask, and how to maintain question/status queues.
- `ONBOARDING_AND_SCOPE.md` — how to get familiar with CLONEID and PhysiCell before attempting the full integration.
- `QUESTION_QUEUE.md`, `WORK_QUEUE.md`, and `STATUS.md` — live coordination files that should be updated during work.

The agent should accumulate precise questions for the user's noon and evening review windows while continuing safe independent work.
