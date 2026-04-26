# CLONEID schema notes for the CLONEID–PhysiCell agent

These notes summarize schema concepts relevant to the agent workflow. They are not a complete schema reference.

The agent should query the full CLONEID database through a read-only connection. Do not assume individual exports have been prepared.

---

## Event backbone: `Passaging`

`Passaging` is the main event-history table.

Important fields:

- `id`: primary event/sample identifier.
- `cellLine`: linked to `CellLinesAndPatients.name`.
- `event`: currently `seeding` or `harvest`.
- `passaged_from_id1`, `passaged_from_id2`: parent event/sample links.
- `growthType`: experimental growth context.
- `passage`: passage number.
- `cellCount`: measured cell count.
- `correctedCount`: corrected count, preferred when available and documented.
- `date`: event timestamp.
- `media`: linked to `Media.id`.
- `flask`: linked to `Flask.id`.
- `areaOccupied_um2`: image-derived or field-derived occupied area.
- `cellSize_um2`: estimated cell size.
- `comment`: free-text experimental context.

For PhysiCell mapping, `Passaging` provides:

- event sequence,
- initial conditions,
- endpoint events,
- passaging graph,
- temporal spacing,
- growth/density observables,
- links to context tables.

---

## Image-derived phenotype: `QuPathEvaluation`

`QuPathEvaluation` contains image-analysis-derived cell-count fields and related event-like metadata.

Potentially useful fields:

- `id`
- `cellLine`
- `event`
- `passaged_from_id1`
- `passaged_from_id2`
- `growthType`
- `passage`
- `date`
- `flask`
- `cellCount_brightnessCorrection`
- `cellCount_brightnessCorrection2`
- `cellCount_standard`
- `cellCount_cellpose`
- `cellCount_cellpose_g65`
- `cellCount_cellpose_flowThresh80`
- `cellCount_QCmetrics`

The implementation should select image-derived count fields conservatively and record why a given field was selected.

---

## Molecular Perspective: `Perspective`

`Perspective` represents assay-specific molecular or state views linked to an experimental origin.

Important fields:

- `cloneID`: primary identifier for a Perspective record.
- `origin`: links to `Passaging.id`.
- `whichPerspective`: type of molecular or assay-specific view.
- `size`: abundance or size of this Perspective state.
- `parent`: parent clone/state relationship.
- `sampleSource`: source label.
- `rootID`: root identity or tree identifier.
- `profile_loci`: link to `Loci.id`.
- `state`: state label.
- `alias`: human-readable alias.
- `hasChildren`: whether this state has children.

For PhysiCell mapping, `Perspective` may provide endpoint state distributions or molecular labels.

---

## Inferred Identity: `Identity`

`Identity` represents inferred clone-level identities reconciled across Perspectives.

Important fields:

- `cloneID`
- `size`
- `whichPerspective`
- `rootID`
- `sampleSource`
- `parent`
- `KaryotypePerspective`
- `GenomePerspective`
- `ExomePerspective`
- `TranscriptomePerspective`
- `state`
- `alias`
- `hasChildren`

Important interpretability rule:

> `Identity` is inferred. It must not be treated as a directly witnessed phenotype.

In reports, distinguish directly observed phenotype records from inferred Identity records.

---

## Context tables

### `CellLinesAndPatients`

Contains cell-line and patient metadata.

Useful fields:

- `name`
- `doublingTime_hours`
- `year_of_first_report`
- `whichType`
- `source`

### `Flask`

Contains culture vessel and surface geometry information.

Useful fields:

- `id`
- `dishSurfaceArea_cm2`
- `surface_treated_type`
- `bottom_shape`

### `Media`

Contains medium, nutrient, and stressor/treatment context.

Useful fields:

- `id`
- `base1`, `base1_pct`
- `base2`, `base2_pct`
- `FBS`, `FBS_pct`
- `EnergySource`, `EnergySource_nM`
- `EnergySource2`, `EnergySource2_pct`
- `Stressor`, `Stressor_concentration`, `Stressor_unit`
- `comment`

### `MediaIngredients`

Contains metadata about medium ingredients, drugs, nutrients, and stressors.

Useful fields:

- `name`
- `vendor`
- `catalogue_number`
- `description`

---

## First implementation assumptions

The first implementation may treat a candidate dataset as records grouped by:

- `cellLine`,
- `growthType`,
- related `Passaging` parent-child links,
- repeated phenotype measurements,
- endpoint `Perspective.origin` links.

This definition should be made explicit in the output report and can be refined later.

---

## Provenance requirements

Every selected record should remain traceable to the source database table and primary key.

Recommended provenance record format:

```json
{
  "source_table": "Passaging",
  "primary_key": "HGC27_...",
  "role": "calibration_observable",
  "fields_used": ["date", "correctedCount", "areaOccupied_um2"],
  "notes": "used for longitudinal growth trajectory"
}
```

---

## Recommended first joins

Use `Passaging` as the central table.

Recommended joins:

```text
Passaging.cellLine → CellLinesAndPatients.name
Passaging.flask → Flask.id
Passaging.media → Media.id
Perspective.origin → Passaging.id
```

`Identity` may not always link directly to `Passaging.id`; the implementation should document exactly how Identity records are associated with selected dataset records.
