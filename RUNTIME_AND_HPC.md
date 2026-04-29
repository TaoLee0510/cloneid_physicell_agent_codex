# Runtime and HPC strategy

## Summary

The CLONEID–PhysiCell proof-of-principle should be developed in three execution tiers:

1. **Dry-run mode** — validates database access, dataset selection, CLONEID-to-PhysiCell mapping, candidate-model generation, and report generation without running PhysiCell.
2. **Local-test mode** — runs small PhysiCell simulations on a laptop, desktop, or workstation.
3. **Batch/HPC mode** — prepares many independent simulation jobs for parameter sweeps, stochastic replicates, and model-family comparisons.

The database-first design does not change the runtime strategy. The database is used for discovery, selection, and provenance. PhysiCell runtime only becomes substantial after candidate models are instantiated and executed.

## Pinned backend recommendation

Use official PhysiCell core `v1.14.2` as the pinned simulation backend:

- release source: <https://github.com/MathCancer/PhysiCell/releases/tag/1.14.2>
- use the official source release as the canonical backend for local builds, Docker builds, and HPC containers
- do not depend on PhysiCell Studio for automated execution

PhysiCell Studio may still be used for:

- human inspection of generated models
- manual XML editing during development

But the CLONEID-PhysiCell workflow itself should run command-line PhysiCell jobs generated from repository-managed templates.

If Docker is used, build a project-owned image from the official PhysiCell `v1.14.2` release rather than relying on an unpinned community Studio image.

If HPC execution is used, prefer Apptainer or Singularity images derived from that same pinned Docker or source environment so that local, Docker, and HPC runs stay aligned.

---

## Tier 1 — dry-run mode

Dry-run mode should be the first implementation target.

It should:

- connect to the CLONEID database in read-only mode,
- inventory available tables and candidate datasets,
- select a modelable dataset,
- select observables,
- generate the agent plan,
- generate candidate PhysiCell model folders,
- generate configuration stubs,
- generate placeholder evaluation files,
- generate a draft report and figure stubs.

It should not require a PhysiCell binary.

Example:

```bash
python -m cloneid_agent run \
  --db-url "$CLONEID_DB_READONLY_URL" \
  --templates model_templates/physicell \
  --output runs/test_dry_run \
  --mode dry-run
```

Equivalent using `.env`:

```bash
python -m cloneid_agent run \
  --templates model_templates/physicell \
  --output runs/test_dry_run \
  --mode dry-run
```

---

## Tier 2 — local-test mode

Local-test mode should run small simulations suitable for a laptop, desktop, or workstation.

Use local-test mode for:

- one selected dataset,
- 3 to 5 candidate model families,
- small cell numbers,
- reduced simulation duration,
- reduced spatial resolution,
- few stochastic replicates,
- debugging of PhysiCell configuration generation.

Example:

```bash
python -m cloneid_agent run \
  --db-url "$CLONEID_DB_READONLY_URL" \
  --templates model_templates/physicell \
  --physicell-bin /path/to/PhysiCell_v1.14.2/project \
  --output runs/local_test \
  --mode local-test \
  --threads 4
```

Recommended local-test backend:

- build official PhysiCell core `v1.14.2` from source on the workstation
- keep the checked-out or extracted source tree in a user-controlled path
- point the workflow at the project-owned executable or wrapper built from that tree

Local execution should not require PhysiCell Studio.

---

## Tier 3 — batch/HPC mode

Use HPC when running large model comparisons.

HPC is useful for:

- many model families,
- many parameter sets,
- many stochastic replicates,
- bootstrap or holdout analyses,
- multiple CLONEID datasets,
- large 3D domains,
- long simulated time horizons,
- expensive output generation,
- sensitivity analysis.

Standard PhysiCell workflows are usually best parallelized as many independent jobs rather than as one distributed simulation. The natural design is embarrassingly parallel:

```text
candidate_model_1 × parameter_set_001 × replicate_01
candidate_model_1 × parameter_set_001 × replicate_02
candidate_model_2 × parameter_set_001 × replicate_01
...
```

Each job should run one PhysiCell simulation using a controlled number of OpenMP threads.

Example preparation command:

```bash
python -m cloneid_agent prepare-hpc \
  --agent-plan runs/full_run/agent_plan.json \
  --output runs/full_run/hpc_jobs \
  --scheduler slurm \
  --threads-per-job 4 \
  --replicates 10
```

Recommended container strategy:

- Docker: build a project-owned image from official PhysiCell core `v1.14.2`
- HPC: derive an Apptainer/Singularity image from the same pinned Docker image or equivalent pinned source build
- use the same PhysiCell version, compiler/runtime stack, and template layout across local, Docker, and HPC execution

---

## OpenMP thread management

PhysiCell commonly uses OpenMP shared-memory parallelism. The workflow should explicitly set:

```bash
OMP_NUM_THREADS=<threads_per_simulation>
```

For large sweeps, it may be better to run many simulations with fewer threads each than one simulation with many threads.

The generated run metadata should record:

- `OMP_NUM_THREADS`,
- command used,
- PhysiCell binary path,
- PhysiCell version tag,
- source or container provenance,
- model folder,
- random seed,
- parameter set,
- job ID if run on HPC.

---

## Output management

Large simulation sweeps can produce excessive output.

Implement:

- sparse output intervals,
- optional output compression,
- per-run summary metrics,
- cleanup options for unnecessary intermediate files,
- one folder per model / parameter set / replicate,
- a top-level manifest that records all generated outputs.

---

## Scheduler support

The first HPC implementation should support SLURM job arrays.

Suggested generated files:

```text
runs/<run_id>/hpc_jobs/job_manifest.csv
runs/<run_id>/hpc_jobs/run_array.slurm
runs/<run_id>/hpc_jobs/collect_results.sh
```

The job manifest should include:

- job index,
- model ID,
- model family,
- parameter set ID,
- replicate ID,
- random seed,
- input model folder,
- output folder,
- command to run.

---

## Practical recommendation

For the first manuscript proof of principle, do not require HPC.

The first result should be possible with:

- one selected CLONEID dataset,
- 3 candidate model families,
- modest parameter grids,
- few stochastic replicates,
- local or single-node execution.

Build HPC support early enough that larger sweeps are easy, but do not make HPC a dependency for the minimal figure.
