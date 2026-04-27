# PhysiCell Smoke Test Check

## Scope

This note records the first successful minimal PhysiCell smoke test from the persistent local install of the pinned backend.

Inspection date:

- 2026-04-26

Pinned backend:

- PhysiCell `v1.14.2`

Persistent install location:

- `/Users/4470246/Downloads/PhysiCell-1.14.2`

Executable used:

- `/Users/4470246/Downloads/PhysiCell-1.14.2/heterogeneity`

## Smoke-test command

Repository wrapper:

```bash
scripts/run_physicell_smoke_test.sh /Users/4470246/Downloads/PhysiCell-1.14.2 60 1
```

Effective smoke settings:

- `max_time = 60`
- `omp_num_threads = 1`
- unique output folder

## Outcome

The smoke test completed successfully.

Observed runtime:

- about `2.53` seconds wall time

Output folder:

- `/Users/4470246/Downloads/PhysiCell-1.14.2/output_smoke_20260427T014616Z`

## Output artifacts observed

Confirmed files include:

- `initial.svg`
- `final.svg`
- `legend.svg`
- `initial.xml`
- `final.xml`
- `output00000000.xml`
- `output00000001.xml`
- matching `.mat` and graph companion files
- copied `PhysiCell_settings.xml`

## Meaning of this result

This validates:

1. the persistent local PhysiCell install path
2. command-line execution independent of Studio
3. minimal XML patch-and-restore smoke workflow
4. output-folder creation and artifact generation on this machine

This does not yet validate:

1. repository-generated PhysiCell model folders
2. CLONEID-to-PhysiCell template instantiation
3. candidate-model evaluation from this repository

## Recommended next step after user confirmation

Choose one:

1. run a first repository-coupled PhysiCell smoke test from a generated template/model stub
2. return to the CLONEID extraction branch and build the data-to-model handshake inputs
