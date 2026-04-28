# Phase Abstraction Design Memo

## Scope

- Anchor lineage object: `lineage_path::SUM159_NLS_4N_O2_A7K_harvest`
- Matched comparison branch: `lineage_path::SUM159_NLS_2N_O2_A7K_harvest`
- Technical smoke object remains separate: `rooted_trajectory_bundle::2586-4`

This memo defines design options for translating long-term CLONEID lineage paths into tractable PhysiCell model phases without simulating raw calendar time minute-by-minute.

## Current artifact facts

- Anchor event count: `23`
- Anchor graph depth / path length: `22 / 23`
- Anchor raw elapsed time: `1035.26` days
- Anchor current phase summary:
  - passage intervals: `22`
  - context regimes: `10`
  - normalized phase plan currently available: `22` phases x `1440` simulated minutes = `31680` simulated minutes
- Anchor phenotype support:
  - `Passaging.correctedCount`: `18` rows
  - `Passaging.cellCount`: `23` rows
  - `Passaging.areaOccupied_um2`: `18` rows
  - `Perspective.size`: `19` supporting rows
- Matched branch event count: `25`
- Matched branch raw elapsed time: `900.249` days
- Matched branch phenotype support:
  - `Passaging.correctedCount`: `24` rows
  - `Passaging.cellCount`: `25` rows
  - `Passaging.areaOccupied_um2`: `18` rows
- Current selected biological question:
  - compare matched SUM-159 ploidy / oxygen-state lineage paths to test whether state-specific history changes expansion behavior across repeated passages and harvest endpoints

## Design objective

The biological proof-of-principle branch should:

- preserve the explicit `Passaging.passaged_from_id1` lineage order,
- preserve event provenance,
- use CLONEID phenotype values as calibration and validation targets,
- use `Perspective.size` as endpoint molecular support,
- avoid treating long idle calendar intervals as literal PhysiCell wall-clock runtime,
- produce a manuscript-usable comparison between biologically meaningful matched lineage paths.

## Strategy 1: Primary-Lineage Interval Phases

### 1. What counts as a phase

Each adjacent primary-lineage interval becomes one phase:

- `Event_i -> Event_{i+1}` on the `passaged_from_id1` backbone

For the anchor, this yields one phase per lineage step, which is currently `22` phases.

### 2. How CLONEID Events map to PhysiCell

- first Event on the path: initial condition
- each subsequent Event: end of the current phase and start of the next
- passage or reseeding step: modeled as an explicit bottleneck / transfer event between phases
- harvest-labeled Event: endpoint / validation checkpoint
- `Perspective.origin` records linked to terminal Event: endpoint molecular constraint
- `Identity`: retained only as secondary inferred support

### 3. How real elapsed time maps to simulated time

- do not use raw elapsed time literally
- normalize every lineage interval to one fixed simulated duration
- current first-pass example: `1440` simulated minutes per interval
- record both:
  - real elapsed minutes between Events
  - assigned simulated minutes for that phase

### 4. Which CLONEID observables are used

- calibration / trajectory:
  - `Passaging.cellCount`
  - `Passaging.correctedCount`
  - `Passaging.areaOccupied_um2`
- endpoint validation:
  - `Perspective.size`
- secondary support only:
  - `Identity`

### 5. What the model families would mean under this abstraction

- `neutral_growth`:
  - all phases use the same growth rules; differences arise only from initialization, bottlenecks, and schedule
- `fixed_state_fitness`:
  - 2N and 4N branches have different fixed effective growth or death tendencies across phases
- `density-dependent/resource-sensitive growth`:
  - the same lineage schedule is used, but branch differences appear through crowding or resource-response rules during each phase

### 6. What model comparison would test

- 2N vs 4N differences under related O2-labeled lineage history
- whether repeated passage bottlenecks alone explain divergence
- whether fixed state-specific fitness is needed
- whether density/resource dependence improves the fit over neutral growth

### 7. Assumptions

- each backbone interval is a meaningful biological episode
- phase normalization does not erase the signal of interest
- passage transitions matter more than literal waiting time

### 8. What could go wrong

- some intervals may represent heterogeneous biology despite a single lineage edge
- equal simulated duration per phase may over-compress some regimes and under-compress others
- repeated passaging effects may be confounded with media or oxygen-history effects

### 9. Suitability for first manuscript figure

High. This is the safest first design because it aligns directly with the explicit lineage graph and requires the fewest extra interpretive decisions.

## Strategy 2: Seed-to-Harvest Episode Phases

### 1. What counts as a phase

A phase is a bounded seed-to-harvest or seed-to-next-transfer episode, potentially grouping several adjacent lineage Events if they are part of one experimental episode.

### 2. How CLONEID Events map to PhysiCell

- seed Event: phase initialization
- intermediate within-episode Events: internal calibration checkpoints
- harvest Event: phase endpoint
- passage / reseeding after harvest: hard transition to the next phase
- terminal `Perspective.origin`: endpoint validation

### 3. How real elapsed time maps to simulated time

- use compressed episode duration, not raw calendar duration
- one option: assign each seed-to-harvest episode a shared fixed runtime
- another option: scale phase duration to episode phenotype change magnitude rather than literal days

### 4. Which CLONEID observables are used

