# Matched Phase Plan

- Comparison: `SUM159_4N_O2_vs_SUM159_2N_O2`
- Anchor branch: `lineage_path::SUM159_NLS_4N_O2_A7K_harvest`
- Comparison branch: `lineage_path::SUM159_NLS_2N_O2_A7K_harvest`
- Matched phases: `22`
- Unmatched anchor phases: `0`
- Unmatched comparison phases: `2`

## Validation

- `simulated_duration_fixed_at_1440_minutes`: `True`
- `real_elapsed_time_not_used_as_runtime`: `True`
- `total_simulated_duration_within_guardrail`: `True`

## Matched phases

- phase `1`: anchor `SUM-159_4N_NLS_mCherry -> SUM-159_NLS_4N_A1_seed` vs comparison `SUM-159_NLS_mCherry -> SUM-159_NLS_2N_A3_seed`
- phase `2`: anchor `SUM-159_NLS_4N_A1_seed -> SUM-159_NLS_4N_A1_seedT2` vs comparison `SUM-159_NLS_2N_A3_seed -> SUM-159_NLS_2N_A3_harvest_T3`
- phase `3`: anchor `SUM-159_NLS_4N_A1_seedT2 -> SUM-159_NLS_4N_A2_seed` vs comparison `SUM-159_NLS_2N_A3_harvest_T3 -> SUM-159_NLS_2N_A4_seed`
- phase `4`: anchor `SUM-159_NLS_4N_A2_seed -> SUM-159_NLS_4N_A2_seedT4` vs comparison `SUM-159_NLS_2N_A4_seed -> SUM-159_NLS_2N_A4_harvest_T1`
- phase `5`: anchor `SUM-159_NLS_4N_A2_seedT4 -> SUM-159_NLS_4N_dp_seed` vs comparison `SUM-159_NLS_2N_A4_harvest_T1 -> SUM-159_NLS_2N_A5_seed`
- phase `6`: anchor `SUM-159_NLS_4N_dp_seed -> SUM-159_NLS_4N_dp_seedT1` vs comparison `SUM-159_NLS_2N_A5_seed -> SUM-159_NLS_2N_A5_harvest_T3`
- phase `7`: anchor `SUM-159_NLS_4N_dp_seedT1 -> SUM-159_NLS_4N_O2_A1_seed` vs comparison `SUM-159_NLS_2N_A5_harvest_T3 -> SUM-159_NLS_2N_dp_seed`
- phase `8`: anchor `SUM-159_NLS_4N_O2_A1_seed -> SUM-159_NLS_4N_O2_A1_seedT1` vs comparison `SUM-159_NLS_2N_dp_seed -> SUM-159_NLS_2N_dp_seedT1`
- phase `9`: anchor `SUM-159_NLS_4N_O2_A1_seedT1 -> SUM-159_NLS_4N_O2_A2_seed` vs comparison `SUM-159_NLS_2N_dp_seedT1 -> SUM-159_NLS_2N_O2_A1_seed`
- phase `10`: anchor `SUM-159_NLS_4N_O2_A2_seed -> SUM-159_NLS_4N_O2_A2_seedT2` vs comparison `SUM-159_NLS_2N_O2_A1_seed -> SUM-159_NLS_2N_O2_A1_seedT1`
- phase `11`: anchor `SUM-159_NLS_4N_O2_A2_seedT2 -> SUM-159_NLS_4N_O2_A3_seed` vs comparison `SUM-159_NLS_2N_O2_A1_seedT1 -> SUM-159_NLS_2N_O2_A2_seed`
- phase `12`: anchor `SUM-159_NLS_4N_O2_A3_seed -> SUM-159_NLS_4N_O2_A3_seedT2` vs comparison `SUM-159_NLS_2N_O2_A2_seed -> SUM-159_NLS_2N_O2_A2_seedT2`
- phase `13`: anchor `SUM-159_NLS_4N_O2_A3_seedT2 -> SUM-159_NLS_4N_O2_A4_seed` vs comparison `SUM-159_NLS_2N_O2_A2_seedT2 -> SUM-159_NLS_2N_O2_A3_seed`
- phase `14`: anchor `SUM-159_NLS_4N_O2_A4_seed -> SUM-159_NLS_4N_O2_A4_seedT2` vs comparison `SUM-159_NLS_2N_O2_A3_seed -> SUM-159_NLS_2N_O2_A3_seedT2`
- phase `15`: anchor `SUM-159_NLS_4N_O2_A4_seedT2 -> SUM-159_NLS_4N_O2_A5_seed` vs comparison `SUM-159_NLS_2N_O2_A3_seedT2 -> SUM-159_NLS_2N_O2_A4_seed`
- phase `16`: anchor `SUM-159_NLS_4N_O2_A5_seed -> SUM-159_NLS_4N_O2_A5_seedT2` vs comparison `SUM-159_NLS_2N_O2_A4_seed -> SUM-159_NLS_2N_O2_A4_seedT2`
- phase `17`: anchor `SUM-159_NLS_4N_O2_A5_seedT2 -> SUM-159_NLS_4N_O2_A6_seed` vs comparison `SUM-159_NLS_2N_O2_A4_seedT2 -> SUM-159_NLS_2N_O2_A5_seed`
- phase `18`: anchor `SUM-159_NLS_4N_O2_A6_seed -> SUM-159_NLS_4N_O2_A6_seedT2` vs comparison `SUM-159_NLS_2N_O2_A5_seed -> SUM-159_NLS_2N_O2_A5_seedT2`
- phase `19`: anchor `SUM-159_NLS_4N_O2_A6_seedT2 -> SUM-159_NLS_4N_O2_A7_seed` vs comparison `SUM-159_NLS_2N_O2_A5_seedT2 -> SUM-159_NLS_2N_O2_A6_seed`
- phase `20`: anchor `SUM-159_NLS_4N_O2_A7_seed -> SUM-159_NLS_4N_O2_A7_seedT2` vs comparison `SUM-159_NLS_2N_O2_A6_seed -> SUM-159_NLS_2N_O2_A6_seedT2`
- phase `21`: anchor `SUM-159_NLS_4N_O2_A7_seedT2 -> SUM-159_NLS_4N_O2_A7K_seed` vs comparison `SUM-159_NLS_2N_O2_A6_seedT2 -> SUM-159_NLS_2N_O2_A7_seed`
- phase `22`: anchor `SUM-159_NLS_4N_O2_A7K_seed -> SUM159_NLS_4N_O2_A7K_harvest` vs comparison `SUM-159_NLS_2N_O2_A7_seed -> SUM-159_NLS_2N_O2_A7_seedT2`

## Unmatched comparison phases

- `SUM159_2N_O2::phase_023` `SUM-159_NLS_2N_O2_A7_seedT2 -> SUM-159_NLS_2N_O2_A7K_seed`
- `SUM159_2N_O2::phase_024` `SUM-159_NLS_2N_O2_A7K_seed -> SUM159_NLS_2N_O2_A7K_harvest`
