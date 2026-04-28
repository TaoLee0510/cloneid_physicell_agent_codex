# Schedule-Aware Model Family Specification

- Comparison: `SUM159_4N_O2_vs_SUM159_2N_O2`
- Anchor branch: `SUM159_4N_O2`
- Comparison branch: `SUM159_2N_O2`
- Matched growth episodes: `8`
- No fitted parameter values yet: `True`

## neutral_growth

- Meaning: Same growth rule for 2N and 4N branches; differences arise only from observed initial conditions and transfer bottlenecks.
- Primary calibration target: `Passaging.cellCount`
- Secondary validation targets: `Passaging.correctedCount, Passaging.areaOccupied_um2, Perspective.size`
- Transfer events: Apply observed transfer_events as external bottleneck/reseeding updates between growth episodes; do not simulate transfer as growth time.
- Growth episodes: Simulate each growth_episode for fixed 1440 minutes, using observed start counts / area as initialization and observed end values as calibration targets.
- Terminal Perspective.size: Use terminal Perspective.size only as endpoint support / validation, not as a growth-episode calibration signal.

### Exposed parameters

- `shared_proliferation_rate` (shared, placeholder)
- `shared_death_rate` (shared, placeholder)
- `shared_initial_cell_area` (shared, placeholder)

- Win condition: One shared growth program explains both 2N and 4N seed-to-harvest trajectories after applying observed transfer bottlenecks.
- Failure condition: Systematic branch-specific trajectory mismatch remains after shared-parameter fitting, especially if 2N and 4N diverge in consistent opposite directions.

## fixed_state_fitness

- Meaning: 2N and 4N branches may require different intrinsic proliferation / death balance under otherwise matched O2 schedule structure.
- Primary calibration target: `Passaging.correctedCount`
- Secondary validation targets: `Passaging.cellCount, Passaging.areaOccupied_um2, Perspective.size`
- Transfer events: Same as neutral_growth: apply observed transfer_events as non-growth bottleneck/reseeding resets between growth episodes.
- Growth episodes: Simulate fixed 1440-minute growth episodes, but allow 2N and 4N branches to use different intrinsic fitness parameters across the whole matched window.
- Terminal Perspective.size: Use terminal Perspective.size as endpoint support to judge whether branch-specific fitness differences remain biologically consistent at harvest.

### Exposed parameters

- `proliferation_rate_2N` (branch_specific, `2N`, placeholder)
- `proliferation_rate_4N` (branch_specific, `4N`, placeholder)
- `death_rate_2N` (branch_specific, `2N`, placeholder)
- `death_rate_4N` (branch_specific, `4N`, placeholder)
- `shared_initial_cell_area` (shared, placeholder)

- Win condition: Branch-specific intrinsic parameters materially improve joint fit across matched episodes relative to neutral_growth.
- Failure condition: Branch-specific parameters do not improve fit enough to justify extra degrees of freedom.

## density_dependent_growth

- Meaning: Growth depends on density / confluence proxy, with areaOccupied_um2 used as the preferred schedule-aware crowding signal.
- Primary calibration target: `Passaging.areaOccupied_um2`
- Secondary validation targets: `Passaging.cellCount, Passaging.correctedCount, Perspective.size`
- Transfer events: Apply observed transfer_events as explicit reductions / resets in seeded cell burden and occupancy before the next growth episode.
- Growth episodes: Simulate each 1440-minute growth episode with density-sensitive growth, comparing whether occupied area better explains the seed-to-harvest trajectory than fixed-rate growth.
- Terminal Perspective.size: Use terminal Perspective.size only as endpoint support, not as the driver of the density response.

### Exposed parameters

- `shared_density_response_threshold` (shared, placeholder)
- `shared_density_response_slope` (shared, placeholder)
- `shared_baseline_proliferation_rate` (shared, placeholder)
- `optional_branch_specific_density_thresholds` (optional_branch_specific, placeholder)

- Win condition: Density-sensitive growth explains both cell-count and area trajectories better than fixed-rate models across the matched episodes.
- Failure condition: Adding density dependence does not improve the joint count/area fit or only explains one branch.

## Candidate Differentiation Checklist

- `cell phenotype proliferation / death rules`
  - neutral_growth: shared parameters across 2N and 4N
  - fixed_state_fitness: branch-specific proliferation / death balance
  - density_dependent_growth: density-responsive proliferation with optional branch-specific thresholds
- `crowding / density response rule`
  - neutral_growth: not required beyond baseline PhysiCell defaults
  - fixed_state_fitness: not primary driver
  - density_dependent_growth: must be explicitly enabled and parameterized
- `episode initialization inputs`
  - neutral_growth: schedule initial_condition and transfer resets
  - fixed_state_fitness: same schedule inputs plus branch label
  - density_dependent_growth: same schedule inputs plus occupancy-sensitive initialization use
- `transfer-event handling`
  - neutral_growth: external bottleneck / reseeding update
  - fixed_state_fitness: same external transfer update
  - density_dependent_growth: same external transfer update with occupancy reset preserved
- `primary calibration observable`
  - neutral_growth: Passaging.cellCount
  - fixed_state_fitness: Passaging.correctedCount
  - density_dependent_growth: Passaging.areaOccupied_um2