- within-episode trajectory:
  - `Passaging.cellCount`
  - `Passaging.correctedCount`
  - `Passaging.areaOccupied_um2`
- episode endpoint:
  - `Perspective.size`
- `Identity` only as secondary support

### 5. What the model families would mean under this abstraction

- `neutral_growth`:
  - each episode follows the same rules, only interrupted by reseeding / bottlenecks
- `fixed_state_fitness`:
  - each lineage branch carries stable state-specific episode performance
- `density-dependent/resource-sensitive growth`:
  - episode-level differences emerge from environment-sensitive response within each seeded culture episode

### 6. What model comparison would test

- whether branch differences are episode-stable
- whether divergence is concentrated within repeated seed-to-harvest experiments rather than across the full lineage
- whether bottleneck handling plus density/resource sensitivity is sufficient

### 7. Assumptions

- seed-to-harvest episodes are the correct biological unit
- grouped Events within an episode are comparable under one local model context

### 8. What could go wrong

- episode boundaries may be ambiguous for some intervals
- grouping may hide informative Event-to-Event variation
- this strategy requires more interpretive bundling than Strategy 1

### 9. Suitability for first manuscript figure

Moderate to high. Good backup strategy if interval-by-interval modeling proves too granular or too brittle.

## Strategy 3: Regime-Bounded Phases

### 1. What counts as a phase

A phase is defined by a stable local regime, such as:

- same media assignment
- same stressor or oxygen-labeled regime
- same local seeding / flask context when identifiable

### 2. How CLONEID Events map to PhysiCell

- first Event in a regime: initialize that regime phase
- Events within the same regime: trajectory checkpoints inside the phase
- regime switch: explicit event-schedule change
- terminal harvest with `Perspective.origin`: validation endpoint

### 3. How real elapsed time maps to simulated time

- assign one normalized duration per regime phase
- optionally let duration scale with the number of backbone intervals contained in that regime
- still avoid literal raw-time simulation

### 4. Which CLONEID observables are used

- trajectory:
  - `Passaging.cellCount`
  - `Passaging.correctedCount`
  - `Passaging.areaOccupied_um2`
- regime endpoint:
  - `Perspective.size`
- `Identity` only as secondary support

### 5. What the model families would mean under this abstraction

- `neutral_growth`:
  - all regimes share one biological program despite context changes
- `fixed_state_fitness`:
  - branch-specific intrinsic differences persist across regimes
- `density-dependent/resource-sensitive growth`:
  - regime changes directly modulate effective dynamics

### 6. What model comparison would test

- oxygen-regime adaptation
- media/regime dependence versus stable intrinsic branch differences
- whether branch divergence is explained more by context shifts than by fixed lineage state

### 7. Assumptions

- regime annotations capture the dominant selective context
- grouping by regime does not collapse too much lineage detail

### 8. What could go wrong

- local regime labels may be incomplete or not sufficient to define true biological episodes
- this strategy is more interpretation-heavy than Strategy 1
- it risks turning context labels into stronger mechanistic claims than the current evidence supports

### 9. Suitability for first manuscript figure

Moderate. Useful if the paper wants to foreground oxygen/regime adaptation, but less conservative than Strategy 1.

## Comparison summary

| Strategy | Phase unit | Simulated time mapping | Best tests | Main risk | Manuscript safety |
|---|---|---|---|---|---|
| Primary-lineage interval phases | one `passaged_from_id1` interval | fixed duration per lineage interval | 2N vs 4N branch divergence, bottlenecks, density/resource effects | over-normalizing unequal biology | highest |
| Seed-to-harvest episode phases | one experimental episode | fixed or compressed episode duration | episode-stable branch behavior | boundary ambiguity | medium-high |
| Regime-bounded phases | one stable media/stressor regime | fixed duration per regime | oxygen/regime adaptation | interpretation-heavy grouping | medium |

## Recommended default strategy

Use **Strategy 1: Primary-Lineage Interval Phases**.

Why:

- it is closest to the explicit CLONEID lineage graph,
- it preserves provenance cleanly,
- it requires the fewest extra biological assumptions,
- it supports matched-path comparison between the selected 4N/O2 anchor and the 2N/O2 branch,
- it separates the technical issue of long calendar time from the biological question of branch-specific growth behavior.

## Backup strategy

Use **Strategy 2: Seed-to-Harvest Episode Phases** if interval-level phases are too fine-grained for the first manuscript figure or if episode boundaries are already clear in the lineage records.

## Open questions for the user

1. For the first biological proof-of-principle figure, should the comparison prioritize:
   - 4N/O2 vs 2N/O2,
   - 4N/O2 vs 4N/O1,
   - or a three-branch comparison?
2. Should the first manuscript figure emphasize:
   - intrinsic 2N vs 4N differences,
   - oxygen/regime adaptation,
   - or both in a matched-path design?
3. For the first implementation, should phase duration stay:
   - fixed per lineage interval,
   - fixed per seed-to-harvest episode,
   - or be scaled by phenotype change magnitude?
4. Should the first biological proof-of-principle use:
   - only `cellCount`,
   - `cellCount` plus `correctedCount`,
   - or `cellCount` plus `correctedCount` plus `areaOccupied_um2` as joint calibration targets?
