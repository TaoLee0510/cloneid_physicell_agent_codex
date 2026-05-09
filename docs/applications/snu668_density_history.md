# SNU-668 Density-History Proof-of-Principle

This is the primary manuscript-facing application on `update_5.5`.

> In long-term r/K density selection, can late growth advantage be explained by fixed fitness alone, or is continuous event-linked crowding/confluence history required? When the same experiment is compressed to a publication-like sparse view, does mechanistic discrimination weaken or remain partially unresolved?

## Regimes

- `snu668_full_history`: primary CLONEID application regime. It uses event-linked seed/harvest episodes, transfer/bottleneck semantics, image-derived phenotype, confluence proxies, and terminal Perspective support.
- `snu668_published_like_compressed`: controlled ablation of the same internal case. It collapses event order, transfer semantics, per-event confluence, image provenance, and Perspective-to-event linkage into sparse publication-like summaries.
- `nwaa124_curated_external`: semi-structured external comparator based on Li et al. NSR 2021 nwaa124. It supports observability and identifiability comparison; it is not a biological benchmark against SNU-668.

## Manuscript-Facing Families

- `neutral_growth`: no branch/regime advantage and no density-history dependence.
- `fixed_state_fitness`: branch/regime-specific constant advantage is allowed, without continuous crowding-memory semantics.
- `density_dependent_growth`: explicit dependence on crowding/confluence/areaOccupied proxies and transfer/reset semantics.

Extended internal families may remain in benchmark JSON for compatibility, but paper-facing summaries should foreground the three families above.

## Interpretation Boundary

This application compares inferential resolution, not biological truth across datasets. Terminal Perspective is endpoint validation/support only. Identity is inferred secondary support only. The compressed and external arms show observability/identifiability loss when event-linked structure is absent.

Shortest dry-run command:

```bash
PYTHONPATH=src python3 -m cloneid_agent run \
  --config configs/applications/snu668_density_history.yaml \
  --output runs/update_5_5 \
  --mode dry-run \
  --fit \
  --make-figures
```

Mock SNU-668 values are deterministic schema fixtures. Manuscript numerical interpretation requires live read-only CLONEID extraction or an approved frozen SNU-668 snapshot.
