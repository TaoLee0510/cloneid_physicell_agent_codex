CLONEID is an **event-based framework** that preserves the context needed to interpret how genotype gives rise to phenotype over time: Events anchor specimen history, Phenotypes are directly witnessed intact-system states or behaviors, Perspectives are partial assay-specific molecular views, and Identities reconcile Perspectives into inferred clone-level objects.

## The main ontology misunderstandings to avoid

### 1. Misunderstanding “Event” as just a timepoint, passage number, or database row

**Wrong interpretation:**  
An Event is simply one row in `Passaging`, one timestamp, or one chronological measurement.

**Correct interpretation:**  
An Event records “what happened, when, and to which specimen.” It captures propagation, sampling, interventions, specimen relationships, and context. Importantly, Events are not merely chronological; they encode transitions into or out of physical/contextual states. The paper emphasizes that non-genesis Events link to precursor records and that this matters biologically because context changes such as seeding, transfer, biopsy, resection, implantation, or intervention may change selective constraints.

**Why it matters for dataset ranking:**  
If Codex treats Events as generic timepoints, it may rank datasets by number of rows rather than by whether the event graph is biologically interpretable. For PhysiCell, the Event layer should determine:

- initial conditions,
- transfer/seeding events,
- passage bottlenecks,
- environmental context,
- timing of observations,
- treatment/intervention schedules,
- endpoint sampling.

A dataset with fewer Events but clear transition structure may be more modelable than a dataset with many rows but ambiguous parentage/context.

---

### 2. Misunderstanding “Passaging” as only in vitro passaging

**Wrong interpretation:**  
Because the schema table is called `Passaging`, it must only refer to in vitro passage records.

**Correct interpretation:**  
The paper states that some historical schema names remain; most notably, `Passaging` implements event-linked specimen history. The manuscript-level concept is **Event**, while the implementation may still use historical table names.

**Why it matters for dataset ranking:**  
If Codex assumes `Passaging` means only cell-culture passaging, it may exclude clinical or in vivo histories, or fail to recognize that the same event backbone spans clinical, in vivo, and in vitro settings. The dataset-ranker should treat `Passaging` as the current implementation of the Event layer, not as a narrow biological category.

---

### 3. Misunderstanding “Phenotype” as any measured variable

**Wrong interpretation:**  
Any feature, including molecular readouts, copy-number profiles, transcriptomic states, karyotype clusters, or inferred CNA rates, is a phenotype.

**Correct interpretation:**  
Phenotype in CLONEID means directly witnessed, system-level state or behavior of an intact living system in context. It includes event-local phenotype state, such as morphology, confluence, tumor burden, or cell count, and behavioral phenotype inferred across repeated Events, such as growth or motility. Molecular readouts, even if dynamic or quantitative, are not Phenotypes.

**Why it matters for dataset ranking:**  
The agent should rank datasets highly when they contain repeated intact-system observations that can be compared to simulation outputs: cell counts, growth curves, area occupied, confluence, morphology, tumor volume, or imaging-derived behavior. It should not inflate the phenotype score just because a dataset has many transcriptomic or genomic features. Those are Perspectives, not Phenotypes.

For the CLONEID–PhysiCell paper, this is crucial because PhysiCell recapitulates **phenotypic behavior** over time. Molecular Perspectives can define states or endpoint constraints, but they are not the main observed trajectory unless transformed into a model-relevant state variable.

---

### 4. Misunderstanding event-linked evidence as phenotype itself

**Wrong interpretation:**  
Raw images, masks, segmentation files, QC outputs, and annotations are Phenotypes.

**Correct interpretation:**  
The ontology table distinguishes **event-linked evidence** from Phenotype. Event-linked evidence includes images, segmentations, counts, annotations, QC outputs, and other records attached to an Event. These may support Phenotype or Perspective interpretation, but they are not automatically Phenotype, Perspective, or Identity themselves.

**Why it matters for dataset ranking:**  
Codex should not simply count image files and assume the dataset has strong phenotypic observables. It must ask whether usable derived phenotype quantities exist or can be reproducibly derived:

- cell count,
- corrected count,
- area occupied,
- confluence,
- growth rate,
- tumor volume,
- morphology features.

A dataset with many images but no validated derived phenotype may be less immediately modelable than a dataset with fewer images but clean event-linked growth measurements.

---

### 5. Misunderstanding “Perspective” as any viewpoint, visualization, or analytical perspective

**Wrong interpretation:**  
A Perspective is a user’s analysis perspective, a plot, a visualization mode, or any dataset view.

