# Question Queue

This file is maintained by the agent. It accumulates precise questions for the user's review windows.

## Blocking before manuscript numerical results

## Q001 — Live CLONEID extraction or frozen SNU-668 snapshot

**Priority:** Blocking  
**Risk level:** 2  
**Question:** Should the manuscript-facing SNU-668 density-history application use live read-only CLONEID extraction or an approved frozen SNU-668 snapshot for numerical model-selection results?

**Why it matters:** The current dry-run uses deterministic mock/schema fixture values. They validate artifact generation and identifiability logic but cannot support biological numerical claims.

**Options:**
1. Live read-only CLONEID extraction through the approved CLONEID access path.
2. Approved frozen SNU-668 snapshot committed or mounted as an immutable input.
3. Keep mock mode only for methods/software demonstration and omit numerical SNU-668 claims.

**Current default assumption:** Use mock/dry-run mode for workflow validation only.

**Blocked work:** Manuscript numerical interpretation, train/test model fitting, and any quantitative claim about SNU-668 r/K density adaptation.

**Agent recommendation:** Use an approved frozen snapshot for manuscript reproducibility if available; otherwise use live read-only extraction with cached exported artifacts.

**Status:** Open

## Q002 — Exact SNU-668 root ID / subtree target

**Priority:** Blocking  
**Risk level:** 2  
**Question:** What exact SNU-668 `root_id` or subtree should the live/snapshot extraction target?

**Why it matters:** The event graph, seed-harvest episodes, transfer/bottleneck schedule, endpoint Perspective linkage, and history covariates depend on the selected root/subtree.

**Options:**
1. Provide a single approved root ID.
2. Provide a root ID plus branch/replicate filters.
3. Generate candidate SNU-668 subtrees and select the best scoring one after review.

**Current default assumption:** `cloneid_root_id=auto` remains a mock fixture selector until the live/snapshot target is approved.

**Blocked work:** Live `cloneid_full/` replacement and manuscript numerical model fitting.

**Agent recommendation:** Provide a single approved root ID if the intended LTE subtree is known; otherwise allow candidate subtree discovery and review.

**Status:** Open

## Q003 — Real NSR supplement path for this runtime

**Priority:** Important
**Risk level:** 1
**Question:** Should I remount/provide the real NSR supplement directory/archive for the next run, or continue using the deterministic fixture until the manuscript numerical branch is ready?

**Checked paths in this runtime:**
- `/Users/4482173/Documents/GitHub/cloneid_physicell_agent_codex/data/nwaa124_supplement_file`
- `/mnt/data/nwaa124_supplement_file.zip`

**Observed status:** Neither path was accessible from the current workspace during this pass.

**Why it matters:** The workflow can generate artifacts with a minimal fixture, but manuscript comparator interpretation should use the real NSR supplement archive or directory.

**Current default assumption:** Keep fixture fallback for dry-run validation; require the real supplement for manuscript comparator outputs.

**Status:** Open

## Q004 — Curated NSR CSV fallback policy

**Priority:** Important
**Risk level:** 1
**Question:** Should the curated NSR CSV fallback from `update_5.4` remain as a validation artifact, or be removed after automatic docx extraction is stable?

**Why it matters:** Automatic docx extraction is the primary `update_5.5` path. Curated CSV can be useful as regression/validation material, but it risks becoming a second source of truth if not clearly labeled.

**Options:**
1. Keep curated CSV only as validation/fallback and mark automatic docx extraction as authoritative.
2. Remove curated CSV once extraction tests cover the real supplement.
3. Keep both, with a comparison report showing discrepancies.

**Current default assumption:** Keep compatibility adapter logic only; do not make curated CSV a competing primary comparator.

**Status:** Open
