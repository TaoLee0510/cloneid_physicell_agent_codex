# PhysiCell Local Build Check

## Scope

This note records the first successful local source-build check for the pinned PhysiCell backend on this machine.

Inspection date:

- 2026-04-26

Pinned backend:

- PhysiCell `v1.14.2`

Source location used for the check:

- `/tmp/PhysiCell-1.14.2-src`

Compiler used:

- `/opt/homebrew/bin/g++-15`

## Download path used

Official release tarball:

- `https://github.com/MathCancer/PhysiCell/archive/refs/tags/1.14.2.tar.gz`

## First build attempt

Command:

```bash
make
```

Result:

- failed on macOS default compiler path
- error was the expected OpenMP issue from upstream notes:
  - `clang++: error: unsupported option '-fopenmp'`

Interpretation:

- the local source-build path is viable
- the build must explicitly set `PHYSICELL_CPP` to an OpenMP-enabled Homebrew GCC

## Successful build command

Command:

```bash
env PHYSICELL_CPP=/opt/homebrew/bin/g++-15 make
```

Result:

- build completed successfully
- upstream sample project selected by default: `heterogeneity`
- resulting executable name reported by `make`:
  - `heterogeneity`

## Current conclusion

The first actual PhysiCell backend-execution branch is viable on this machine via local source build, provided that:

```bash
export PHYSICELL_CPP=/opt/homebrew/bin/g++-15
```

is set before running `make`.

## Remaining limitations

- this build happened in `/tmp`, not a persistent user-chosen installation path
- Docker-based execution is still blocked because the Docker daemon is not reachable from the current context
- Apptainer/Singularity execution is still blocked because those runtimes are not installed

## Recommended next step after user confirmation

Choose one of these:

1. repeat the local source build in a persistent user-chosen location and record the stable `--physicell-bin` path
2. start the first minimal PhysiCell runtime execution from the successful local build tree
3. add a repository wrapper that prepares sample/template model folders against the local PhysiCell source tree
