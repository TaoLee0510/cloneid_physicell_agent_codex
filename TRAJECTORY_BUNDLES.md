# Trajectory Bundles

## Purpose

The initial candidate ranker identifies local **CandidateSegments**, usually grouped by shared context fields such as cell line, growth type, passage, media, and flask. These segments are useful, but they are not always the biologically meaningful modeling unit.

Many meaningful biological changes arise over longer histories that span multiple passages, transfers, re-seedings, bottlenecks, harvests, treatments, media changes, flask changes, or other physical/contextual translocations of the biological entity.

Therefore, the CLONEID–PhysiCell workflow should distinguish:

```text
Event
→ CandidateSegment
→ LineagePath / RootedTrajectoryBundle
```

The selected lineage object, not the CandidateSegment, should become the preferred modeling unit for the CLONEID–PhysiCell handshake when longer connected histories are available.

---

## Definitions

### Event

An **Event** is a time-stamped record of what happened to a biological entity, including physical transfers, seeding, passaging, imaging, treatment, harvest, molecular sampling, or other contextual transitions.

An Event is not merely a timestamp, passage number, or database row. It anchors specimen history and provides the context needed to interpret linked Phenotypes, Perspectives, and Identities.

In the current CLONEID schema, the `Passaging` table is the primary implementation of the Event backbone.

---

### CandidateSegment

A **CandidateSegment** is a local group of records with shared context, such as:

- cell line,
- growth type,
- passage,
- media,
- flask.

CandidateSegments are useful for identifying local phenotype trajectories and compact modeling fragments. However, they may be too narrow to capture long-term biological change because they can split a connected biological history at exactly the transitions that may be mechanistically important.

Examples of transitions that may break CandidateSegments include:

- passage changes,
- flask changes,
- media changes,
- stressor introduction or withdrawal,
- seeding or re-seeding,
- physical transfer,
- bottlenecking,
- sampling,
- harvest for molecular assay.

A CandidateSegment should therefore be treated as a **local segment** or **seed**, not automatically as the final modeling unit.

---

### LineagePath

A **LineagePath** is an ancestor-to-endpoint lineage path recovered through `Passaging.passaged_from_id1`.

A LineagePath may span:

- multiple passages,
- multiple media conditions,
- multiple flasks,
- multiple physical transfers,
- multiple sampling events,
- one or more terminal molecular Perspectives.

The LineagePath is useful when a single ancestor-to-endpoint chain is the clearest modeling unit.

### RootedTrajectoryBundle

A **RootedTrajectoryBundle** is a rooted descendant event graph consisting of one or more CandidateSegments linked through CLONEID event relationships on the primary lineage backbone.

A RootedTrajectoryBundle may span:

- multiple passages,
- multiple media conditions,
- multiple flasks,
- multiple physical transfers,
- multiple sampling events,
- multiple local experiments,
- one or more terminal molecular Perspectives.

A RootedTrajectoryBundle should preserve the history of the biological entity or lineage across relevant physical and contextual transitions.

The RootedTrajectoryBundle is the preferred modeling unit when the goal is to understand biological change over time rather than only fit a local growth fragment.

---

## Why this matters

PhysiCell should often model a connected biological process, not only a local table grouping.

A context-local CandidateSegment may contain repeated measurements, but the biological mechanism may only become visible when the history is reconstructed across transitions.

Examples of biologically meaningful transitions include:

- seeding density changes,
- passaging bottlenecks,
- media changes,
- stressor introduction or withdrawal,
- transfer to a new vessel,
- harvest for molecular assay,
- splitting one lineage into multiple branches,
- merging or comparing related experimental branches.

The CLONEID–PhysiCell handshake should therefore ask:

> Is this high-ranking CandidateSegment part of a larger connected biological trajectory that is more meaningful than the segment alone?

---

## Implementation rule

Do not treat the top-ranked CandidateSegment as the final modeling unit by default.

Instead:

1. Use the top CandidateSegment as a seed.
2. Construct the explicit lineage graph through `Passaging.passaged_from_id1`.
3. Record `Passaging.passaged_from_id2` as secondary / exception / merge support.
4. Identify connected CandidateSegments.
5. Construct one or more `LineagePath` and `RootedTrajectoryBundle` objects.
6. Rank lineage objects for modelability.
7. Select a lineage object for record bundling and observable extraction.

The existing CandidateSegment ranking should remain useful as a first-stage screen. It should not be discarded.

The intended flow is:

```text
ranked CandidateSegment
→ explicit lineage graph construction
→ LineagePath / RootedTrajectoryBundle discovery
→ lineage-object ranking
→ selected lineage-object bundle
→ observable extraction
→ CLONEID-to-PhysiCell mapping
```

