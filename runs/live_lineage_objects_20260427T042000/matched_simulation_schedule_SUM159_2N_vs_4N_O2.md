# Matched Simulation Schedule

- Comparison: `SUM159_4N_O2_vs_SUM159_2N_O2`
- Matching strategy: `biological_milestone_alignment`
- Comparison window: `O2_A1_seed -> O2_A7K_harvest`
- Matched growth episodes: `8`
- Anchor transfer events: `7`
- Comparison transfer events: `7`

## Endpoint alignment

- Both branches contain A7K harvest: `True`
- Both A7K harvest endpoints have Perspective support: `True`
- Anchor terminal supported-event count: `1`
- Anchor terminal record count: `19`
- Comparison terminal supported-event count: `1`
- Comparison terminal record count: `16`

## Matched growth episodes

- `O2_A1_seedT1`: anchor `SUM-159_NLS_4N_O2_A1_seed -> SUM-159_NLS_4N_O2_A1_seedT1` vs comparison `SUM-159_NLS_2N_O2_A1_seed -> SUM-159_NLS_2N_O2_A1_seedT1`
- `O2_A2_seedT2`: anchor `SUM-159_NLS_4N_O2_A2_seed -> SUM-159_NLS_4N_O2_A2_seedT2` vs comparison `SUM-159_NLS_2N_O2_A2_seed -> SUM-159_NLS_2N_O2_A2_seedT2`
- `O2_A3_seedT2`: anchor `SUM-159_NLS_4N_O2_A3_seed -> SUM-159_NLS_4N_O2_A3_seedT2` vs comparison `SUM-159_NLS_2N_O2_A3_seed -> SUM-159_NLS_2N_O2_A3_seedT2`
- `O2_A4_seedT2`: anchor `SUM-159_NLS_4N_O2_A4_seed -> SUM-159_NLS_4N_O2_A4_seedT2` vs comparison `SUM-159_NLS_2N_O2_A4_seed -> SUM-159_NLS_2N_O2_A4_seedT2`
- `O2_A5_seedT2`: anchor `SUM-159_NLS_4N_O2_A5_seed -> SUM-159_NLS_4N_O2_A5_seedT2` vs comparison `SUM-159_NLS_2N_O2_A5_seed -> SUM-159_NLS_2N_O2_A5_seedT2`
- `O2_A6_seedT2`: anchor `SUM-159_NLS_4N_O2_A6_seed -> SUM-159_NLS_4N_O2_A6_seedT2` vs comparison `SUM-159_NLS_2N_O2_A6_seed -> SUM-159_NLS_2N_O2_A6_seedT2`
- `O2_A7_seedT2`: anchor `SUM-159_NLS_4N_O2_A7_seed -> SUM-159_NLS_4N_O2_A7_seedT2` vs comparison `SUM-159_NLS_2N_O2_A7_seed -> SUM-159_NLS_2N_O2_A7_seedT2`
- `O2_A7K_harvest`: anchor `SUM-159_NLS_4N_O2_A7K_seed -> SUM159_NLS_4N_O2_A7K_harvest` vs comparison `SUM-159_NLS_2N_O2_A7K_seed -> SUM159_NLS_2N_O2_A7K_harvest`

## Validation

- `O2_A7K_harvest_aligned_to_O2_A7K_harvest`: `True`
- `phase_index_matching_not_primary_alignment`: `True`
- `total_simulated_growth_duration_within_guardrail`: `True`
- `pre_o2_phases_remain_context_only`: `True`
- `terminal_perspective_support_retained_as_endpoint_validation`: `True`
