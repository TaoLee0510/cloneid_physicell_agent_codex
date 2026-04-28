# Milestone-Matched Phase Plan

- Comparison: `SUM159_4N_O2_vs_SUM159_2N_O2`
- Matching strategy: `biological_milestone_alignment`
- Recommended comparison window: `O2_A1_seed -> O2_A7K_harvest`
- Start rationale: Use O2_A1_seed as the primary manuscript comparison start because both branches are explicitly O2-labeled from that point onward; preserve dp history as pre-O2 context rather than forcing it into the direct phase alignment.

## Endpoint alignment

- Both branches contain A7K harvest: `True`
- Both A7K harvest endpoints have Perspective support: `True`
- Anchor terminal supported-event count: `1`
- Anchor terminal record count: `19`
- Comparison terminal supported-event count: `1`
- Comparison terminal record count: `16`

## Matched milestone phases

- `O2_A1_seed`: anchor `SUM-159_NLS_4N_dp_seedT1 -> SUM-159_NLS_4N_O2_A1_seed` vs comparison `SUM-159_NLS_2N_dp_seedT1 -> SUM-159_NLS_2N_O2_A1_seed`
- `O2_A1_seedT1`: anchor `SUM-159_NLS_4N_O2_A1_seed -> SUM-159_NLS_4N_O2_A1_seedT1` vs comparison `SUM-159_NLS_2N_O2_A1_seed -> SUM-159_NLS_2N_O2_A1_seedT1`
- `O2_A2_seed`: anchor `SUM-159_NLS_4N_O2_A1_seedT1 -> SUM-159_NLS_4N_O2_A2_seed` vs comparison `SUM-159_NLS_2N_O2_A1_seedT1 -> SUM-159_NLS_2N_O2_A2_seed`
- `O2_A2_seedT2`: anchor `SUM-159_NLS_4N_O2_A2_seed -> SUM-159_NLS_4N_O2_A2_seedT2` vs comparison `SUM-159_NLS_2N_O2_A2_seed -> SUM-159_NLS_2N_O2_A2_seedT2`
- `O2_A3_seed`: anchor `SUM-159_NLS_4N_O2_A2_seedT2 -> SUM-159_NLS_4N_O2_A3_seed` vs comparison `SUM-159_NLS_2N_O2_A2_seedT2 -> SUM-159_NLS_2N_O2_A3_seed`
- `O2_A3_seedT2`: anchor `SUM-159_NLS_4N_O2_A3_seed -> SUM-159_NLS_4N_O2_A3_seedT2` vs comparison `SUM-159_NLS_2N_O2_A3_seed -> SUM-159_NLS_2N_O2_A3_seedT2`
- `O2_A4_seed`: anchor `SUM-159_NLS_4N_O2_A3_seedT2 -> SUM-159_NLS_4N_O2_A4_seed` vs comparison `SUM-159_NLS_2N_O2_A3_seedT2 -> SUM-159_NLS_2N_O2_A4_seed`
- `O2_A4_seedT2`: anchor `SUM-159_NLS_4N_O2_A4_seed -> SUM-159_NLS_4N_O2_A4_seedT2` vs comparison `SUM-159_NLS_2N_O2_A4_seed -> SUM-159_NLS_2N_O2_A4_seedT2`
- `O2_A5_seed`: anchor `SUM-159_NLS_4N_O2_A4_seedT2 -> SUM-159_NLS_4N_O2_A5_seed` vs comparison `SUM-159_NLS_2N_O2_A4_seedT2 -> SUM-159_NLS_2N_O2_A5_seed`
- `O2_A5_seedT2`: anchor `SUM-159_NLS_4N_O2_A5_seed -> SUM-159_NLS_4N_O2_A5_seedT2` vs comparison `SUM-159_NLS_2N_O2_A5_seed -> SUM-159_NLS_2N_O2_A5_seedT2`
- `O2_A6_seed`: anchor `SUM-159_NLS_4N_O2_A5_seedT2 -> SUM-159_NLS_4N_O2_A6_seed` vs comparison `SUM-159_NLS_2N_O2_A5_seedT2 -> SUM-159_NLS_2N_O2_A6_seed`
- `O2_A6_seedT2`: anchor `SUM-159_NLS_4N_O2_A6_seed -> SUM-159_NLS_4N_O2_A6_seedT2` vs comparison `SUM-159_NLS_2N_O2_A6_seed -> SUM-159_NLS_2N_O2_A6_seedT2`
- `O2_A7_seed`: anchor `SUM-159_NLS_4N_O2_A6_seedT2 -> SUM-159_NLS_4N_O2_A7_seed` vs comparison `SUM-159_NLS_2N_O2_A6_seedT2 -> SUM-159_NLS_2N_O2_A7_seed`
- `O2_A7_seedT2`: anchor `SUM-159_NLS_4N_O2_A7_seed -> SUM-159_NLS_4N_O2_A7_seedT2` vs comparison `SUM-159_NLS_2N_O2_A7_seed -> SUM-159_NLS_2N_O2_A7_seedT2`
- `O2_A7K_seed`: anchor `SUM-159_NLS_4N_O2_A7_seedT2 -> SUM-159_NLS_4N_O2_A7K_seed` vs comparison `SUM-159_NLS_2N_O2_A7_seedT2 -> SUM-159_NLS_2N_O2_A7K_seed`
- `O2_A7K_harvest`: anchor `SUM-159_NLS_4N_O2_A7K_seed -> SUM159_NLS_4N_O2_A7K_harvest` vs comparison `SUM-159_NLS_2N_O2_A7K_seed -> SUM159_NLS_2N_O2_A7K_harvest`

