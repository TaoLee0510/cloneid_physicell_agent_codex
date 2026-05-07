# SNU-668 Density-History Application

This application implements a focused proof-of-principle framework for the question:

> During long-term r/K density selection, can late-passaged growth advantage be explained by fixed fitness alone, or is continuous event-linked crowding/confluence history required? When the data are compressed to a published sparse view, does mechanistic discrimination become weaker or partially unresolved?

## Regimes

- `snu668_full_history`: primary CLONEID application regime. It uses event-linked longitudinal phenotype and terminal Perspective support.
- `snu668_published_like_compressed`: controlled ablation of the same internal case. It collapses event order, transfer semantics, and cumulative crowding history into a sparse publication-like summary.
- `nwaa124_curated_external`: semi-structured external comparator based on the local NSR r/K selection supplement. It is an observability/identifiability comparator, not a biological benchmark.

## Model Families

- `neutral_growth`: constant birth/death with no lineage or density-history advantage.
- `fixed_state_fitness`: branch/regime-specific constant proliferation or death advantage, without continuous crowding-memory semantics.
- `density_dependent_growth`: explicit dependence on crowding/confluence proxies and transfer/reset semantics.

## Interpretation Boundary

This branch compares inferential resolution, not biological truth across datasets. Terminal Perspective is endpoint validation/support only. Identity is inferred secondary support only. The compressed and external arms are used to show observability/identifiability loss.

Shortest dry-run command:

```bash
python -m cloneid_agent run --config configs/applications/snu668_density_history.yaml --output runs/update_5_4 --mode dry-run
```
