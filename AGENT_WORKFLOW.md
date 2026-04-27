# CLONEID–PhysiCell Agent Workflow

## Purpose

This project implements a constrained, auditable agentic workflow that connects the **full CLONEID database** to PhysiCell mechanistic simulations.

The agent is **not** an unconstrained chatbot. It is a multi-step workflow that uses CLONEID as structured experimental memory, PhysiCell as the executable multicellular hypothesis engine, and a bounded planning layer to select datasets, instantiate candidate models, run simulations, and compare those simulations to observed data.

The goal is to demonstrate the following proof of principle:

> Given a full CLONEID database and a library of PhysiCell model templates, an agent can identify a dataset suitable for mechanistic simulation, select relevant observables and constraints, generate a small set of competing PhysiCell model candidates, run the simulations, compare outputs to observed CLONEID data, and produce an auditable model-selection report.

The desired final output is a figure and report showing that one PhysiCell model family recapitulates the selected CLONEID dataset better than several biologically plausible alternatives.

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
2. Inventory first-stage candidate segments.
3. Rank candidate segments and use top segments as seeds for connected-history discovery.
4. Discover one or more connected `TrajectoryBundle` objects suitable for simulation.
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
→ database inventory
→ CandidateSegment discovery
→ CandidateSegment ranking
→ TrajectoryBundle discovery from top-ranked segment seeds
→ TrajectoryBundle ranking / review
→ selected TrajectoryBundle record bundle
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
2. `TrajectoryBundle` ranking for connected biological histories that may span multiple CandidateSegments.

A modeling unit is modelable if it contains:

1. A clear event history.
2. Time-stamped repeated phenotypic observations.
3. At least one endpoint molecular Perspective or Identity readout.
4. Sufficient context to initialize a simulation.
5. At least two plausible competing model families.
6. At least one observable that can be compared between simulation and experiment.

### CandidateSegment definition

For the first implementation, define a `CandidateSegment` as a group of records from the database that share enough local experimental context to be summarized together.

Useful grouping fields include:

- `Passaging.cellLine`
- `Passaging.growthType`
- `Passaging.passage`
- `Passaging.media`
- `Passaging.flask`
- `Passaging.passaged_from_id1`
- `Passaging.passaged_from_id2`
- `Perspective.origin` for later attachment
- `Identity.rootID` or related fields where applicable as secondary support only

The implementation should record exactly how CandidateSegments were defined in `dataset_inventory.json`.

CandidateSegments are useful as first-stage ranking units, but they are not assumed to be the final biologically meaningful modeling unit. Changes in passage, transfer, media, flask, harvest, or bottleneck structure may split one connected biological history across multiple CandidateSegments.

### TrajectoryBundle definition

Define a `TrajectoryBundle` as a connected event-history modeling unit discovered from one or more CandidateSegment seeds by traversing:

- `Passaging.passaged_from_id1`
- `Passaging.passaged_from_id2`

A TrajectoryBundle should:

- expand upstream and downstream through the event graph,
- identify all connected CandidateSegments in scope,
- record context transitions across passage, media, flask, growth type, and related fields,
- attach `Perspective` records through `Perspective.origin`,
- attach `Identity` only as inferred secondary support.

The implementation should preserve the distinction:

- `CandidateSegment` = first-stage local screen
- `TrajectoryBundle` = preferred modeling unit when connected histories exist

### CandidateSegment score

Implement a first-stage CandidateSegment score from 0 to 5.

```text
+1 event history available
+1 repeated phenotype measurements available
+1 endpoint Perspective or Identity available
+1 experimental context sufficient for initialization
+1 multiple plausible mechanisms distinguishable
```

The agent should not assume the top-ranked CandidateSegment is the final selected dataset. It should use high-ranked CandidateSegments as seeds for TrajectoryBundle discovery.

### TrajectoryBundle ranking plan

TrajectoryBundle ranking should distinguish which connected histories are best suited for the first CLONEID-to-PhysiCell proof of principle.

Planned ranking features include:

- `connected_segment_count`
- `event_graph_depth`
- `transition_count`
- repeated phenotype observations across the graph
- terminal `Perspective` support
- calibration/validation split potential
- tractability penalty

The selected modeling unit should be the highest-priority reviewed TrajectoryBundle unless the user provides an override.

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
| passaging relationship | `passaged_from_id1`, `passaged_from_id2` | lineage/event graph |
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
- candidate dataset inventory summary,
- selected dataset,
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
2. Database provenance, CandidateSegment inventory, and TrajectoryBundle discovery summary.
3. Selected TrajectoryBundle and why it was selected.
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
2. Agent database inventory, CandidateSegment ranking, and TrajectoryBundle selection.
3. CLONEID-to-PhysiCell mapping.
4. Candidate model families.
5. Observed versus simulated trajectories.
6. Model adjudication.

---

## Minimal viable proof of principle

The first working version should:

1. Connect to the CLONEID database in read-only mode.
2. Inventory CandidateSegments.
3. Discover connected TrajectoryBundles from top-ranked CandidateSegment seeds.
4. Identify one longitudinal TrajectoryBundle with repeated phenotype measurements.
5. Select cell count, image-derived count, or area occupied as the main time-series observable.
6. Select one endpoint Perspective distribution as the primary endpoint observable and retain Identity only as inferred secondary support.
7. Instantiate three model candidates: neutral growth, fixed state-specific fitness, and density-dependent growth.
8. Run or mock-run PhysiCell.
9. Compare observed and simulated trajectories.
10. Produce a model-selection report.
11. Produce a figure showing observed data, model predictions, and model ranking.

---

## Definition of done

The project is successful when a fresh user can run one command and obtain:

1. A database inventory.
2. A selected CLONEID TrajectoryBundle.
3. A structured agent plan.
4. Generated PhysiCell candidate models.
5. Simulation outputs or validated dry-run outputs.
6. Quantitative model comparison.
7. A reproducible report.
8. A publication-style figure.
