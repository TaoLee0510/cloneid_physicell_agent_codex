# Work Queue

This file is maintained by the agent. It should make unattended progress visible and reviewable.

## Ready now

1. Replace the deterministic mock SNU-668 fixture with live read-only CLONEID extraction or an approved frozen SNU-668 snapshot.
   - Required user input: approved data source and exact SNU-668 root/subtree target.
   - Preserve the same output contract under `cloneid_full/`, `cloneid_downsampled/`, and `modeling/`.

2. Strengthen model fitting after live/snapshot data are available.
   - Add deterministic train/test split or leave-one-episode-out cross-validation.
   - Keep reports structured as supported, rejected under tested assumptions, or unresolved under available records.
   - Keep required inputs available/missing separate from numeric fit metrics.

3. Restore real NSR supplement extraction in an environment where the archive or directory is mounted.
   - Preferred source: `/Users/4482173/Documents/GitHub/cloneid_physicell_agent_codex/data/nwaa124_supplement_file`
   - Fallback source: `/mnt/data/nwaa124_supplement_file.zip`
   - Current runtime only had access to the deterministic minimal fixture.

4. Optional PhysiCell candidate mapping after the modelability benchmark is stable.
   - Use `modeling/family_comparison.json` and `modeling/comparative_identifiability_report.json` to decide whether executable candidates are warranted.
   - Preserve transfer/passaging events as schedule resets rather than growth intervals.

## In progress

None.

## Waiting for user

1. Decide whether manuscript numerical results should use live read-only CLONEID extraction or an approved frozen SNU-668 snapshot.
2. Provide the exact SNU-668 root ID or subtree target for live extraction.
3. Provide or remount the real NSR nwaa124 supplement path/archive if the manuscript comparator run should use real files in this environment.
4. Decide whether the curated NSR CSV fallback should remain as a validation artifact after automatic docx extraction is stable.

## Done in this pass

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
7. Generated `runs/update_5_5/`.
8. Passed `PYTHONPATH=src:tests python3 -m unittest discover -s tests`.