---

## Preferred first implementation

The first implementation should support conservative graph expansion.

Starting from a selected CandidateSegment, the workflow should:

1. Identify the Passaging records belonging to the seed CandidateSegment.
2. Expand upstream and downstream through `Passaging.passaged_from_id1`.
3. Record `Passaging.passaged_from_id2` as secondary lineage support without using it as the default expansion edge.
4. Stop expansion at a configurable depth or when a safety boundary is reached.
5. Record all context transitions encountered during expansion.
6. Attach Perspective records through `Perspective.origin`.
7. Attach Identity records only as inferred secondary support.
8. Preserve all source-record identifiers for provenance.

Reasonable initial safety boundaries include:

- stop if cell line changes,
- stop if the graph becomes excessively large,
- stop at a configurable maximum upstream depth,
- stop at a configurable maximum downstream depth,
- stop before including records with ambiguous parentage unless explicitly allowed,
- record excluded neighboring records and why they were excluded.

---

## Graph-expansion inputs

The first implementation should use these fields where available:

| CLONEID concept | Table / field | Role in lineage-object discovery |
|---|---|---|
| Event identifier | `Passaging.id` | Node identifier |
| Biological entity | `Passaging.cellLine` | Safety boundary and grouping context |
| Local context | `growthType`, `passage`, `media`, `flask` | CandidateSegment definition and transition detection |
| Event type | `Passaging.event` | Seeding, harvest, transfer, intervention, etc. |
| Event time | `Passaging.date` | Temporal ordering |
| Parent links | `passaged_from_id1`, `passaged_from_id2` | `passaged_from_id1` = primary lineage backbone; `passaged_from_id2` = recorded secondary support |
| Phenotype observables | `cellCount`, `correctedCount`, `areaOccupied_um2`, `cellSize_um2` | Repeated intact-system observations |
| Image-derived records | `QuPathEvaluation` | Optional phenotype evidence |
| Molecular endpoint | `Perspective.origin` | Links molecular Perspective to Event |
| Inferred clone support | `Identity` fields | Secondary inferred support only |

---

## Context transitions to record

A selected lineage object should explicitly record transitions across its event graph.

At minimum, record changes in:

- passage,
- media,
- flask,
- growth type,
- stressor identity,
- stressor concentration,
- seeding density if inferable,
- event type,
- cell count or density at transfer,
- harvest or sampling status,
- availability of terminal Perspectives.

These transitions are not nuisance variation. They may define the selective pressures or physical constraints that a PhysiCell model should represent.

---

## Ranking features for lineage objects

Lineage objects should be ranked separately from CandidateSegments.

Suggested features:

| Feature | Why it matters |
|---|---|
| `connected_segment_count` | Does the object span multiple local contexts? |
| `event_graph_depth` | Does it cover multiple biological transitions? |
| `event_count` | How much longitudinal history is available? |
| `transition_count` | Number of passage/media/flask/stressor/context changes. |
| `has_branching` | Branches allow stronger model comparison. |
| `has_longitudinal_context_change` | Captures selection across changing conditions. |
| `phenotype_observation_count` | Determines strength of calibration data. |
| `phenotype_time_span_days` | Determines longitudinal depth. |
| `terminal_perspective_support` | Molecular endpoint linked to terminal Event. |
| `identity_support_count` | Inferred clone/state support, secondary only. |
| `calibration_validation_split_possible` | Can fit early/one branch and test late/another branch? |
| `trajectory_bundle_complexity_penalty` | Avoids selecting huge unmanageable graphs first. |

---

## Suggested lineage-object scoring structure

The exact scoring weights can evolve, but the first implementation should separate these components:

```text
lineage-object score =
  event_graph_coherence
+ longitudinal_phenotype_strength
+ transition_information_value
+ molecular_endpoint_value
+ calibration_validation_potential
+ first_round_trip_tractability
- ambiguity_penalty
- excessive_complexity_penalty
```

### High-scoring lineage objects should have

- coherent event links,
- multiple connected CandidateSegments or multiple meaningful Events,
- repeated phenotype observations across time,
- at least one terminal or late molecular Perspective,
- enough context to initialize a PhysiCell model,
- a plausible calibration/validation split,
- manageable size for the first proof of principle.

### Penalize lineage objects with

- ambiguous parentage,
- disconnected fragments,
- excessive complexity,
- missing timing,
- missing initialization context,
- no phenotype observables,
- no terminal endpoint support,
- unclear modality or field meaning.

---

## Observable extraction from lineage objects

Observable extraction should happen after `LineagePath` or `RootedTrajectoryBundle` construction.

The extractor should distinguish:

