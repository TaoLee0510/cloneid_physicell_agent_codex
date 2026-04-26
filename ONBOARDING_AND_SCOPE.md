# Onboarding and Scope

## Why this file exists

CLONEID and PhysiCell are both comprehensive frameworks. This project should not begin by attempting a full integration between all CLONEID concepts and all PhysiCell capabilities.

The first goal is to build a narrow, inspectable, auditable bridge between the two systems.

---

## Guiding principle

Start with the smallest useful handshake:

```text
CLONEID database
→ selected longitudinal dataset
→ selected observables
→ PhysiCell model template
→ simulation output
→ comparison to CLONEID observations
→ auditable report
```

Only expand after this round trip works.

---

## Initial familiarization tasks

Before implementing the full agent workflow, complete these tasks.

### 1. Understand CLONEID at the database level

Inspect the database schema and identify:

- event-history tables;
- phenotype tables;
- molecular Perspective tables;
- Identity tables;
- specimen/cell-line context tables;
- treatment or perturbation records, if present;
- links between records.

Create:

```text
docs/derived/cloneid_schema_map.md
```

### 2. Understand CLONEID data availability

Write a read-only database inventory script.

The script should report:

- available cell lines / samples;
- number of event records;
- number of longitudinal phenotype records;
- number of Perspective records;
- number of Identity records;
- datasets with repeated measurements;
- datasets with endpoint molecular readouts;
- missing fields that block simulation.

Output:

```text
runs/<run_id>/database_inventory.json
runs/<run_id>/database_inventory.md
```

### 3. Understand PhysiCell minimally

Before integrating with real CLONEID records, run one minimal PhysiCell example or template.

Confirm:

- where configuration files live;
- how cell definitions are specified;
- how simulation duration and output intervals are configured;
- how initial conditions are specified;
- where outputs are written;
- which output fields can be compared to CLONEID observables.

Create:

```text
docs/derived/physicell_minimal_run_notes.md
```

### 4. Build a toy bridge before using real data

Use a synthetic or toy dataset first.

The toy bridge should:

- create a fake CLONEID-like event history;
- instantiate one PhysiCell template;
- run or dry-run the simulation;
- read simulation output;
- compare it to the fake observed trajectory;
- generate a report.

### 5. Only then use a real CLONEID dataset

After the toy bridge works, select one real CLONEID dataset with:

- repeated phenotype measurements;
- clear event history;
- sufficient context for simulation initialization;
- at least one endpoint Perspective or Identity readout.

The first real-data goal is not comprehensive biological discovery. The first goal is to show that the CLONEID-to-PhysiCell round trip is possible.

---

## Explicit non-goals for the first milestone

Do not attempt these initially:

- full support for all CLONEID tables;
- full support for all PhysiCell model features;
- autonomous biological discovery;
- unrestricted LLM-generated mechanisms;
- multi-dataset benchmarking;
- large-scale HPC sweeps;
- clinical decision support;
- automated model publication without human review.

---

## Recommended milestone order

### Milestone 0 — documentation and schema map

Understand both systems enough to define a safe first bridge.

### Milestone 1 — database inventory

Read the CLONEID database in read-only mode and summarize available datasets.

### Milestone 2 — PhysiCell smoke test

Run one minimal PhysiCell model or validate one generated configuration.

### Milestone 3 — toy round trip

Use fake CLONEID-like data to produce a complete model-selection report.

### Milestone 4 — real-data round trip

Use one selected CLONEID dataset to instantiate and evaluate a small number of PhysiCell model templates.

### Milestone 5 — agentic model selection

Add the constrained agent layer only after deterministic code paths work.

---

## Agent should be added last

The first implementation should not depend on an LLM agent.

Instead, implement deterministic components first:

1. database inventory;
2. dataset scoring;
3. observable extraction;
4. template filling;
5. simulation execution;
6. evaluation;
7. report generation.

Once these components work, the agent can orchestrate them.

The agent should call existing deterministic tools. It should not replace them.

---

## Definition of a successful first milestone

A successful first milestone produces:

1. a CLONEID schema map;
2. a database inventory;
3. a PhysiCell minimal-run note;
4. a toy round-trip report;
5. a clear recommendation for the first real CLONEID dataset to simulate.

At this stage, no biological claim is required.

The purpose is to make the integration tractable.
