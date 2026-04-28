# CLONEID–PhysiCell Agent Workflow

## Purpose

This project implements a constrained, auditable agentic workflow that connects the **full CLONEID database** to PhysiCell mechanistic simulations.

The agent is **not** an unconstrained chatbot. It is a multi-step workflow that uses CLONEID as structured experimental memory, PhysiCell as the executable multicellular hypothesis engine, and a bounded planning layer to discover connected lineage objects, instantiate candidate models, run simulations, and compare those simulations to observed data.

The goal is to demonstrate the following proof of principle:

> Given a full CLONEID database and a library of PhysiCell model templates, an agent can identify a connected lineage object suitable for mechanistic simulation, select relevant observables and constraints, generate a small set of competing PhysiCell model candidates, run the simulations, compare outputs to observed CLONEID data, and produce an auditable model-selection report.

The desired final output is a figure and report showing that one PhysiCell model family recapitulates the selected CLONEID lineage object better than several biologically plausible alternatives.

For database access expectations, see [`DATABASE_ACCESS.md`](DATABASE_ACCESS.md).

For runtime and HPC expectations, see [`RUNTIME_AND_HPC.md`](RUNTIME_AND_HPC.md).

## Supervision model

This workflow is expected to be developed under intermittent human supervision. The agent should follow `SUPERVISED_AUTONOMY.md`: continue on safe independent tasks, stop only high-risk dependent branches, and accumulate questions in `QUESTION_QUEUE.md` for the user review windows.

Before attempting real-data model selection, the agent should complete the onboarding milestones in `ONBOARDING_AND_SCOPE.md`.

---

## High-level scientific motivation

CLONEID preserves the context needed to interpret genotype-to-phenotype relationships over time. In particular, CLONEID distinguishes:

- **Event**: time-stamped specimen history and experimental context.
- **Phenotype**: directly witnessed properties of the intact system, often measured repeatedly over time.
- **Perspective**: assay-specific molecular views, often partial and sometimes destructive.
- **Identity**: inferred clone-level representations reconciled across Perspectives.

PhysiCell provides an executable framework for multicellular mechanistic simulation.

The agent workflow tests whether CLONEID contains enough structured context to let an AI-guided workflow translate longitudinal records into executable mechanistic hypotheses.

---

## Core agent task

The agent should be given:

1. Read-only access to the full CLONEID database.
2. A library of PhysiCell model templates.
3. A set of allowed model families.
4. A set of allowed observables and evaluation metrics.

The agent must:

1. Inspect the full CLONEID database.
2. Inventory first-stage `CandidateSegment` objects.
3. Rank `CandidateSegment` objects as local context signals while performing explicit lineage-graph discovery over the full primary `Passaging.passaged_from_id1` graph.
4. Discover one or more connected lineage objects suitable for simulation:
   - `LineagePath`
   - `RootedTrajectoryBundle`
5. Identify usable observables and constraints.
6. Generate a small set of competing PhysiCell model candidates from predefined templates.
7. Instantiate those candidates using CLONEID-derived inputs.
8. Run or prepare simulations.
9. Compare simulation outputs to observed CLONEID data.
10. Produce an auditable model-selection report.

The agent should not invent arbitrary biological mechanisms. It should select among predefined, interpretable model families.

---

## Database-first workflow

The primary workflow is:

```text
CLONEID database
→ global lineage graph discovery
→ lineage-object inventory
→ CandidateSegment discovery / ranking
→ lineage-object ranking / review
→ bounded modeling-candidate lineage-object selection
→ smoke-eligible modeling-lineage-object selection
→ biological proof-of-principle candidate selection
→ selected lineage-object record bundle
→ observable selection
→ CLONEID-to-PhysiCell mapping
→ model candidate generation
→ simulation execution or dry run
→ evaluation
→ auditable report and figure
```

A run may create a local cache of the database records used in that run, but this cache is an output of the workflow, not a required input.

---

## Dataset-selection logic

The agent should rank candidate CLONEID records in two stages:

1. `CandidateSegment` ranking for local context-consistent groups.
2. lineage-object ranking plus bounded modeling-candidate selection for connected biological histories that may span multiple CandidateSegments.

The workflow must distinguish:

1. `raw_time_simulation_eligible`
2. `phase_abstracted_modeling_eligible`
3. `biologically_interpretable`

Long-term lineage paths should not be rejected as biologically unsuitable solely because raw elapsed clock time is large. The raw-time guardrail controls the technical smoke-test branch, not the separate biological proof-of-principle branch.

A modeling unit is modelable if it contains:

1. A clear event history.
2. Time-stamped repeated phenotypic observations.
3. At least one endpoint molecular Perspective or Identity readout.
4. Sufficient context to initialize a simulation.
5. At least two plausible competing model families.
6. At least one observable that can be compared between simulation and experiment.

### CandidateSegment definition

