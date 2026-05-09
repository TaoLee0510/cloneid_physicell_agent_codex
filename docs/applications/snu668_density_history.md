# SNU-668 Density-History r/K Benchmark

This application is implemented by the flagship command:

```bash
PYTHONPATH=src python3 -m cloneid_agent.cli run-rk-benchmark \
  --config configs/applications/snu668_density_history.yaml \
  --external-zip /mnt/data/nwaa124_supplement_file.zip \
  --mode mock \
  --output runs/rk_benchmark_config_mock \
  --fit \
  --make-figures
```

The application compares three regimes:

- `NSR_publication_level_reconstructed_record`
- `CLONEID_full_native_record`
- `CLONEID_publication_level_downsampled_record`

The scientific question is whether r/K density adaptation is identifiable from proliferation-only or branch-specific fitness terms, or whether density/confluence/spatial interaction terms require event-linked history.

In mock mode, SNU-668 values are deterministic schema fixtures. They are useful for validating the retrieval, audit, and modelability workflow, but manuscript numerical interpretation requires live read-only CLONEID extraction or an approved frozen SNU-668 snapshot.

The NSR comparator is treated as a strong publication-level biological record. Its supplement supports coarse reconstruction from structured tables, figure captions, model formulas, methods text, and molecular summaries. The benchmark does not treat plot-only evidence as raw numeric data and does not criticize the original paper.
