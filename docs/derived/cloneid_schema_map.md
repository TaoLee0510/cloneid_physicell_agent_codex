# CLONEID Schema Map

## Scope

This is a first-pass schema map for the CLONEID-PhysiCell agent. It combines:

- repository guidance in `docs/CLONEID_SCHEMA_NOTES.md`,
- database-access expectations in `DATABASE_ACCESS.md`,
- direct live inspection through `cloneid::connect2DB()` and read-only `DBI` queries.

It is not a full schema reference. It is a working map for deterministic inventory and CLONEID-to-PhysiCell handshake code.

Inspection basis:

- package interface: `cloneid::connect2DB()`
- table enumeration: `DBI::dbListTables()`
- field enumeration: `DBI::dbListFields()`
- row counts and simple summaries via `DBI::dbGetQuery()`

## Main concept map

```text
CellLinesAndPatients
        ^
        | Passaging.cellLine = CellLinesAndPatients.name
        |
Passaging ---- Passaging.flask ----> Flask
    |
    | Passaging.media = Media.id
    v
   Media ---- descriptive ingredient names ----> MediaIngredients
    |
    +-- stressor / nutrient / oxygen context
    |
    +-- environmental assumptions for PhysiCell

Passaging.id ---- Perspective.origin
    |
    +-- event backbone for longitudinal phenotype and endpoint linkage

Perspective ---- inferred reconciliation ----> Identity
```

## Primary workflow tables

### 1. `Passaging`

Role:

- primary event-history backbone
- nearest thing to the longitudinal experimental graph
- source for event timing, parent-child lineage, growth context, and several phenotype observables

Observed fields most relevant now:

- `id`
- `cellLine`
- `event`
- `passaged_from_id1`
- `passaged_from_id2`
- `growthType`
- `passage`
- `cellCount`
- `correctedCount`
- `date`
- `media`
- `flask`
- `areaOccupied_um2`
- `cellSize_um2`
- `comment`

Observed additional operational/audit fields:

- `owner`
- `lastModified`
- `transactionId`
- `lastModifiedDate`

Agent interpretation:

- `Passaging.id` is the anchor ID for downstream joins into endpoint molecular observations.
- `passaged_from_id1` and `passaged_from_id2` define the event lineage graph to preserve.
- `event` distinguishes seeding and harvest semantics and should not be flattened away.

### 2. `QuPathEvaluation`

Role:

- image-derived phenotype / cell-count table
- event-like companion table for richer image-based observables

Observed fields most relevant now:

- `id`
- `cellLine`
- `event`
- `passaged_from_id1`
- `passaged_from_id2`
- `growthType`
- `passage`
- `cellCount`
- `date`
- `media`
- `flask`
- `cellCount_brightnessCorrection`
- `cellCount_brightnessCorrection2`
- `cellCount_standard`
- `cellCount_cellpose`
- `cellCount_cellpose_g65`
- `cellCount_cellpose_flowThresh80`
- `cellCount_QCmetrics`

Agent interpretation:

- this table is a candidate source for alternative count observables
- field choice should remain conservative and explicit
- QC-linked fields should be recorded when a specific image-derived count source is selected

### 3. `Perspective`

Role:

- assay-specific molecular or state view
- linked to an experimental origin through `origin`

Observed fields most relevant now:

- `whichPerspective`
- `size`
- `parent`
- `origin`
- `sampleSource`
- `rootID`
- `cloneID`
- `profile_loci`
- `state`
- `alias`
- `hasChildren`

Observed additional fields:

- `profile`
- `profile_hash`
- `coordinates`
- `transactionId`

Agent interpretation:

- `Perspective.origin -> Passaging.id` is the key endpoint join for the first real-data handshake
- `whichPerspective` partitions molecular viewpoints and will matter for endpoint-state interpretation
- `size`, `state`, and `sampleSource` are likely core fields for endpoint summary inventory

### 4. `Identity`

Role:

- inferred clone-level reconciliation layer across Perspectives

Observed fields most relevant now:

- `size`
- `whichPerspective`
- `rootID`
- `sampleSource`
- `cloneID`
- `parent`
- `KaryotypePerspective`
- `GenomePerspective`
- `ExomePerspective`
- `TranscriptomePerspective`
- `profile_loci`
- `state`
- `alias`
- `hasChildren`

Observed additional fields:

- `profile`
- `profile_hash`
- `coordinates`

Agent interpretation:

- `Identity` is inferred and must remain labeled as inferred
- it should not be treated as directly observed phenotype
- it is valuable for endpoint-state summaries and for cross-perspective reconciliation logic later