For the first implementation, define a `CandidateSegment` as a local context bucket: a group of records from the database that share enough local experimental context to be summarized together.

Useful grouping fields include local `Passaging` context only:

- `Passaging.cellLine`
- `Passaging.growthType`
- `Passaging.passage`
- `Passaging.media`
- `Passaging.flask`

The implementation should record exactly how CandidateSegments were defined in `dataset_inventory.json`.

`Perspective` and `Identity` should not be used to define CandidateSegments. They attach later to discovered lineage objects:

- `Perspective` attaches through `Perspective.origin`
- `Identity` attaches only as inferred secondary support

CandidateSegments are useful as first-stage ranking units, but they are not assumed to be the final biologically meaningful modeling unit. Changes in passage, transfer, media, flask, harvest, or bottleneck structure may split one connected biological history across multiple CandidateSegments. Context is layered onto the lineage graph; context buckets do not define graph connectivity.

### Lineage-Object Definition

Define a `LineagePath` as an ancestor-to-endpoint path recovered through:

- `Passaging.passaged_from_id1`

A `LineagePath` should:

- record context transitions across passage, media, flask, growth type, and related fields,
- attach `Perspective` records through `Perspective.origin`,
- attach `Identity` only as inferred secondary support.

Define a `RootedTrajectoryBundle` as the descendants of a root event recovered through:

- `Passaging.passaged_from_id1`

A `RootedTrajectoryBundle` should:

- preserve a rooted descendant subtree on the primary lineage backbone,
- identify all connected CandidateSegments in scope,
- record context transitions across passage, media, flask, growth type, and related fields,
- attach `Perspective` records through `Perspective.origin`,
- attach `Identity` only as inferred secondary support.

`Passaging.passaged_from_id2` should be recorded as secondary / exception / merge support and should not expand the primary traversal by default.

The implementation should preserve the distinction:

- `CandidateSegment` = first-stage local screen
- `LineagePath` / `RootedTrajectoryBundle` = connected modeling unit
- selected lineage object = the lineage object chosen for bundling, observable extraction, and CLONEID-to-PhysiCell mapping

### CandidateSegment score

Implement a first-stage CandidateSegment score from 0 to 5.

```text
+1 event history available
+1 repeated phenotype measurements available
+1 endpoint Perspective support available
+1 experimental context sufficient for initialization
+1 multiple plausible mechanisms distinguishable
```

The agent should not assume the top-ranked CandidateSegment is the final modeling unit. CandidateSegment scores are annotations and ranking features for globally discovered lineage objects; they do not seed or define primary lineage connectivity.

### Lineage-Object Ranking Plan

Lineage-object ranking should distinguish which connected histories are best suited for the first CLONEID-to-PhysiCell proof of principle.

Planned ranking features include:

- `connected_segment_count`
- `event_graph_depth`
- `transition_count`
- repeated phenotype observations across the graph
- terminal `Perspective` support
- calibration/validation split potential
- tractability penalty

For biological proof-of-principle selection, add a second interpretation layer:

- preserve event order and provenance,
- treat each primary lineage interval as a candidate model phase,
- record the mapping from real elapsed time to normalized simulated phase time,
- avoid simulating idle calendar time literally,
- preserve raw-time runtime guardrails only for the technical smoke-test branch.

The selected lineage object should be the highest-priority reviewed `LineagePath` or `RootedTrajectoryBundle` unless the user provides an override.

---

## Observable-selection logic

Possible observables include:

| CLONEID source | Candidate observable | PhysiCell comparison target |
|---|---|---|
| `Passaging.cellCount` | cell count over time | viable cell count |
| `Passaging.correctedCount` | corrected cell count over time | viable cell count |
| `Passaging.areaOccupied_um2` | occupied area / density | spatial confluence or area coverage |
| `Passaging.cellSize_um2` | mean cell size | simulated cell size proxy if available |
| `QuPathEvaluation.cellCount_*` | image-derived cell count over time | viable cell count or confluence |
| `Perspective.size` | clone or state abundance | endpoint state fraction |
| `Identity.size` | inferred clone abundance | endpoint state fraction |
| `Passaging.date` | time interval | simulation duration |
| `Passaging.flask` + `Flask.dishSurfaceArea_cm2` | culture geometry | simulation domain size |
| `Passaging.media` + `Media` fields | environmental context | substrate/resource/treatment assumptions |

Prioritize robust observables:

1. Cell count or corrected cell count.
2. Image-derived cell count, if available and QC-supported.
3. Area occupied or density.
4. Endpoint state / clone / karyotype composition.
5. Time between events.

---

## Allowed model families

The agent may choose from a small library of interpretable PhysiCell model templates.

### Model 1 — neutral growth

All simulated cells share the same proliferation and death rules. This is the null model.

### Model 2 — fixed state-specific fitness

Different cell states have different fixed proliferation or death parameters.

