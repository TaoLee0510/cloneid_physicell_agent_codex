# Candidate Differentiation Report

- Candidate root: `runs/live_lineage_objects_20260427T042000/model_candidates_schedule_aware`
- Runnable: `True`
- Model comparison still not yet fitted: `True`
- Perspective.size used for fitting: `False`

## Parameters by family

- `neutral_growth`: `shared_death_rate, shared_initial_cell_area, shared_proliferation_rate`
- `fixed_state_fitness`: `death_rate_2N, death_rate_4N, proliferation_rate_2N, proliferation_rate_4N, shared_initial_cell_area`
- `density_dependent_growth`: `area_proxy_mode, density_response_slope, density_response_threshold, shared_baseline_proliferation_rate, shared_death_rate`

## File differences

- `config/PhysiCell_settings.xml` differs across candidates: `True`
- `candidate_manifest.json` differs across candidates: `True`
- `README.md` differs across candidates: `True`
- `schedule_mapping.json` differs across candidates: `False`
- `evaluation_plan.json` differs across candidates: `True`
- `parameter_placeholders.json` differs across candidates: `True`

## Rules by family

- `neutral_growth`
  - Use identical proliferation/death rule structure for 2N and 4N branches.
  - Apply observed transfer-event bottlenecks externally between episodes.
- `fixed_state_fitness`
  - Use branch-specific proliferation/death placeholders for 2N and 4N.
  - Do not introduce density dependence as the main mechanism.
  - Apply observed transfer-event bottlenecks externally between episodes.
- `density_dependent_growth`
  - Use density/confluence-linked growth modulation informed by areaOccupied_um2.
  - Avoid branch-specific density parameters initially.
  - Apply observed transfer-event bottlenecks externally between episodes.

## Shared evaluation objective

- Primary: `Passaging.cellCount.seed_to_harvest_fold_change, Passaging.correctedCount.seed_to_harvest_fold_change`
- Secondary: `Passaging.areaOccupied_um2.episode_end_value, Passaging.areaOccupied_um2.seed_to_harvest_fold_change`
- Endpoint validation only: `Perspective.size`

## Remaining before biological interpretation

- Implement family-specific XML/config/rules execution semantics beyond placeholders.
- Add parameter search or fitting on the shared objective vector.
- Run the candidates and compute matched-episode residuals.
- Verify that terminal Perspective.size remains validation-only.
