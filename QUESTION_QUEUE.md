# Question Queue

This file is maintained by the agent. It accumulates precise questions for the user's review windows.

## Blocking before manuscript numerical results

## Q001 — Read-only CLONEID credential/access failure

**Priority:** Blocking
**Risk level:** 2
**Question:** Should the current `cloneid::connect2DB()` credentials be updated, or should the live run be executed from an environment where user `agent` is authorized?

**Observed failure:** The new live extractor reached the database host, but the database rejected the configured user:

```text
Access denied for user 'agent'@'47-200-2-146.fdr01.unvr.fl.ip.frontiernet.net'
```

**Why it matters:** `run-rk-benchmark --mode live` now performs real read-only extraction and intentionally fails if CLONEID access is not accepted. Manuscript numerical results cannot be generated until credentials/access are fixed.

**Current default assumption:** Keep code ready for live extraction; do not substitute mock data for live manuscript results.

**Status:** Open

## Q002 — Real NSR supplement path for this runtime

**Priority:** Important
**Risk level:** 1
**Question:** Should I remount/provide the real NSR supplement directory/archive for the next run, or continue using the deterministic fixture until the manuscript numerical branch is ready?

**Preferred path:**
- `/Users/4482173/Documents/GitHub/cloneid_physicell_agent_codex/data/nwaa124_supplement_file`

**Fallback path:**
- `/mnt/data/nwaa124_supplement_file.zip`

**Why it matters:** The workflow can generate artifacts with a minimal fixture, but manuscript comparator interpretation should use the real NSR supplement archive or directory.

**Status:** Open

## Q003 — Curated NSR CSV fallback policy

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

## Resolved in this pass

## Q004 — Exact SNU-668 r/K roots

**Status:** Answered

Use:

- `SNU-668_r2_A9_seed` for r cells
- `SNU-668_K3_A9_seed` for K cells

The live extractor now accepts these roots through:

```bash
--cloneid-root-id "SNU-668_r2_A9_seed,SNU-668_K3_A9_seed"
```
