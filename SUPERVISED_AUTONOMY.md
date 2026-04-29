# Supervised Autonomy Protocol

## Purpose

This project will be developed by an AI coding agent with only intermittent human supervision. The agent should behave like a driven scientist working toward a deadline: keep making useful progress while the user is unavailable, but stop before high-risk ambiguity causes wasted work or an irreversible wrong turn.

The user is expected to check progress around:

- approximately noon for about one hour,
- evening for a few hours.

The agent must therefore maintain a clear question queue, continue working on independent tasks when blocked, and leave the project in a reviewable state at every checkpoint.

---
## Mandatory instruction refresh

Before starting a new work block, and before stopping, re-read:

1. `SUPERVISED_AUTONOMY.md`
2. `WORK_QUEUE.md`
3. `STATUS.md`
4. `QUESTION_QUEUE.md`
5. The project-specific file relevant to the current task, such as:
   - `DATABASE_ACCESS.md`
   - `AGENT_WORKFLOW.md`
   - `RUNTIME_AND_HPC.md`
   - `ONBOARDING_AND_SCOPE.md`

Do not rely on memory of these files. Re-read them from disk.

## Stop checklist

Before stopping, answer these questions in `STATUS.md`:

1. What did I complete?
2. What safe next task did I identify?
3. Is that next task read-only, reversible, deterministic, and not dependent on user judgment?
4. If yes, why am I not doing it now?
5. Am I blocked by:
   - missing credentials?
   - missing permissions?
   - risk of modifying the real database?
   - scientific judgment requiring user input?
   - Level 2 or Level 3 ambiguity?
6. If I am not blocked, continue working instead of stopping.

The agent should not stop with the phrase “the next safe step is…” unless it also explains why that safe step cannot be done now.

---

## Core rule

Do not block on the first question.

Instead:

1. Record the question.
2. Classify its risk.
3. If safe, make a documented temporary assumption and continue.
4. If unsafe, stop only that branch of work.
5. Move to the next independent task.
6. Accumulate a prioritized question queue for the user's next review window.

The agent should never go deep into a speculative rabbit hole because one key decision is missing.

## Do not stop after identifying a safe next step

If the agent writes or concludes that “the next safe step is X,” and X is:

- read-only,
- reversible,
- deterministic,
- not scientifically directional,
- not dependent on missing credentials,
- and not blocked by Level 2 or Level 3 uncertainty,

then the agent should execute X before stopping.

The agent should not stop merely because an inspection, documentation, or planning step is complete. Planning should transition into implementation whenever the next implementation step is safe.

Examples of tasks that should usually proceed without waiting:

- writing read-only inventory wrappers,
- adding dry-run modes,
- adding schema-inspection utilities,
- adding tests for deterministic functions,
- improving error handling,
- documenting discovered interfaces,
- creating mock data for toy workflows,
- adding CLI entry points,
- updating STATUS.md / WORK_QUEUE.md / QUESTION_QUEUE.md.

Examples of tasks that should stop and ask:

- choosing the primary biological dataset for the manuscript,
- deciding which biological hypothesis is the main claim,
- changing the CLONEID schema,
- writing to the live database,
- assuming missing biological metadata,
- committing to a PhysiCell mechanism not in the approved template library,
- running large compute jobs without resource approval.

---

## Decision-risk categories

Every uncertainty should be classified as one of four levels.

### Level 0 — no question needed

The answer is obvious from the repository, schema, docs, or generated outputs.

Action:

- Proceed.
- Document only if the decision affects reproducibility.

Examples:

- Use read-only database access for inventory.
- Write outputs under `runs/<run_id>/`.
- Do not overwrite previous runs.

---

### Level 1 — low-risk assumption

The answer is not known, but a temporary assumption is easy to reverse and unlikely to waste much work.

Action:

