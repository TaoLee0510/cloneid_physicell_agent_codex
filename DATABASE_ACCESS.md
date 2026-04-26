# CLONEID database access strategy

## Core principle

The agent should be given access to the **entire CLONEID database**, not isolated manually prepared exports.

The database is the source of truth. The agent should discover candidate datasets by querying the database, then select records for modeling based on modelability criteria.

Exports and snapshots are secondary. They may be used for:

- offline testing,
- regression tests,
- manuscript reproducibility,
- sharing a frozen run state,
- debugging without database access.

They should not be required for the primary workflow.

---

## Access policy

Use a read-only database account.

The code must only execute `SELECT` statements. It must never execute:

- `INSERT`
- `UPDATE`
- `DELETE`
- `DROP`
- `ALTER`
- `CREATE`
- `TRUNCATE`
- stored procedures that mutate data

If possible, enforce read-only mode at both levels:

1. Database user permissions.
2. Application-side query validation.

---

## Environment configuration

Do not hard-code credentials.

Use `.env` or environment variables.

Expected variable:

```bash
CLONEID_DB_READONLY_URL=mysql+pymysql://USER:PASSWORD@HOST:3306/CLONEID
```

An example file is provided as `.env.example`.

The workflow should also allow explicit CLI override:

```bash
python -m cloneid_agent run --db-url "$CLONEID_DB_READONLY_URL" ...
```

---

## Database adapter

Implement the database adapter in:

```text
src/cloneid_agent/db.py
```

The adapter should provide functions such as:

```python
get_engine(db_url: str)
check_readonly_connection(engine) -> dict
list_tables(engine) -> pandas.DataFrame
load_event_records(engine) -> pandas.DataFrame
load_context_records(engine) -> dict[str, pandas.DataFrame]
load_perspective_records(engine) -> pandas.DataFrame
load_identity_records(engine) -> pandas.DataFrame
load_qupath_records(engine) -> pandas.DataFrame
load_candidate_dataset_records(engine, dataset_id: str) -> dict[str, pandas.DataFrame]
```

All database calls should be centralized in `db.py`. Other modules should call typed functions rather than embedding ad hoc SQL throughout the codebase.

---

## Query provenance

Every run should save database provenance to:

```text
runs/<run_id>/database_provenance.json
```

Required fields:

```json
{
  "database_name": "CLONEID",
  "database_host_hash": "hash or redacted host identifier",
  "schema_tables_seen": [],
  "run_started_at": "ISO-8601 timestamp",
  "read_only_check_passed": true,
  "queries": [
    {
      "name": "load_event_records",
      "sql_template": "SELECT ...",
      "parameters": {},
      "row_count": 0,
      "output_file": "runs/<run_id>/database_cache/passaging.parquet"
    }
  ]
}
```

Do not store passwords or full database URLs in provenance files.

---

## Optional run-local cache

For reproducibility and speed, each run may write a cache of the records it actually used:

```text
runs/<run_id>/database_cache/
```

Recommended formats:

- Parquet for tabular records.
- JSON for small metadata summaries.
- CSV only for lightweight human inspection.

The cache should be treated as a frozen snapshot of records used in that run. It should not be edited manually.

---

## Core tables for first implementation

### `Passaging`

Primary event backbone.

Relevant fields:

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

### `QuPathEvaluation`

Image-analysis-derived phenotype data.

Relevant fields include:

- `id`
- `cellLine`
- `event`
- `passage`
- `date`
- `flask`
- multiple `cellCount_*` fields derived from image-analysis pipelines

### `Perspective`

Assay-specific molecular or state views linked to experimental origin.

Relevant fields:

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

The `origin` field links to `Passaging.id`.

### `Identity`

Inferred clone-level representations reconciled across Perspectives.

Relevant fields:

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

`Identity` is inferred and must not be treated as a directly observed phenotype.

### `CellLinesAndPatients`

Cell-line or patient metadata.

Relevant fields:

- `name`
- `doublingTime_hours`
- `year_of_first_report`
- `whichType`
- `source`

### `Flask`

Physical culture geometry and surface context.

Relevant fields:

