# Work Queue

This file is maintained by the agent. It should make unattended progress visible and reviewable.

## Ready now

1. Rerun the live SNU-668 A9 benchmark after read-only CLONEID credentials are accepted.
   - Command target: `runs/snu668_r2_K3_A9_live`
   - Roots:
     - `SNU-668_r2_A9_seed`
     - `SNU-668_K3_A9_seed`
   - Current blocker: database rejected user `agent` from this environment.

2. Restore or standardize the manuscript NSR supplement source path for final runs.
   - Preferred source from the original task: `/Users/4482173/Documents/GitHub/cloneid_physicell_agent_codex/data/nwaa124_supplement_file`
   - Accessible source in this runtime: `/Users/4482173/Downloads/nwaa124_supplement_file.zip`
   - Mock/fixture extraction remains workflow validation only.

3. Strengthen model fitting after live/snapshot data are available.
   - Add deterministic train/test split or leave-one-episode-out cross-validation.
   - Keep reports structured as supported, rejected under tested assumptions, or unresolved under available records.
   - Keep required inputs available/missing separate from numeric fit metrics.

4. Calibrate real PhysiCell simulations after live/snapshot data are available.
   - Current workflow writes PhysiCell-ready input packages and directly executes generated full-history PhysiCell configs against `/Users/4482173/Documents/PhysiCell/heterogeneity`.
   - Next step is custom PhysiCell rule implementation for `neutral_growth`, `fixed_state_fitness`, and `density_dependent_growth` so runtime outputs encode the manuscript model-family differences rather than only executable candidate surfaces.
   - Preserve transfer/passaging events as schedule resets rather than growth intervals.
   - Compare simulated episode-end counts/area proxies against live CLONEID growth episodes; use NSR as summary-prior/external observability support, not as a biological head-to-head.

## In progress

None.

## Waiting for user

1. Provide working read-only CLONEID credentials/access for the configured `cloneid::connect2DB()` user, or run the live command in an environment where that user is authorized.
2. Decide whether final runs should use the accessible zip at `/Users/4482173/Downloads/nwaa124_supplement_file.zip` or remount the original requested data directory.
3. Decide whether the curated NSR CSV fallback should remain as a validation artifact after automatic docx extraction is stable.

## Done

1. Reframed the repo top level around the SNU-668 density-history proof-of-principle.
2. Replaced benchmark-oriented public names in config/docs/reports with:
   - `snu668_full_history`
   - `snu668_published_like_compressed`
   - `nwaa124_curated_external`
3. Foregrounded the manuscript-facing model families:
   - `neutral_growth`
   - `fixed_state_fitness`
   - `density_dependent_growth`
4. Kept `run-rk-benchmark` working while documenting `python3 -m cloneid_agent run --config ...` as the manuscript command.
5. Added root-level manuscript artifact aliases and `figure_data/`.
6. Updated the minimum longitudinal evolution record standard.
7. Added live read-only SNU-668 A9 r/K extraction for:
   - `SNU-668_r2_A9_seed`
   - `SNU-668_K3_A9_seed`
8. Verified the new code with unit tests and a mock benchmark workflow run.
9. Added the PhysiCell-facing stage to the main benchmark workflow:
   - `physicell/physicell_input_manifest.json`
   - `physicell/model_family_physicell_comparison.csv`
   - `physicell/physicell_summary.md`
   - `physicell/required_data_for_physicell.md`
   - `figures/physicell_model_input_comparison.png`
10. Removed obsolete quick-check validation code and verified the repo no longer uses that validation path.
11. Configured the real local PhysiCell path in `configs/applications/snu668_density_history.yaml`.
12. Directly executed generated full-history PhysiCell candidate configs; all three manuscript-facing families returned code `0` in `runs/snu668_rk_physicell_runtime_mock/physicell/physicell_execution_report.json`.
