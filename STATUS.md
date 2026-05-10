# Status checkpoint

This file is maintained by the agent. It records the current reviewable state of the repository.

## Current state

- Current branch: `update_5.5`
- Last committed baseline before this pass: `3c539dd`
- Current work unit: replace the previous quick-check PhysiCell validation path with direct runtime execution against the configured local PhysiCell install.
- Current work state: completed and tested.
- Approved roots:
  - `SNU-668_r2_A9_seed` for r cells
  - `SNU-668_K3_A9_seed` for K cells

## What changed in this pass

- Added a PhysiCell integration stage:
  - `src/cloneid_agent/rk_physicell_integration.py`
  - optional CLI flags `--run-physicell`, `--physicell-root`, `--execute-physicell`, and `--physicell-runtime-max-time`
  - output directory `physicell/`
  - candidate input packages for `snu668_full_history`, `snu668_published_like_compressed`, and `nwaa124_curated_external`
  - model-family encoding comparison for `neutral_growth`, `fixed_state_fitness`, and `density_dependent_growth`
  - required-data report for PhysiCell analysis.
- Removed obsolete quick-check runtime validation code and references:
  - deleted the old schedule-aware validation helper module
  - deleted the old validation helper test
  - deleted the old standalone validation shell script
  - deleted obsolete derived validation docs
  - renamed remaining model-candidate/runtime helper language to direct runtime terminology.
- Configured the real local PhysiCell install in `configs/applications/snu668_density_history.yaml`:
  - root: `/Users/4482173/Documents/PhysiCell`
  - executable: `/Users/4482173/Documents/PhysiCell/heterogeneity`
  - source config: `/Users/4482173/Documents/PhysiCell/sample_projects/heterogeneity/config/PhysiCell_settings.xml`
- Updated generated PhysiCell XML to use the matching heterogeneity source config and runtime parameters required by that executable, including `tumor_radius` and oncoprotein parameters.
- Added `figures/physicell_model_input_comparison.png` when `--make-figures --run-physicell` are used.
- Updated `model_selection_report.md`, `manuscript_facing_summary.md`, `MANUSCRIPT_INSERT.md`, README, and application docs to explain the PhysiCell layer and its guardrails.
- Confirmed local PhysiCell root discovery at `/Users/4482173/Documents/PhysiCell`.
- Ran a mock full workflow with real local NSR zip from `/Users/4482173/Downloads/nwaa124_supplement_file.zip` and direct PhysiCell execution.

## Previous required-data work retained

- Added `required_data_by_question.md` to the benchmark report outputs.
- Added question-specific required-data sections to `model_selection_report.md` and `manuscript_facing_summary.md`.
- Strengthened the manuscript language that NSR directly compares r and K populations at publication level, while CLONEID adds event-linked fields that make event-history questions automatically queryable and auditable.
- Framed CLONEID-LTEE as a low-cost, gold-standard-style minimum record for long-term evolutionary experiments.
- Updated `docs/standards/minimum_longitudinal_evolution_record.md` with a question-specific minimum-data table.

## Previous live-extraction work retained

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
PYTHONPATH=src:tests python3 -m unittest tests/test_rk_benchmark_cli.py tests/test_pipeline_run.py
PYTHONPATH=src python3 -m cloneid_agent.cli run-rk-benchmark --config configs/applications/snu668_density_history.yaml --cloneid-root-id "SNU-668_r2_A9_seed,SNU-668_K3_A9_seed" --mode mock --output runs/snu668_question_required_data_mock --fit --make-figures
PYTHONPATH=src:tests python3 -m unittest discover -s tests
PYTHONPATH=src python3 -m compileall src/cloneid_agent
PYTHONPATH=src:tests python3 -m unittest tests/test_rk_physicell_integration.py tests/test_rk_benchmark_cli.py
PYTHONPATH=src python3 -m cloneid_agent.cli run-rk-benchmark --config configs/applications/snu668_density_history.yaml --external-zip /Users/4482173/Downloads/nwaa124_supplement_file.zip --cloneid-root-id SNU-668_r2_A9_seed,SNU-668_K3_A9_seed --mode mock --output runs/snu668_rk_physicell_mock --fit --make-figures --run-physicell --physicell-root /Users/4482173/Documents/PhysiCell
PYTHONPATH=src:tests python3 -m unittest tests.test_rk_physicell_integration
PYTHONPATH=src python3 -m compileall src/cloneid_agent
rg -n "<obsolete quick-check validation term>" .
PYTHONPATH=src python3 -m cloneid_agent.cli run-rk-benchmark --config configs/applications/snu668_density_history.yaml --external-zip /Users/4482173/Downloads/nwaa124_supplement_file.zip --cloneid-root-id SNU-668_r2_A9_seed,SNU-668_K3_A9_seed --mode mock --output runs/snu668_rk_physicell_runtime_mock --fit --make-figures --run-physicell --physicell-root /Users/4482173/Documents/PhysiCell --execute-physicell --physicell-runtime-max-time 1
PYTHONPATH=src:tests python3 -m unittest discover -s tests
```

## Test results

- New live extraction tests: passed, `3` tests.
- Full unittest suite: passed, `102` tests.
- Question-specific report tests: passed.
- Mock benchmark workflow run after required-data patch: succeeded.
- PhysiCell integration tests: passed, `3` targeted tests for the new module.
- Obsolete validation-code scan returned no matches.
- PhysiCell direct runtime workflow run: succeeded, output at `runs/snu668_rk_physicell_runtime_mock`.
- PhysiCell execution report: all three full-history candidate families returned code `0`:
  - `snu668_full_history__neutral_growth`
  - `snu668_full_history__fixed_state_fitness`
  - `snu668_full_history__density_dependent_growth`

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
  --make-figures \
  --run-physicell \
  --physicell-root /Users/4482173/Documents/PhysiCell \
  --execute-physicell
```

## Remaining blockers

- Current CLONEID credentials for user `agent` were rejected by the database.
- Real manuscript numerical results still require a successful live run or an approved frozen SNU-668 snapshot.
- Real NSR supplement path/archive must be accessible for final comparator interpretation. `/Users/4482173/Downloads/nwaa124_supplement_file.zip` was accessible in this runtime and used for the direct PhysiCell workflow validation; the originally requested repo data directory was not present in this checkout.
- PhysiCell runtime execution can now be requested directly with `--execute-physicell`; direct runtime execution succeeded against `/Users/4482173/Documents/PhysiCell/heterogeneity`. Biological simulation interpretation still requires calibrated custom PhysiCell rules plus live or frozen SNU-668 data.

## Claim boundary

- Mock outputs do not support biological numerical claims.
- Live extraction is read-only and uses `SELECT` queries through the installed `cloneid` R package.
- Endpoint Perspective remains validation/support only.
- Identity remains inferred secondary support only.
- Transfer/passaging events remain schedule resets, not growth intervals.