- `id`
- `dishSurfaceArea_cm2`
- `surface_treated_type`
- `bottom_shape`

### `Media` and `MediaIngredients`

Environmental and treatment context.

Relevant fields include medium components, serum percentage, energy source, stressor, stressor concentration, and stressor unit.

---

## Candidate dataset discovery

The agent should discover modelable datasets using database queries rather than expecting named exports.

A candidate dataset may be defined as a connected event lineage or experimental branch in `Passaging`, possibly grouped by:

- cell line,
- growth type,
- passage range,
- media/stressor context,
- event lineage through `passaged_from_id1` and `passaged_from_id2`,
- availability of repeated phenotype measurements,
- availability of endpoint `Perspective` or `Identity` records.

For the first implementation, a pragmatic candidate dataset definition is:

> a group of `Passaging` records with the same `cellLine` and `growthType`, connected or partially connected by passaging relationships, spanning at least two time points, with at least one usable phenotype observable and at least one endpoint Perspective or Identity record.

The exact definition should be recorded in `dataset_inventory.json`.

---

## Suggested SQL query templates

### Event backbone

```sql
SELECT
  p.id,
  p.cellLine,
  p.event,
  p.passaged_from_id1,
  p.passaged_from_id2,
  p.growthType,
  p.passage,
  p.cellCount,
  p.correctedCount,
  p.date,
  p.media,
  p.flask,
  p.areaOccupied_um2,
  p.cellSize_um2,
  p.comment,
  p.owner,
  p.lastModified
FROM Passaging p;
```

### Event records with flask geometry and media context

```sql
SELECT
  p.id,
  p.cellLine,
  p.event,
  p.passaged_from_id1,
  p.passaged_from_id2,
  p.growthType,
  p.passage,
  p.cellCount,
  p.correctedCount,
  p.date,
  p.areaOccupied_um2,
  p.cellSize_um2,
  f.dishSurfaceArea_cm2,
  f.surface_treated_type,
  f.bottom_shape,
  m.Stressor,
  m.Stressor_concentration,
  m.Stressor_unit,
  m.FBS_pct,
  m.EnergySource,
  m.EnergySource_nM,
  m.comment AS media_comment
FROM Passaging p
LEFT JOIN Flask f ON p.flask = f.id
LEFT JOIN Media m ON p.media = m.id;
```

### Perspective records linked to event origin

```sql
SELECT
  pr.cloneID,
  pr.origin,
  pr.whichPerspective,
  pr.size,
  pr.parent,
  pr.sampleSource,
  pr.rootID,
  pr.profile_loci,
  pr.state,
  pr.alias,
  pr.hasChildren
FROM Perspective pr
WHERE pr.origin IS NOT NULL;
```

### Identity records

```sql
SELECT
  i.cloneID,
  i.whichPerspective,
  i.size,
  i.rootID,
  i.sampleSource,
  i.parent,
  i.KaryotypePerspective,
  i.GenomePerspective,
  i.ExomePerspective,
  i.TranscriptomePerspective,
  i.state,
  i.alias,
  i.hasChildren
FROM Identity i;
```

### QuPath/image-derived phenotype records

```sql
SELECT *
FROM QuPathEvaluation;
```

---

## Database inventory output

Every run should produce:

```text
runs/<run_id>/database_inventory.json
```

It should include:

```json
{
  "tables": [],
  "row_counts": {},
  "event_record_count": 0,
  "perspective_record_count": 0,
  "identity_record_count": 0,
  "qupath_record_count": 0,
  "cell_lines": [],
  "growth_types": [],
  "candidate_dataset_count": 0,
  "warnings": []
}
```

---

## Security and privacy notes

- Never commit `.env`.
- Never write database passwords to reports.
- Redact or hash hostnames in reports unless explicitly allowed.
- Do not expose patient-level identifiers in manuscript-facing output without deliberate review.
- Prefer run-local record identifiers over raw credentials or environment details.

---

## Testing without production access

If production database access is unavailable, use one of these options:

1. A local MySQL clone populated from a sanitized dump.
2. A small SQLite fixture that mimics relevant CLONEID tables.
3. A frozen run-local snapshot created by the `snapshot` command.

Tests should not require production credentials.
