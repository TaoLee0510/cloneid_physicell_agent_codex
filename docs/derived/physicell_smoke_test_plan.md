# PhysiCell Smoke Test Plan

## Goal

Run a minimal command-line smoke test from the successful local PhysiCell `v1.14.2` build without committing to any CLONEID-coupled model generation yet.

## Persistent install target

Recommended persistent source-tree location:

```text
/Users/4470246/Downloads/PhysiCell-1.14.2
```

## Smoke-test target

Use the already-built `heterogeneity` sample executable from the pinned `v1.14.2` source tree.

## Minimal runtime settings

For the first smoke test:

- `max_time = 60` minutes
- `omp_num_threads = 1`
- unique output folder per run

The repository wrapper `scripts/run_physicell_smoke_test.sh` temporarily patches the XML, runs the executable, and restores the original config afterward.

## Success criteria

The smoke test is considered successful if:

1. the executable starts and exits with code `0`
2. the output folder is created
3. at least one expected output artifact exists, such as:
   - `initial.svg`
   - `final.svg`
   - `output*.xml`
   - `legend.svg`

## Why this is sufficient for now

This validates:

- pinned source reproducibility
- compiler/runtime compatibility on this machine
- command-line execution independent of Studio
- output-folder creation

It does not yet validate:

- CLONEID-coupled model instantiation
- template generation from this repository
- model-family-specific XML generation