### Model 3 — density-dependent growth

Cell states differ in how proliferation changes with local density.

### Model 4 — resource-limited growth

Cell states differ in resource consumption, substrate sensitivity, or carrying-capacity behavior.

### Model 5 — event-history-aware model

Passaging, seeding density, harvest timing, and bottleneck events are explicitly represented.

---

## CLONEID-to-PhysiCell mapping

| CLONEID concept | Database source | PhysiCell concept |
|---|---|---|
| cell line or patient sample | `CellLinesAndPatients`, `Passaging.cellLine` | cell type or simulation label |
| seeding event | `Passaging.event='seeding'` | initial condition |
| harvest event | `Passaging.event='harvest'` | endpoint / validation time |
| passaging relationship | `passaged_from_id1`, `passaged_from_id2` | primary lineage backbone plus recorded secondary support |
| cell count | `Passaging.cellCount` | initial number or calibration target |
| corrected cell count | `Passaging.correctedCount` | preferred count observable |
| image-derived count | `QuPathEvaluation.cellCount_*` | count/confluence observable |
| area occupied | `Passaging.areaOccupied_um2` | confluence/density observable |
| flask surface area | `Flask.dishSurfaceArea_cm2` | simulation domain area |
| media | `Media`, `MediaIngredients` | environmental/resource assumptions |
| Perspective state | `Perspective.state`, `Perspective.whichPerspective` | molecular/cell-state label |
| Identity state | `Identity.state`, Perspective-specific fields | inferred clone/state label |
| treatment event/context | `Media.Stressor`, `Media.Stressor_concentration`, `Media.Stressor_unit` | simulation perturbation schedule |

The implementation should write this mapping to `runs/<run_id>/agent_plan.json` and to a human-readable section of `runs/<run_id>/model_selection_report.md`.

---

## Agent plan schema

Every run should produce an `agent_plan.json` containing:

- run ID and timestamp,
- database provenance summary,
- `CandidateSegment` inventory summary,
- selected lineage object,
- available and selected observables,
- constraints,
- candidate models,
- CLONEID-to-PhysiCell mapping,
- evaluation metrics,
- provenance,
- warnings.

Use a strict JSON schema in `src/cloneid_agent/schemas.py`.

---

## Evaluation metrics

Recommended metrics:

- time-series RMSE or normalized RMSE,
- endpoint distribution distance,
- held-out prediction error,
- AIC/BIC or explicit model-complexity penalty,
- event-history value by comparing event-aware and event-flattened models.

---

## Required final report

Each run must generate `runs/<run_id>/model_selection_report.md` including:

1. Executive summary.
2. Database provenance, `CandidateSegment` inventory, and lineage-object discovery summary.
3. Selected lineage object and why it was selected.
4. Available and selected observables.
5. CLONEID records used.
6. Candidate model families.
7. CLONEID-to-PhysiCell mapping.
8. Simulation settings.
9. Evaluation metrics.
10. Model comparison table.
11. Winning model.
12. Rejected alternatives.
13. Biological interpretation.
14. Limitations.
15. Reproducibility instructions.
16. Paths to generated PhysiCell files and simulation outputs.

Use restrained language: “supports,” “is sufficient to recapitulate,” “is inconsistent with,” and “rejected under the tested assumptions.” Avoid “proves” or “discovers the true mechanism.”

---

## Required final figure

Suggested panels:

1. CLONEID database as structured memory.
2. Agent database inventory, `CandidateSegment` ranking, and lineage-object selection.
3. CLONEID-to-PhysiCell mapping.
4. Candidate model families.
5. Observed versus simulated trajectories.
6. Model adjudication.

---

## Minimal viable proof of principle

The first working version should:

1. Connect to the CLONEID database in read-only mode.
2. Inventory CandidateSegments.
3. Construct the explicit lineage graph.
4. Discover `LineagePath` and `RootedTrajectoryBundle` objects from top-ranked CandidateSegment seeds.
5. Identify one longitudinal selected lineage object with repeated phenotype measurements.
6. Select cell count, image-derived count, or area occupied as the main time-series observable.
7. Select one endpoint Perspective distribution as the primary endpoint observable and retain Identity only as inferred secondary support.
8. Instantiate three model candidates: neutral growth, fixed state-specific fitness, and density-dependent growth.
9. Run or mock-run PhysiCell.
10. Compare observed and simulated trajectories.
11. Produce a model-selection report.
12. Produce a figure showing observed data, model predictions, and model ranking.

---

## Definition of done

The project is successful when a fresh user can run one command and obtain:

1. A database inventory.
2. A selected CLONEID lineage object (`LineagePath` or `RootedTrajectoryBundle`).
3. A structured agent plan.
4. Generated PhysiCell candidate models.
5. Simulation outputs or validated dry-run outputs.
6. Quantitative model comparison.
7. A reproducible report.
8. A publication-style figure.