**Correct interpretation:**  
A Perspective is an assay-specific molecular view of a specimen, subpopulation, or cell at a specific sampling moment and resolution. It represents a molecular layer such as genome, transcriptome, proteome, or karyotype while preserving provenance and assay context. It is inherently partial and snapshot-like.

**Why it matters for dataset ranking:**  
For modelability, Perspectives are useful when they can define:

- endpoint clone/state composition,
- molecularly defined cell states,
- initial or final karyotype distributions,
- transcriptomic/copy-number state labels,
- constraints on state transitions.

But they should not be treated as direct phenotype trajectories. A dataset with many Perspectives but no repeated intact-system phenotype may be excellent for molecular comparison but weak for a PhysiCell trajectory-recapitulation proof of principle.

---

### 6. Misunderstanding image-based molecular assays as Phenotype because they are images

**Wrong interpretation:**  
Anything image-based belongs to Phenotype.

**Correct interpretation:**  
The paper explicitly says CLONEID distinguishes Phenotype from Perspective by the **type of information represented**, not the measurement modality. Spatial molecular assays remain Perspectives, even when image-based, because they represent molecular layers.

**Why it matters for dataset ranking:**  
Codex may otherwise misclassify spatial transcriptomics, karyotype images, or imaging-derived molecular maps as Phenotypes. For PhysiCell integration, this would confuse:

- observed intact-system behavior,
- molecular state labels,
- endpoint constraints,
- calibration targets.

A karyotype image-derived ploidy state is better treated as a molecular Perspective or Identity-related endpoint, not as a directly witnessed behavioral phenotype.

---

### 7. Misunderstanding “Identity” as observed truth rather than inferred reconciliation

**Wrong interpretation:**  
Identity is the actual clone, directly observed and certain.

**Correct interpretation:**  
Identity is an inferred reconciliation object. It links one or more Perspectives judged to be consistent with the same clone-level biological unit across assays, samples, or time while preserving provenance. The paper emphasizes that Perspective records remain assay-specific, while Identity stores the inferred links grouping them into a shared clone representation.

**Why it matters for dataset ranking:**  
The agent should not treat Identity as ground truth. It should score Identity availability as valuable but also record:

- which Perspectives support the Identity,
- how many Perspectives were reconciled,
- whether the Identity is endpoint-only or longitudinal,
- whether uncertainty/provenance is available,
- whether Identity can be used as calibration or only validation.

For model comparison, Identity should often be an endpoint or state-label constraint, not an unquestioned direct observation.

---

### 8. Misunderstanding “Clone” as a fully observed cell lineage

**Wrong interpretation:**  
A clone is directly observed in full across time.

**Correct interpretation:**  
The paper defines clone operationally: a cell population inferred to share recent lineage and sufficiently similar underlying state to be treated as one evolving unit across measurements, samples, or time. The ontology table also states that a clone is not assumed to be observed directly in full; it is approximated through Events, Perspectives, Identities, and Phenotypes.

**Why it matters for dataset ranking:**  
Codex should not require perfect clone tracking to score a dataset as useful. A modelable dataset may have:

- event-linked phenotypes,
- endpoint molecular Perspectives,
- inferred Identities,
- partial clone/state continuity.

The ranker should score the **quality of linked evidence**, not demand impossible direct clone observability.

---

### 9. Misunderstanding “Specimen / study entity” as only a biological sample

**Wrong interpretation:**  
Specimen means only a tissue sample or physical aliquot.

**Correct interpretation:**  
The paper defines specimen/study entity broadly as the bearer of state whose history is organized. Depending on workflow, this may be a patient case, animal model, lineage, sample, or culture-derived entity.

**Why it matters for dataset ranking:**  
For agentic dataset selection, the unit being simulated may be:

- a cell-line branch,
- a culture lineage,
- a tumor-bearing animal,
- a patient tumor trajectory,
- a biopsy-derived specimen chain.

If Codex uses a narrow specimen definition, it may fail to group the correct records into a modelable trajectory.

---

### 10. Misunderstanding derived phenotype quantities as direct observations

**Wrong interpretation:**  
`cellCount`, `correctedCount`, `areaOccupied_um2`, and `cellSize_um2` are direct measurements with uniform meaning.

**Correct interpretation:**  
The paper states that several phenotype-associated quantities are derived rather than directly recorded. For microscopy events, stored cell counts are estimated from segmented image fields and scaled to full vessel surface area; `areaOccupied_um2` is similarly extrapolated; `cellSize_um2` is an aggregated summary, not a direct mean cell area. The paper also warns that preprocessing, QC filtering, manual image exclusion, and lineage-specific segmentation parameters can affect event-level values.

**Why it matters for dataset ranking:**  
For PhysiCell calibration, Codex must not treat all numeric fields as equally reliable. It should score datasets higher when:

- derived quantities have clear provenance,
- flask area is available,
- segmentation settings are interpretable,
- repeated observations are comparable within a lineage,
- QC exclusions are documented.

It should flag datasets where the same storage field may have modality-specific meaning or where derived quantities are not comparable across settings.

---

### 11. Misunderstanding storage-layer absence as data absence

**Wrong interpretation:**  
If raw images or segmentation artifacts are not in SQL, they are unavailable or irrelevant.

**Correct interpretation:**  
CLONEID separates relational metadata from large binary/file-based artifacts. The relational database stores the records needed to reconstruct context, while large phenotype imaging and segmentation artifacts are stored outside the relational database, under durable object-storage prefixes, with keys anchored to event-linked identifiers.

**Why it matters for dataset ranking:**  
Codex should not rank a dataset poorly just because raw images are not stored as SQL blobs. It should check whether object-backed phenotype assets exist and whether they can be materialized or summarized. Conversely, it should not assume it can access image-derived features unless the manifests or object keys are available.

---

### 12. Misunderstanding “context-bundled export” as merely a data download

**Wrong interpretation:**  
Export means downloading a flat dataset or CSV.

**Correct interpretation:**  
The paper describes context-bundled export as preserving the linkage between event history, phenotypic observations, and downstream molecular records. The exported object is designed as a portable partial database or subtree-based bundle, not a decontextualized table.

**Why it matters for dataset ranking:**  
For the agent workflow, the ranking unit should often be a **subtree / trajectory / event history**, not an individual table, sample, or file. The agent should ask: “Can I reconstruct a coherent longitudinal record?” not merely “Can I access measurements?”

---

## How this should change the dataset-ranking logic

I would add a new instruction file:

```text
ONTOLOGY_FOR_DATASET_RANKING.md
```

and require Codex to read it immediately before implementing or running dataset scoring.

The ranker should not simply score:

```text
number of rows + number of tables + number of images + number of omics records
```

It should score:

```text
coherent Event graph
+ repeated intact-system Phenotype
+ endpoint or longitudinal Perspective
+ Identity reconciliation/provenance
+ usable context for PhysiCell initialization
+ clear calibration/validation split
+ minimal ontology ambiguity
```

It should also distinguish between:

- `CandidateSegment`: a local context-consistent grouping used for first-stage screening
- `TrajectoryBundle`: a connected event-history modeling unit that may span multiple CandidateSegments

The top CandidateSegment is not automatically the final modeling unit. It is a seed for TrajectoryBundle discovery through `Passaging.passaged_from_id1` and `Passaging.passaged_from_id2`.

## Dataset-ranking criteria Codex should use

Stage 1 should keep the current CandidateSegment ranking as a fast screen.

Stage 2 should rank discovered TrajectoryBundles using a more biologically meaningful connected-history scorecard.

I would define the TrajectoryBundle score like this:

| Criterion | Score contribution | Why |
|---|---:|---|
| Connected CandidateSegment count | 0–1 | More connected local segments can reflect a richer but still coherent history. |
| Event graph depth | 0–2 | PhysiCell needs ancestry and temporal structure, not just isolated rows. |
| Context transition count | 0–1 | Passage, media, flask, and related shifts matter mechanistically. |
| Repeated intact-system Phenotype across the graph | 0–3 | Simulation outputs must be compared to observed behavior across the connected history. |
| Terminal Perspective support | 0–2 | Endpoint molecular state can constrain or validate model output. |
| Calibration/validation split potential | 0–2 | Needed for credible model adjudication within one connected history. |
| Initialization/context sufficiency | 0–2 | Need cell counts, geometry, timing, media/context, and interventions where applicable. |
| Identity reconciliation available | 0–1 | Useful as inferred secondary support, not direct phenotype. |
| Derived-measurement provenance | 0–1 | Prevents overconfidence in image-derived values. |
| Tractability penalty | −0 to −3 | Penalize bundles that are too fragmented, branched, or complex for a first proof of principle. |
| Ontology ambiguity penalty | −0 to −3 | Penalize units where fields are likely to be misinterpreted. |

This would make the agent pick the connected event history that best tests the CLONEID–PhysiCell handshake, not merely the local segment with the most data.

## Attachment policy that should be preserved in code

For TrajectoryBundle construction and ranking:

- attach `Perspective` directly via `Perspective.origin -> Passaging.id`
- attach `Identity` only as inferred secondary support
- do not count `Identity` as directly observed phenotype
- do not let raw Perspective row volume dominate repeated phenotype evidence

The workflow should save both stages explicitly:

- CandidateSegment rank and reasons
- TrajectoryBundle discovery summary
- TrajectoryBundle rank and component breakdown
