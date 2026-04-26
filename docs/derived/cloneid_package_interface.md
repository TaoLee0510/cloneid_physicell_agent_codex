# cloneid Package Interface for Read-Only Inventory

## Scope

This note documents the installed `cloneid` R package interface relevant to safe, read-only CLONEID database inventory.

Inspection date: 2026-04-25  
Installed package version: `1.2.2`

## Key finding

The installed package already contains the database credentials and exposes a connection helper:

- `connect2DB()`

This is the approved path for database access in the current environment.

## How `connect2DB()` works

`connect2DB()` takes no arguments. Its body shows that it:

1. loads `RMySQL`,
2. reads package-local YAML config from `system.file(package = "cloneid")/config/config.yaml`,
3. extracts `mysqlConnection` fields from that YAML,
4. opens a MySQL connection with `dbConnect()`,
5. returns the connection object.

Implication:

- The first inventory implementation does not need a separate checked-in `.env` credential path.
- The first inventory wrapper should call `cloneid::connect2DB()` and then use `DBI` functions directly.

## Recommended read-only inventory pattern

The package does not appear to provide a dedicated inventory API. The safe pattern is:

1. open a connection with `cloneid::connect2DB()`,
2. use `DBI::dbListTables()` to enumerate tables,
3. use `DBI::dbListFields()` to inspect schema,
4. use `DBI::dbGetQuery()` with explicit `SELECT` statements for counts and summaries,
5. disconnect with `DBI::dbDisconnect()`.

Minimal pattern:

```r
library(cloneid)
library(DBI)

con <- connect2DB()
on.exit(dbDisconnect(con), add = TRUE)

tables <- dbListTables(con)
fields <- lapply(tables, function(t) dbListFields(con, t))
counts <- lapply(
  tables,
  function(t) dbGetQuery(con, sprintf("SELECT COUNT(*) AS n FROM `%s`", t))
)
```

## Safe vs unsafe package surface

### Safe for read-only inventory

- `connect2DB()`
- `DBI::dbListTables()`
- `DBI::dbListFields()`
- `DBI::dbGetQuery()` with explicit `SELECT` statements

### Not appropriate for inventory wrappers

Many exported package functions appear to be workflow/manipulation helpers for CLONEID operations rather than passive inventory functions. Examples include:

- `seed`
- `harvest`
- `feed`
- `inject`
- `resect`
- `updateLiquidNitrogen`
- `removeFromLiquidNitrogen`

These should not be used by this project’s agent pipeline.

Even some read-style functions are too specific for a generic inventory layer because they embed fixed SQL assumptions and analysis logic:

- `readGrowthRate(cellLine)`
- `plotCellLineHistory()`
- `getPerspectivesPerIdentity(sName, whichP = "GenomePerspective")`
- `countCellsPerIdentity(sName, state = "G0G1")`

These are useful as examples of table relationships, but the inventory code should not depend on them.

## Example package functions inspected

### `readGrowthRate(cellLine)`

This function:

- queries `Passaging`,
- self-joins parent and child passaging rows,
- restricts to `P2.event = 'harvest'`,
- computes a simple per-day growth-rate expression using `DATEDIFF()` and cell counts.

Interpretation:

- `Passaging` is actively used by the package as the event-history backbone.
- Parent-child lineage links via `passaged_from_id1` are operational in the installed package.

### `plotCellLineHistory()`

This function runs:

```sql
select name, year_of_first_report, doublingTime_hours
from CellLinesAndPatients
where year_of_first_report > 0
```

Interpretation:

- `CellLinesAndPatients` is used as a context/metadata table.
- The package treats it as a clean lookup table for cell-line-level metadata.

### `getPerspectivesPerIdentity()`

This function performs joins across:

- `Perspective`
- `Identity`

Interpretation:

- `Identity` and `Perspective` are operationally linked in the package.
- These joins can inform later endpoint-state inventory logic.

## Core tables observed through `connect2DB()`

The following tables were visible during inspection:

- `CellLinesAndPatients`
- `CellSurfaceMarkers_hg19`
- `Crypgene_LiquidNitrogenBackup`
- `Flask`
- `FlowCytometry`
- `Identity`
- `IdentitySub`
- `LiquidNitrogen`
- `Loci`
- `Media`
- `MediaIngredients`
- `Minus80Freezer`
- `Passaging`
- `Passaging_backup_2025_10_09`
- `Perspective`
- `PerspectivePartial`
- `QuPathEvaluation`
- `ToDelete_MorphologyPerspective`

## Row counts observed during inspection

These counts are an inspection snapshot, not a stable contract:

