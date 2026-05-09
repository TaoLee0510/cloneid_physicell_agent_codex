# Status checkpoint

This file is maintained by the agent. It records the current reviewable state of the repository.

## Current state

- Current branch: `update_5.5`
- Last committed baseline before this cleanup pass: `6703b56`
- Current work unit: manuscript-facing cleanup for the SNU-668 density-history proof-of-principle.
- Current work state: completed and tested.
- Generated output directory: `runs/update_5_5`

## What changed in this pass

- Repositioned the repository homepage around the SNU-668 density-history proof-of-principle rather than a generic r/K benchmark.
- Made the manuscript-facing config/docs use canonical regime names:
  - `snu668_full_history`
  - `snu668_published_like_compressed`
  - `nwaa124_curated_external`
- Foregrounded the three paper-facing model families:
  - `neutral_growth`
  - `fixed_state_fitness`
  - `density_dependent_growth`
- Preserved the `update_5.5` engineering for:
  - NSR nwaa124 archive/docx extraction
  - `run-rk-benchmark`
  - CLONEID full versus downsampled records
  - modelability/observability/family comparison reports
  - CLONEID-LTE standards and figures
- Added paper-facing artifact aliases for:
  - `manuscript_facing_summary.md`
  - `family_discrimination_summary.md`
  - `observability_matrix.json`
  - `observability_matrix.csv`
  - `dataset_missingness.md`
  - `history_covariates.json`
  - `history_covariates.md`
  - `history_ablation.json`
  - `history_ablation.md`
  - `minimum_longitudinal_evolution_record.md`
  - `figure_data/`
- Refined `docs/standards/minimum_longitudinal_evolution_record.md` as the low-cost record-standard asset.
- Updated tests to assert the canonical regime names and new manuscript-facing artifacts.

## Benchmark-oriented code retained intentionally

- The lower-level `run-rk-benchmark` command remains available and compatible.
- Extended internal fit families remain in the modeling JSON for compatibility:
  - `context_blind_null`
  - `proliferation_only`
  - `branch_specific_fitness`
  - `density_plus_branch_optional`
- Paper-facing reports map those extended families onto `neutral_growth`, `fixed_state_fitness`, and `density_dependent_growth`.

## External supplement availability

- Checked preferred path:
  - `/Users/4482173/Documents/GitHub/cloneid_physicell_agent_codex/data/nwaa124_supplement_file`
- Checked mounted zip:
  - `/mnt/data/nwaa124_supplement_file.zip`
- Result in this runtime: neither path was accessible.
- Dry-run/mock mode therefore used the deterministic minimal NSR extraction fixture.
- Manuscript comparator interpretation still requires the real NSR supplement archive or directory.

## Live CLONEID availability

- Live SNU-668 CLONEID extraction was not attempted in this pass.
- Current run used deterministic mock/schema fixture values.
- Manuscript numerical interpretation requires either:
  - live read-only CLONEID extraction, or
  - an approved frozen SNU-668 snapshot.

## Claims not yet biologically supported

- The mock run does not support biological numerical claims about SNU-668.
- The mock run does not establish causality or a final mechanism.
- HeLa and SNU-668 are not treated as biologically equivalent.
- Endpoint Perspective remains validation/support only.
- Identity remains inferred secondary support only.
- Transfer/passaging events remain schedule resets, not growth intervals.

## Commands run

Startup and required inspection:

```bash
git branch --show-current
git status --short
ls
sed -n '1,220p' README.md
sed -n '1,220p' CODEX_INSTRUCTIONS.md
sed -n '1,220p' DATABASE_ACCESS.md
sed -n '1,220p' AGENT_WORKFLOW.md
sed -n '1,220p' RUNTIME_AND_HPC.md
sed -n '1,220p' GIT_WORKFLOW.md
sed -n '1,220p' SUPERVISED_AUTONOMY.md
sed -n '1,260p' STATUS.md
sed -n '1,260p' WORK_QUEUE.md
sed -n '1,260p' QUESTION_QUEUE.md
sed -n '1,260p' docs/CLONEID_SCHEMA_NOTES.md
git show update_5.4:README.md
git show update_5.4:configs/applications/snu668_density_history.yaml
git show update_5.4:docs/applications/snu668_density_history.md
```

Supplement-path checks:

```bash
test -d /Users/4482173/Documents/GitHub/cloneid_physicell_agent_codex/data/nwaa124_supplement_file
test -f /mnt/data/nwaa124_supplement_file.zip
find data -maxdepth 3 -iname '*nwaa124*' -o -iname '*supplement*'
find /Users/4482173/Documents/GitHub/cloneid_physicell_update_5_5 -maxdepth 4 -iname '*nwaa124*' -o -iname '*supplement*'
```

Validation:

```bash
PYTHONPATH=src:tests python3 -m unittest tests/test_rk_benchmark_cli.py tests/test_pipeline_run.py tests/test_observability_profile.py tests/test_history_ablation.py tests/test_comparative_identifiability.py
PYTHONPATH=src python3 -m cloneid_agent run --config configs/applications/snu668_density_history.yaml --output runs/update_5_5 --mode dry-run --fit --make-figures
PYTHONPATH=src:tests python3 -m unittest discover -s tests
```

## Test results

- Focused CLI/report tests: passed, `8` tests.
- Full unittest suite: passed, `97` tests.
- `pytest` was not run because the repository validation contract for this pass was `PYTHONPATH=src:tests python3 -m unittest discover -s tests`.

## Most useful generated artifacts

- `runs/update_5_5/model_selection_report.md`
- `runs/update_5_5/manuscript_facing_summary.md`
- `runs/update_5_5/family_discrimination_summary.md`
- `runs/update_5_5/modeling/comparative_identifiability_report.md`
- `runs/update_5_5/modeling/rejection_report.md`
- `runs/update_5_5/modeling/observability_matrix.csv`
- `runs/update_5_5/modeling/family_comparison.csv`
- `runs/update_5_5/minimum_longitudinal_evolution_record.md`
- `runs/update_5_5/MANUSCRIPT_INSERT.md`

## Stop checklist

- Completed: deterministic manuscript-facing cleanup, artifact generation, and tests.
- Safe next task: replace mock SNU-668 fixture with live read-only extraction or an approved frozen snapshot.
- Why not continuing into live extraction now: the exact source and root/subtree target remain unresolved user decisions.
