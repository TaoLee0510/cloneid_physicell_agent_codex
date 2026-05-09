# Work Queue

This file is maintained by the agent. It should make unattended progress visible and reviewable.

## Ready now

1. Rerun the live SNU-668 A9 benchmark after read-only CLONEID credentials are accepted.
   - Command target: `runs/snu668_r2_K3_A9_live`
   - Roots:
     - `SNU-668_r2_A9_seed`
     - `SNU-668_K3_A9_seed`
   - Current blocker: database rejected user `agent` from this environment.

2. Restore real NSR supplement extraction in an environment where the archive or directory is mounted.
   - Preferred source: `/Users/4482173/Documents/GitHub/cloneid_physicell_agent_codex/data/nwaa124_supplement_file`
   - Fallback source: `/mnt/data/nwaa124_supplement_file.zip`
   - Mock/fixture extraction remains workflow validation only.

3. Strengthen model fitting after live/snapshot data are available.
   - Add deterministic train/test split or leave-one-episode-out cross-validation.
   - Keep reports structured as supported, rejected under tested assumptions, or unresolved under available records.
   - Keep required inputs available/missing separate from numeric fit metrics.

4. Optional PhysiCell candidate mapping after the modelability benchmark is stable.
   - Use `modeling/family_comparison.json` and `modeling/comparative_identifiability_report.json` to decide which families deserve executable candidates.
   - Preserve transfer/passaging events as schedule resets rather than growth intervals.

## In progress

None.

## Waiting for user

1. Provide working read-only CLONEID credentials/access for the configured `cloneid::connect2DB()` user, or run the live command in an environment where that user is authorized.
2. Provide or remount the real NSR nwaa124 supplement path/archive for final comparator outputs.
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
8. Verified the new code with unit tests and a mock benchmark smoke run.