1. **Phenotype observables**  
   Directly witnessed or derived intact-system observations, such as cell count, corrected count, area occupied, confluence, growth rate, tumor volume, or image-derived summaries.

2. **Event-linked evidence**  
   Images, segmentations, QC outputs, annotations, or analysis artifacts that support phenotype interpretation but are not automatically phenotypes themselves.

3. **Molecular Perspectives**  
   Assay-specific molecular readouts linked to Events, such as genome, transcriptome, karyotype, or proteome records.

4. **Identity support**  
   Inferred reconciliation across Perspectives. Identity should remain labeled as inferred and should not be treated as directly observed phenotype.

5. **Context variables**  
   Flask, media, stressor, passage, date, seeding/harvest status, and other variables needed to initialize or constrain PhysiCell models.

---

## PhysiCell mapping implications

The selected lineage object should provide the basis for CLONEID-to-PhysiCell mapping.

Potential mappings include:

| Lineage object element | PhysiCell role |
|---|---|
| first seeding event | initial condition |
| cell count / corrected count | initial cell number or calibration target |
| flask surface area | simulation domain size |
| media / stressor context | substrate or perturbation assumptions |
| repeated phenotype observations | time-series calibration / validation |
| passaging or transfer events | bottleneck / reset / reinitialization schedule |
| branch points | alternative trajectories or validation branches |
| terminal harvest event | endpoint comparison time |
| terminal Perspective | endpoint molecular/state constraint |
| Identity support | inferred clone/state interpretation, secondary only |

---

## Language rule

Use **CandidateSegment** for local context-specific groups.

Use **LineagePath** for ancestor-to-endpoint connected event histories.

Use **RootedTrajectoryBundle** for rooted descendant connected event histories.

Avoid using **experiment** as the main technical term, because:

- one experiment may contain multiple lineage objects,
- one lineage object may span multiple experimental branches,
- multiple experiments may together reveal one biological process,
- “experiment” is often a human organizational label rather than a precise modeling unit.

When user-facing language requires a more intuitive term, describe a selected lineage object as:

> a connected longitudinal event history spanning one or more local experimental segments.

---

## Minimal implementation artifacts

A lineage-object discovery run should write:

```text
runs/<run_id>/trajectory_bundle_candidates.json
runs/<run_id>/trajectory_bundle_candidates.md
runs/<run_id>/selected_trajectory_bundle.json
runs/<run_id>/selected_trajectory_bundle.md
runs/<run_id>/trajectory_bundle_graph.json
runs/<run_id>/trajectory_bundle_transitions.json
runs/<run_id>/ASSUMPTIONS.md
```

The Markdown report should include:

1. Seed CandidateSegment.
2. Expansion rules.
3. Included Events.
4. Excluded neighboring Events and reasons.
5. Connected CandidateSegments.
6. Context transitions.
7. Phenotype observations.
8. Terminal Perspectives.
9. Identity support, clearly labeled as inferred.
10. Tractability assessment for the first PhysiCell round trip.

---

## Testing requirements

Add deterministic tests using mock data.

Test cases should include:

1. A single CandidateSegment with no linked neighbors.
2. Two CandidateSegments connected by parent-child Event links.
3. A multi-passage trajectory with media or flask changes.
4. A branch point with two downstream children.
5. A terminal Perspective linked through `Perspective.origin`.
6. Identity records attached as secondary inferred support.
7. Ambiguous parentage that should trigger a warning or exclusion.
8. Expansion depth limits.
9. Prevention of cross-cell-line expansion by default.

The tests should verify that CandidateSegment ranking remains first-stage input and that lineage-object discovery creates a larger connected modeling unit when supported by the event graph.

---

## Stop / ask conditions

The agent should stop the lineage-object branch and ask the user if:

- the top CandidateSegment expands into multiple competing large bundles and no deterministic rule selects among them;
- parentage is ambiguous and affects the selected biological history;
- expansion requires crossing cell-line or patient boundaries;
- the best bundle depends on interpreting an undocumented field;
- the bundle would determine the main manuscript biological claim;
- the agent would need to assume missing event links or missing terminal Perspectives.

The agent should continue without asking if:

- expansion is read-only;
- expansion rules are conservative and documented;
- mock tests can be written;
- excluded records are documented;
- the work only creates scaffolding or reports;
- no biological claim is being made yet.

---

## Summary

CandidateSegments are useful local units, but they are not always the biologically meaningful modeling units.

For the CLONEID–PhysiCell proof of principle, the workflow should use high-ranking CandidateSegments as seeds, expand them through the `Passaging.passaged_from_id1` lineage backbone, record `passaged_from_id2` separately, and construct lineage objects that preserve the connected history over which biological change emerges.

The first real model should be built on a selected lineage object, not automatically on the top local CandidateSegment.