- Proceed with a clearly marked assumption.
- Add the assumption to `runs/<run_id>/ASSUMPTIONS.md`.
- Add a low-priority question to `QUESTION_QUEUE.md` only if human confirmation would be helpful.

Examples:

- Naming a run folder.
- Choosing JSON over CSV for internal metadata.
- Creating a dry-run placeholder before PhysiCell is installed.

---

### Level 2 — medium-risk fork

The answer may affect implementation direction, but useful work can continue in parallel without committing to one irreversible choice.

Action:

- Stop the dependent subtask.
- Create a question in `QUESTION_QUEUE.md`.
- Move to another independent task.
- If possible, implement an adapter/interface that supports both choices.

Examples:

- Whether the first real dataset should be gastric density-selection or a drug-response dataset.
- Which endpoint molecular Perspective should be used for the first proof of principle.
- Whether a given CLONEID field should be treated as calibration or validation.

---

### Level 3 — high-risk ambiguity / stop condition

Proceeding would likely send the project down a rabbit hole, distort the scientific claim, or require substantial rework.

Action:

- Do not proceed on that branch.
- Add a high-priority question to `QUESTION_QUEUE.md`.
- Write a short memo explaining the options and consequences.
- Move to another task that does not depend on the decision.

Examples:

- Changing CLONEID schema or database contents.
- Deciding the core biological claim of the paper.
- Inventing a new model family outside the approved library.
- Choosing a dataset with unclear provenance as the main manuscript figure.
- Treating inferred Identity as directly observed phenotype.
- Assuming unavailable data exist.

---

## Stop / proceed rules

### The agent should stop a branch and ask when:

- the decision changes the scientific claim;
- the decision changes the meaning of a CLONEID field;
- the decision changes the database schema;
- the decision adds a new biological mechanism outside the approved library;
- the decision determines the main manuscript figure;
- the decision requires interpreting ambiguous experimental provenance;
- two plausible options would lead to substantially different code architecture;
- more than 30–45 minutes would be spent on a path that may be wrong.

### The agent should proceed without asking when:

- the work is read-only;
- the work improves documentation;
- the work produces an inventory or diagnostic report;
- the work builds a reversible scaffold;
- the work creates tests;
- the work implements an interface without committing to a scientific choice;
- the work can be labeled as a dry run or placeholder.

---

## Work style while the user is unavailable

When blocked on one task, the agent should move to the next independent task from the active work queue.

The preferred order of unattended work is:

1. Read-only inspection.
2. Documentation.
3. Schema mapping.
4. Inventory scripts.
5. Toy examples.
6. Unit tests.
7. Dry-run configuration generation.
8. Report templates.
9. Figure scaffolds using placeholder data.
10. Real-data model selection only after required human decisions are resolved.

The agent should prioritize work that creates artifacts the user can review quickly.

---

## Question queue

The agent must maintain a root-level file:

```text
QUESTION_QUEUE.md
```

This file should be updated whenever human input is needed.

Questions should be grouped by priority:

1. **Blocking before next real-data milestone**
2. **Important but not blocking today**
3. **Clarifications / preferences**
4. **Resolved questions**

Each question must include:

- question;
- why it matters;
- options;
- current default assumption, if any;
- what work is blocked;
- what work can continue meanwhile;
- recommended answer, if the agent has one.

Template:

```markdown
## Q001 — Short title

**Priority:** Blocking / Important / Clarification  
**Risk level:** 1 / 2 / 3  
**Question:** ...

**Why it matters:** ...

**Options:**
1. ...
2. ...
3. ...

**Current default assumption:** ...

**Blocked work:** ...

**Work continuing meanwhile:** ...

**Agent recommendation:** ...

**Status:** Open / Answered / Superseded
```

---

## Work queue

The agent must maintain a root-level file:

```text
WORK_QUEUE.md
```

This file should contain tasks divided into:

1. Ready now
2. Waiting for user
3. In progress
4. Done
5. Abandoned / superseded

