# Milestone 0 Plan

## Scope

Milestone 0 is documentation, scaffold verification, and safe offline planning. It does not include real database access, PhysiCell execution, or scientific dataset selection.

## Scientific goal in working terms

Build a narrow, auditable bridge from structured CLONEID records to constrained PhysiCell model comparisons. The first claim is feasibility of the round trip, not biological discovery.

## Intended CLONEID-to-PhysiCell handshake

```text
CLONEID database
-> candidate dataset inventory
-> one selected longitudinal dataset
-> selected observables and constraints
-> mapping into a predefined PhysiCell model family
-> dry-run or simulation outputs
-> quantitative comparison to observed CLONEID records
-> auditable model-selection report
```

## Guardrails

Allowed:

- Read-only inspection
- Deterministic planning
- Reversible scaffolding
- Toy/synthetic fixtures
- Provenance-first design
- Placeholder dry-run artifacts

Not allowed:

- Mutating the CLONEID database
- Inventing unavailable records
- Treating inferred `Identity` as directly observed phenotype
- Inventing new biological mechanisms outside the approved model library
- Choosing the scientific claim or main manuscript dataset by guesswork
- Overwriting prior run outputs silently

## Blocked-branch behavior while the user is away

When a branch is blocked, stop only that branch, record the question and risk level, and continue independent work. Use:

- Level 0: proceed
- Level 1: reversible documented assumption
- Level 2: stop that branch and continue elsewhere
- Level 3: stop that branch, queue a question, and avoid speculative implementation

## Smallest toy round trip

The safest toy round trip before touching real CLONEID data is:

1. Create a synthetic CLONEID-like dataset with:
   - one cell line label,
   - one seeding event,
   - two or three time-stamped harvest observations,
   - one endpoint state distribution,
   - simple flask/media metadata.
2. Run deterministic candidate-dataset scoring on the synthetic records.
3. Select one robust observable:
   - corrected cell count or simple cell count trajectory.
4. Map the toy dataset into one or two stub model families:
   - `neutral_growth`
   - `fixed_state_fitness`
5. Generate dry-run candidate model folders and a strict `agent_plan.json`.
6. Produce placeholder evaluation outputs from deterministic synthetic predictions.
7. Emit a report comparing the toy observed trajectory to toy model outputs.

This validates interface contracts, provenance, folder layout, and report generation without requiring real database access or a PhysiCell executable.

## First deterministic utility modules to build before any LLM layer

Build these first, in order:

1. `schemas.py`
   - strict JSON/Pydantic schemas for run config, dataset inventory, selected dataset, observables, model candidates, and provenance
2. `cli.py` and `__main__.py`
   - deterministic command entrypoint and argument validation
3. `db.py`
   - read-only URL loading, query validation, and provenance capture interfaces
4. `inventory.py`
   - candidate dataset inventory and summary output
5. `dataset_scoring.py`
   - explicit 0-to-5 modelability scoring
6. `observable_selection.py`
   - deterministic observable ranking and exclusions
7. `physicell_mapping.py`
   - CLONEID-to-template parameter mapping and candidate folder generation
8. `evaluation.py`
   - deterministic comparison metrics and placeholder evaluators
9. `report.py`
   - auditable markdown and JSON outputs
10. `simulation_runner.py`
   - dry-run folder generation first, real execution later

The LLM/agent layer should orchestrate these modules only after they work deterministically.

## First implementation slice recommended now

Safe offline implementation slice:

1. Add package metadata and CLI skeleton.
2. Add run-folder creation utilities and schema objects.
3. Add a toy fixture loader.
4. Add deterministic dry-run plan generation.
5. Add tests covering schema validation, scoring, and report-file emission.

This is Level 0 or Level 1 work and does not force any scientific choice.

## Missing prerequisites for later milestones

Before Milestone 1 real database inventory:

- actual read-only connection details or a sanctioned local snapshot
- confirmation of the target schema instance if multiple CLONEID deployments exist

Before Milestone 2 PhysiCell smoke test:

- a PhysiCell binary path or explicit build/install instructions
- at least one minimal runnable PhysiCell config or approved stub format

## Recommended next milestones after Milestone 0

1. Implement deterministic dry-run scaffolding using toy data.
2. Implement read-only database adapter and provenance capture once credentials are available.
3. Perform a PhysiCell smoke test once runtime assets are available.
4. Only then attempt the first real CLONEID round trip.
