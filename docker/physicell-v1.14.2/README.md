# Docker Plan for PhysiCell `v1.14.2`

This directory contains the project-owned Docker build definition for the pinned PhysiCell backend.

Canonical image tag:

```text
cloneid-physicell:1.14.2
```

Planned build command:

```bash
docker build -t cloneid-physicell:1.14.2 docker/physicell-v1.14.2
```

This image is intended to:

- compile official PhysiCell core `v1.14.2`
- provide a reproducible command-line backend for local automation
- serve as the source image for optional Apptainer/Singularity conversion

It is not intended to provide PhysiCell Studio.
