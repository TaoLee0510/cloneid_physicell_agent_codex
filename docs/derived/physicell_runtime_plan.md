# PhysiCell Runtime Plan

## Scope

This note turns the answered PhysiCell runtime question into a concrete repository-owned execution plan.

Pinned backend:

- PhysiCell core `v1.14.2`
- official release source: <https://github.com/MathCancer/PhysiCell/releases/tag/1.14.2>

This plan does not install PhysiCell yet. It defines the supported runtime surfaces and the provenance that future execution code should record.

## Supported runtime surfaces

The workflow should support the same pinned backend through three interchangeable surfaces:

1. local source build
2. project-owned Docker image
3. optional Apptainer/Singularity image derived from the same pinned environment

PhysiCell Studio is explicitly out of scope for automated execution. It may be used only for manual inspection or XML editing.

## Canonical repository layout

```text
docker/
  physicell-v1.14.2/
    Dockerfile
    README.md

containers/
  apptainer/
    physicell-v1.14.2.def

scripts/
  check_physicell_runtime.sh
```

Recommended user-controlled local source location:

```text
~/Downloads/PhysiCell-1.14.2/
```

The PhysiCell source tree should not be vendored into this repository unless explicitly requested later.

## Local source build plan

Primary target environment for this machine:

- macOS
- Homebrew `g++-15`
- `make`

Key upstream constraint from the official `1.14.2` release:

- macOS builds should define `PHYSICELL_CPP` to an OpenMP-capable `g++`

Planned local build procedure:

1. Obtain official PhysiCell `v1.14.2` source.
2. Set:
   - `PHYSICELL_CPP=/opt/homebrew/bin/g++-15`
3. Run `make` in the PhysiCell root.
4. Record:
   - PhysiCell version
   - compiler path
   - compiler version
   - build date
   - source path

Expected workflow-facing binary path:

```text
<PHYSICELL_SOURCE_ROOT>/project
```

The agent runtime should accept that path through `--physicell-bin`.

## Docker plan

Use a project-owned image built from the official `v1.14.2` release source, not an unpinned Studio image.

Image naming convention:

```text
cloneid-physicell:1.14.2
```

The Docker image should:

- install build essentials
- download the official `v1.14.2` tarball
- compile PhysiCell once during image build
- expose a shell suitable for batch command execution
- preserve the pinned version and source URL in labels or environment variables

The image is intended for:

- reproducible local command-line runs
- later conversion to an Apptainer/Singularity image for HPC

## Apptainer / Singularity plan

Use an Apptainer definition derived from the same pinned PhysiCell environment.

Preferred strategy:

1. build the project-owned Docker image
2. convert it to an Apptainer/Singularity image for HPC

Fallback strategy:

1. use the provided definition file
2. build directly from Ubuntu
3. compile the same PhysiCell `v1.14.2` release inside the container

The HPC image should preserve:

- PhysiCell version
- compiler stack
- source URL
- identical execution entrypoint assumptions

## Runtime provenance requirements

Every future local-test or HPC run should record:

- PhysiCell version tag
- backend type: `local_source`, `docker`, or `apptainer`
- source URL or image tag
- compiler path and version when applicable
- `OMP_NUM_THREADS`
- invoked command
- working directory
- generated model folder

## Immediate next implementation tasks after user confirmation

1. run `scripts/check_physicell_runtime.sh`
2. verify local compiler and Docker state on this machine
3. if approved, download official PhysiCell `v1.14.2`
4. attempt the local source build first
5. only then decide whether Docker or Apptainer is still needed immediately

## Why local source build remains the first execution target

On this machine, the easiest likely path is still the local source build because:

- `make` is available
- Homebrew `g++-15` is available
- official release notes explicitly support the `PHYSICELL_CPP` path on macOS
- Docker daemon availability was previously not confirmed

So the planning conclusion is:

- keep all three surfaces pinned and defined
- prefer local source build first for the first actual runtime execution
- use Docker and Apptainer mainly for reproducibility and HPC portability