## Unmatched pre-O2 phases

- Anchor count: `6`
- Comparison count: `8`
- `anchor` `NLS_4N_A1_seed` `SUM-159_4N_NLS_mCherry -> SUM-159_NLS_4N_A1_seed`
- `anchor` `NLS_4N_A1_seedT2` `SUM-159_NLS_4N_A1_seed -> SUM-159_NLS_4N_A1_seedT2`
- `anchor` `NLS_4N_A2_seed` `SUM-159_NLS_4N_A1_seedT2 -> SUM-159_NLS_4N_A2_seed`
- `anchor` `NLS_4N_A2_seedT4` `SUM-159_NLS_4N_A2_seed -> SUM-159_NLS_4N_A2_seedT4`
- `anchor` `dp_seed` `SUM-159_NLS_4N_A2_seedT4 -> SUM-159_NLS_4N_dp_seed`
- `anchor` `dp_seedT1` `SUM-159_NLS_4N_dp_seed -> SUM-159_NLS_4N_dp_seedT1`
- `comparison` `NLS_2N_A3_seed` `SUM-159_NLS_mCherry -> SUM-159_NLS_2N_A3_seed`
- `comparison` `NLS_2N_A3_harvest_T3` `SUM-159_NLS_2N_A3_seed -> SUM-159_NLS_2N_A3_harvest_T3`
- `comparison` `NLS_2N_A4_seed` `SUM-159_NLS_2N_A3_harvest_T3 -> SUM-159_NLS_2N_A4_seed`
- `comparison` `NLS_2N_A4_harvest_T1` `SUM-159_NLS_2N_A4_seed -> SUM-159_NLS_2N_A4_harvest_T1`
- `comparison` `NLS_2N_A5_seed` `SUM-159_NLS_2N_A4_harvest_T1 -> SUM-159_NLS_2N_A5_seed`
- `comparison` `NLS_2N_A5_harvest_T3` `SUM-159_NLS_2N_A5_seed -> SUM-159_NLS_2N_A5_harvest_T3`
- `comparison` `dp_seed` `SUM-159_NLS_2N_A5_harvest_T3 -> SUM-159_NLS_2N_dp_seed`
- `comparison` `dp_seedT1` `SUM-159_NLS_2N_dp_seed -> SUM-159_NLS_2N_dp_seedT1`

## Unmatched extra branch history

- Anchor count: `0`
- Comparison count: `0`

## Unmatched post-comparison tail

- Anchor count: `0`
- Comparison count: `0`

## Validation

- `terminal_A7K_harvest_endpoints_aligned`: `True`
- `terminal_perspective_supported_events_aligned_as_endpoints`: `True`
- `phase_index_matching_not_primary_alignment`: `True`
- `unmatched_phases_labeled_as_prehistory_extra_or_post_tail`: `True`
- `total_simulated_duration_within_guardrail`: `True`