| Table | Rows |
|---|---:|
| `CellLinesAndPatients` | 220 |
| `CellSurfaceMarkers_hg19` | 4267 |
| `Crypgene_LiquidNitrogenBackup` | 13 |
| `Flask` | 22 |
| `FlowCytometry` | 41 |
| `Identity` | 87 |
| `IdentitySub` | 9 |
| `LiquidNitrogen` | 7371 |
| `Loci` | 198 |
| `Media` | 108 |
| `MediaIngredients` | 70 |
| `Minus80Freezer` | 810 |
| `Passaging` | 11917 |
| `Passaging_backup_2025_10_09` | 11524 |
| `Perspective` | 187925 |
| `PerspectivePartial` | 264004 |
| `QuPathEvaluation` | 5124 |
| `ToDelete_MorphologyPerspective` | 257940 |

## Core fields observed for first-pass inventory

### `Passaging`

- `id`
- `cellLine`
- `event`
- `passaged_from_id1`
- `passaged_from_id2`
- `growthType`
- `passage`
- `cellCount`
- `date`
- `comment`
- `media`
- `flask`
- `correctedCount`
- `areaOccupied_um2`
- `cellSize_um2`

Additional audit/operational fields are present, including `owner`, `lastModified`, `transactionId`, and `lastModifiedDate`.

### `QuPathEvaluation`

- `id`
- `cellLine`
- `event`
- `passaged_from_id1`
- `passaged_from_id2`
- `growthType`
- `passage`
- `cellCount`
- `date`
- `comment`
- `media`
- `flask`
- `cellCount_brightnessCorrection`
- `cellCount_brightnessCorrection2`
- `cellCount_standard`
- `cellCount_cellpose`
- `cellCount_cellpose_g65`
- `cellCount_cellpose_flowThresh80`
- `cellCount_QCmetrics`

### `Perspective`

- `whichPerspective`
- `size`
- `parent`
- `profile`
- `profile_hash`
- `origin`
- `sampleSource`
- `coordinates`
- `rootID`
- `cloneID`
- `profile_loci`
- `state`
- `alias`
- `hasChildren`

### `Identity`

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
- `coordinates`
- `profile_loci`
- `state`
- `alias`
- `hasChildren`

### Context tables

- `CellLinesAndPatients`: `name`, `doublingTime_hours`, `year_of_first_report`, `whichType`, `source`
- `Flask`: `id`, `dishSurfaceArea_cm2`, `surface_treated_type`, `bottom_shape`
- `Media`: medium composition plus stressor/environment fields
- `MediaIngredients`: ingredient metadata

## Recommended first inventory outputs through this interface

Using `connect2DB()` plus `DBI`, the first inventory wrapper should produce:

1. table list,
2. row counts,
3. field lists for core tables,
4. distinct `Passaging.cellLine` counts,
5. counts of `Passaging.event` values,
6. counts of non-null repeated-phenotype fields:
   - `correctedCount`
   - `areaOccupied_um2`
   - selected `QuPathEvaluation.cellCount_*` fields
7. counts of `Perspective.origin` links into `Passaging`,
8. counts of `Identity.sampleSource` / `rootID` groups,
9. candidate dataset summaries grouped generically rather than by preselected biology.

## Important execution note

In this environment, `connect2DB()` required network-capable execution outside the default sandbox. The package interface itself is valid, but unattended inventory code may need the same permission model unless runtime/network settings change.

## Implementation recommendation

The first production wrapper should be a small R script or a Python-to-R bridge that:

1. calls `cloneid::connect2DB()`,
2. performs explicit read-only `SELECT` queries,
3. writes JSON/CSV summaries into `runs/<run_id>/`,
4. records query text for provenance,
5. avoids all mutating CLONEID package functions.

## Implemented wrapper

This wrapper is now implemented in the repository as:

- `scripts/cloneid_inventory.R`
- `src/cloneid_agent/cli.py`
- `src/cloneid_agent/inventory.py`

Manual entry points:

```bash
Rscript scripts/cloneid_inventory.R --mode auto --output runs/inventory_auto
```

```bash
PYTHONPATH=src python -m cloneid_agent inventory --mode auto --output runs/inventory_auto
```

Mode behavior:

- `--mode live`
  - attempts the live read-only database inventory through `cloneid::connect2DB()`
- `--mode mock`
  - writes a mock inventory from the previously discovered schema/table snapshot
- `--mode auto`
  - tries live access first and falls back gracefully to mock output on connection failure

Validation completed:

- mock mode verified locally
- graceful live-failure fallback verified locally
- live mode verified with network-capable execution

Current observed sandbox limitation:

- inside the default sandbox, live mode may fail with host-resolution/network errors
- the wrapper captures that exact error message in output and falls back to mock mode in `auto`

Non-blocking live warning observed:

- MySQL field type 7 was imported as character for some date-like fields during live verification
- this did not block inventory generation, but later schema-normalization code should handle date typing explicitly