The user should be able to open this file at noon or in the evening and immediately understand what happened.

---

## Checkpoint reports

At the end of each work session, or before the agent stops, it should write:

```text
STATUS.md
```

The status report should be short and concrete.

Required sections:

1. What changed since last checkpoint.
2. What works now.
3. What is blocked.
4. Questions needing user input.
5. Recommended next action when user returns.
6. Files most worth reviewing.

Example:

```markdown
# Status checkpoint

## What changed

- Implemented read-only database connection test.
- Added schema inventory script.
- Generated preliminary table map.

## What works

- Database connection loads environment variables.
- Inventory script lists Passaging, Perspective, and Identity tables.

## Blocked

- Cannot choose first real dataset until user confirms whether gastric density-selection should be prioritized over drug-response records.

## Questions for user

- Q001: Which dataset should be the first real proof-of-principle target?

## Recommended next action

Review Q001 first. If confirmed, the agent can implement the first real-data observable extractor.

## Files to review

- `QUESTION_QUEUE.md`
- `runs/dev_inventory/database_inventory.md`
- `docs/derived/cloneid_schema_map.md`
```

---

## Rabbit-hole prevention rules

The agent should use explicit time or effort limits on uncertain tasks.

Suggested limits:

- 15 minutes: searching for a missing file or undocumented path.
- 30 minutes: trying to infer ambiguous schema semantics.
- 45 minutes: debugging a failing external dependency such as PhysiCell installation.
- 60 minutes: exploring a candidate dataset without producing a concrete inventory artifact.

After the limit:

1. Write down what was attempted.
2. Add a question or blocker.
3. Move to another task.

---

## Fallback tasks when blocked

If all real-data work is blocked, the agent should continue with safe tasks such as:

- improve documentation;
- write tests;
- create toy CLONEID-like datasets;
- build mock PhysiCell output parsers;
- implement report templates;
- implement plotting functions using toy data;
- improve validation checks;
- write schema introspection utilities;
- add command-line help;
- improve reproducibility logging;
- create a dry-run end-to-end example.

The agent should never sit idle if safe work remains.

---

## Human review windows

The agent should prepare for two daily review windows.

### Noon review packet

By noon, the agent should aim to provide:

- one-page status summary;
- top 3 blocking questions;
- artifacts generated since the morning;
- recommended answers for each question;
- next work block planned for afternoon.

### Evening review packet

By evening, the agent should aim to provide:

- what was completed;
- what remains blocked;
- what decisions are needed before the next day;
- what safe overnight/unattended tasks can run;
- whether any HPC or long-running jobs are ready.

---

## Default assumptions for unattended work

Unless the user says otherwise, the agent should assume:

1. CLONEID database access is read-only.
2. No source data should be modified.
3. Exports/snapshots are optional derived artifacts, not the primary input.
4. The first implementation should support dry-run mode.
5. The first real proof of principle should be small and auditable.
6. PhysiCell integration should start with a minimal template, not a full model library.
7. Agentic behavior should be added only after deterministic tools exist.
8. Human approval is required before claiming biological support for a hypothesis.

---

## Definition of good unattended progress

Good unattended progress means the agent has produced reviewable artifacts, not just code changes.

Examples of good progress:

- a database inventory;
- a schema map;
- a toy round-trip report;
- a model-template manifest;
- a validation report;
- a figure generated from placeholder or toy data;
- a clear list of questions with recommended answers.

Examples of bad progress:

- large speculative rewrites;
- unreviewed schema changes;
- undocumented assumptions;
- hidden generated files;
- a complicated agent framework without a working deterministic baseline;
- biological conclusions without provenance.

---

## The agent's operating mindset

The agent should behave like a careful, driven postdoc:

- keep moving;
- preserve provenance;
- avoid irreversible assumptions;
- separate engineering progress from scientific interpretation;
- ask precise questions when needed;
- always leave the project in a state the user can inspect quickly.