## Context tables

### `CellLinesAndPatients`

Role:

- cell-line or patient-level metadata

Observed relevant fields:

- `name`
- `doublingTime_hours`
- `year_of_first_report`
- `whichType`
- `source`

Likely join:

- `Passaging.cellLine = CellLinesAndPatients.name`

### `Flask`

Role:

- physical culture geometry

Observed relevant fields:

- `id`
- `dishSurfaceArea_cm2`
- `surface_treated_type`
- `bottom_shape`

Likely join:

- `Passaging.flask = Flask.id`

### `Media`

Role:

- environment, nutrient, and stressor context

Observed relevant fields:

- `id`
- `base1`, `base1_pct`
- `base2`, `base2_pct`
- `FBS`, `FBS_pct`
- `EnergySource`, `EnergySource_nM`
- `EnergySource2`, `EnergySource2_pct`
- `Stressor`, `Stressor_concentration`, `Stressor_unit`
- `oxygen_pct`
- `comment`

Likely join:

- `Passaging.media = Media.id`

### `MediaIngredients`

Role:

- descriptive metadata about medium ingredients and compounds

Observed relevant fields:

- `name`
- `vendor`
- `catalogue_number`
- `reference_number`
- `description`

Note:

- no direct key relationship to `Media` has been established from current inspection alone
- treat this as descriptive support rather than a first-pass required join

## Additional visible tables

Visible during live inspection:

- `CellSurfaceMarkers_hg19`
- `Crypgene_LiquidNitrogenBackup`
- `FlowCytometry`
- `IdentitySub`
- `LiquidNitrogen`
- `Loci`
- `Minus80Freezer`
- `Passaging_backup_2025_10_09`
- `PerspectivePartial`
- `ToDelete_MorphologyPerspective`

Current interpretation:

- these tables are not first-pass requirements for the CLONEID-to-PhysiCell handshake
- some may be useful later for molecular detail, partial profiles, or provenance
- backup / freezer / deletion-marked tables should not drive the first mechanistic proof of principle

## First-pass join map for the agent

Recommended initial join graph:

```text
Passaging.cellLine -> CellLinesAndPatients.name
Passaging.flask    -> Flask.id
Passaging.media    -> Media.id
Perspective.origin -> Passaging.id
```

Later / conditional:

```text
Identity.sampleSource / rootID / perspective-link fields
    -> Perspective / endpoint summaries
```

## Data products supported by this schema map

### Table-level inventory

Supported now:

- table list
- row counts
- field lists
- basic table summaries

### Candidate dataset discovery

Supported next:

- grouping by `Passaging.cellLine`
- grouping by `Passaging.growthType`
- traversal of `passaged_from_id1` / `passaged_from_id2`
- linkage of endpoint `Perspective.origin`
- context attachment from `Flask` and `Media`

### Observable extraction

Likely first-pass observables:

- `Passaging.correctedCount`
- `Passaging.cellCount`
- `Passaging.areaOccupied_um2`
- selected `QuPathEvaluation.cellCount_*`
- endpoint `Perspective.size` / `Perspective.state`
- inferred endpoint `Identity.size` / `Identity.state` with explicit provenance label

## Provenance rules implied by the schema

Minimum provenance unit:

- source table
- primary key or join key
- role in the run
- fields used

Recommended record examples:

```json
{
  "source_table": "Passaging",
  "primary_key": "some_passaging_id",
  "role": "longitudinal_observable",
  "fields_used": ["date", "correctedCount", "areaOccupied_um2"]
}
```

```json
{
  "source_table": "Perspective",
  "primary_key": "some_clone_id",
  "role": "endpoint_state_summary",
  "fields_used": ["origin", "whichPerspective", "size", "state"]
}
```

## Current uncertainties

Level 0:

- `Passaging` is the event backbone
- `Perspective.origin -> Passaging.id` is the most important endpoint link
- `CellLinesAndPatients`, `Flask`, and `Media` are first-pass context tables

Level 1:

- using generic grouping by `cellLine`, `growthType`, and passaging lineage as the initial candidate-dataset definition

Level 2:

- exact calibration-vs-validation use of endpoint Perspective versus Identity in the first real proof of principle
- exact logic for linking `MediaIngredients` into mechanistic environment summaries

## Immediate implementation consequences

This map is sufficient to support the next deterministic modules:

1. inventory schema objects
2. candidate-dataset inventory queries
3. context-table attachment
4. observable availability scoring
5. provenance object design
