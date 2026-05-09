# Status checkpoint

This file is maintained by the agent. It records the current reviewable state of the repository.

## Current state

- Current branch: `update_5.5`
- Last committed baseline before this pass: `cc9569e`
- Current work unit: connect `run-rk-benchmark --mode live` to read-only CLONEID extraction for the approved SNU-668 A9 r/K roots.
- Current work state: completed and tested.
- Approved roots:
  - `SNU-668_r2_A9_seed` for r cells
  - `SNU-668_K3_A9_seed` for K cells

## What changed in this pass

- Added a read-only R extractor:
  - `scripts/cloneid_rk_benchmark_records.R`
- Added Python conversion/wrapper logic:
  - `src/cloneid_agent/cloneid_live_rk_extraction.py`
- Updated `run-rk-benchmark` so `--mode live`:
  - parses comma/space-separated root IDs,
  - calls the live R extractor through `cloneid::connect2DB()`,
  - traverses descendants through `Passaging.passaged_from_id1`,
  - attaches `Perspective` through `Perspective.origin`,
  - keeps `Identity` as inferred secondary support,
  - writes raw live extraction to `cloneid_full/live_cloneid_rk_extraction_raw.json`,
  - fails loudly on live extraction errors instead of silently substituting mock data.
- `--mode auto` can still fall back to deterministic mock if live extraction fails.
- Added live-conversion tests:
  - `tests/test_cloneid_live_rk_extraction.py`
- Made growth-episode/model fitting more robust to missing live counts or missing confluence fields.
- Updated README and application docs with the live SNU-668 A9 command.

## Live CLONEID check

Attempted read-only live extraction:

```bash
Rscript scripts/cloneid_rk_benchmark_records.R \
  --mode live \
  --root-id SNU-668_r2_A9_seed \
  --root-id SNU-668_K3_A9_seed \
  --output /tmp/cloneid_rk_live_records.json
```

Result:

- Network/DNS succeeded after running outside the sandbox.
- Database rejected the current configured user:
  - `Access denied for user 'agent'@'47-200-2-146.fdr01.unvr.fl.ip.frontiernet.net'`
- Interpretation: the new live code path reaches the CLONEID database host, but the current credentials do not have access from this environment.

## Commands run

```bash
PYTHONPATH=src:tests python3 -m unittest tests/test_cloneid_live_rk_extraction.py
Rscript scripts/cloneid_rk_benchmark_records.R --mode mock --root-id SNU-668_r2_A9_seed --root-id SNU-668_K3_A9_seed --output /tmp/cloneid_rk_mock_records.json
Rscript scripts/cloneid_rk_benchmark_records.R --mode live --root-id SNU-668_r2_A9_seed --root-id SNU-668_K3_A9_seed --output /tmp/cloneid_rk_live_records.json
PYTHONPATH=src:tests python3 -m unittest discover -s tests
PYTHONPATH=src python3 -m cloneid_agent.cli run-rk-benchmark --config configs/applications/snu668_density_history.yaml --cloneid-root-id "SNU-668_r2_A9_seed,SNU-668_K3_A9_seed" --mode mock --output runs/snu668_r2_K3_A9_mock_after_live_patch --fit --make-figures
```

## Test results

- New live extraction tests: passed, `3` tests.
- Full unittest suite: passed, `100` tests.
- Mock benchmark smoke run after live patch: succeeded.

## Current real-data command

Run this after the approved CLONEID credentials are available:

```bash
PYTHONPATH=src python3 -m cloneid_agent.cli run-rk-benchmark \
  --config configs/applications/snu668_density_history.yaml \
  --external-zip /Users/4482173/Documents/GitHub/cloneid_physicell_agent_codex/data/nwaa124_supplement_file \
  --cloneid-root-id "SNU-668_r2_A9_seed,SNU-668_K3_A9_seed" \
  --mode live \
  --output runs/snu668_r2_K3_A9_live \
  --fit \
  --make-figures
```

## Remaining blockers

- Current CLONEID credentials for user `agent` were rejected by the database.
- Real manuscript numerical results still require a successful live run or an approved frozen SNU-668 snapshot.
- Real NSR supplement path/archive must be accessible for final comparator interpretation; mock/fixture extraction remains workflow validation only.

## Claim boundary

- Mock outputs do not support biological numerical claims.
- Live extraction is read-only and uses `SELECT` queries through the installed `cloneid` R package.
- Endpoint Perspective remains validation/support only.
- Identity remains inferred secondary support only.
- Transfer/passaging events remain schedule resets, not growth intervals.
