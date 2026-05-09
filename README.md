# SNU-668 Density-History Proof-of-Principle

This branch is the manuscript-facing CLONEID application for one focused question:

> In long-term r/K density selection, can late growth advantage be explained by fixed fitness alone, or is continuous event-linked crowding/confluence history required? When the same experiment is compressed to a publication-like sparse view, does mechanistic discrimination weaken or remain partially unresolved?

The practical claim is narrow: CLONEID is an event-linked data standard and executable retrieval layer that makes this comparison auditable. The branch keeps the NSR nwaa124 external comparator machinery, but uses it as supporting evidence for what publication-level records can and cannot resolve automatically.

## Shortest Run

Dry-run/mock execution does not require live CLONEID access:

```bash
PYTHONPATH=src python3 -m cloneid_agent run \
  --config configs/applications/snu668_density_history.yaml \
  --output runs/update_5_5 \
  --mode dry-run \
  --fit \
  --make-figures
```

The lower-level benchmark command remains available:

```bash
PYTHONPATH=src python3 -m cloneid_agent.cli run-rk-benchmark \
  --config configs/applications/snu668_density_history.yaml \
  --output runs/rk_benchmark_mock \
  --mode mock \
  --fit \
  --make-figures
```

In dry-run/mock mode, SNU-668 values are deterministic schema fixtures. They validate retrieval, audit, downsampling, and report generation. They are not biological numerical results. Manuscript numerical interpretation requires live read-only CLONEID extraction or an approved frozen SNU-668 snapshot.

## Regimes Compared

- `snu668_full_history`: the primary CLONEID application regime. It preserves Event -> Phenotype -> Perspective linkage, seed/harvest growth episodes, transfer/bottleneck semantics, image-derived phenotype, confluence proxies, and terminal Perspective support.
- `snu668_published_like_compressed`: the main controlled ablation. It compresses the same SNU-668 fixture into a publication-like sparse summary by removing event IDs, parent-child graph structure, transfer semantics, per-event confluence, image provenance, and Perspective-to-event linkage.
- `nwaa124_curated_external`: the supporting external comparator based on Li et al. NSR 2021 nwaa124. It is a strong publication-level r/K-selection biological record for observability and identifiability comparison, not a biological head-to-head against SNU-668.

## Model Families

The manuscript-facing summaries foreground three families:

- `neutral_growth`: no lineage/regime advantage, no density feedback, no cumulative history dependence.
- `fixed_state_fitness`: a constant branch/regime-specific advantage is allowed, but no continuous crowding-memory term is used.
- `density_dependent_growth`: growth depends on event-linked crowding/confluence/areaOccupied proxies, with transfer/reset semantics and cumulative density-history exposure available.

Extended internal benchmark families may still be emitted for compatibility, but the paper-facing reports answer whether `fixed_state_fitness` can be separated from `density_dependent_growth` only when full event-linked history is present.

## Key Outputs

The run writes the manuscript-facing artifact tree under the requested output directory, including:

```text
model_selection_report.md
manuscript_facing_summary.md
family_discrimination_summary.md
modeling/comparative_identifiability_report.md
modeling/rejection_report.md
modeling/observability_matrix.json
modeling/observability_matrix.csv
modeling/family_comparison.json
modeling/family_comparison.csv
modeling/dataset_missingness.md
cloneid_full/history_covariates.json
cloneid_full/history_covariates.md
cloneid_downsampled/history_ablation.json
cloneid_downsampled/history_ablation.md
minimum_longitudinal_evolution_record.md
figure_data/
```

The legacy CLONEID-LTE benchmark artifacts are also preserved, including NSR extraction reports, CLONEID full/downsampled records, standards files, figures, and `MANUSCRIPT_INSERT.md`.

## External Comparator Role

The NSR supplement is not treated as weak data. It contains publication-level experimental records that support coarse reconstruction: growth-rate samples, reported growth-model fit statistics, carrying-capacity formulas, mixed-population dynamics, spatial model descriptions, migration/adhesion phenotype, and molecular summaries.

The comparison asks a different question: which mechanistic families are agent-ready and auditable from the available record structure? Plot-only evidence is not treated as raw numeric time series, and HeLa biology is not treated as equivalent to SNU-668 biology.

## Non-Claim Boundary

This branch does not claim mechanism proof, causality, or cross-cell-line biological equivalence. Endpoint `Perspective` records are validation/support only, `Identity` is inferred secondary support only, and transfer/passaging events are schedule resets rather than growth intervals.

## Read First

For implementation work, start with:

1. [`CODEX_INSTRUCTIONS.md`](CODEX_INSTRUCTIONS.md)
2. [`DATABASE_ACCESS.md`](DATABASE_ACCESS.md)
3. [`AGENT_WORKFLOW.md`](AGENT_WORKFLOW.md)
4. [`RUNTIME_AND_HPC.md`](RUNTIME_AND_HPC.md)
5. [`docs/CLONEID_SCHEMA_NOTES.md`](docs/CLONEID_SCHEMA_NOTES.md)
6. [`STATUS.md`](STATUS.md), [`WORK_QUEUE.md`](WORK_QUEUE.md), and [`QUESTION_QUEUE.md`](QUESTION_QUEUE.md)

The database remains the source of truth for live work. The repository can use exports, CSVs, JSON files, and snapshots only as fixtures, caches, or approved frozen manuscript inputs.
