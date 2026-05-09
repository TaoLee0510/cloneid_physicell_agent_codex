# Minimum Longitudinal Evolution Record

This compact standard defines the low-cost record needed for auditable mechanistic comparison in long-term evolution experiments. The point is not only collecting more data; it is preserving the relationships that make proliferation-only, branch-specific fitness, and density-history hypotheses distinguishable.

## Required Event Ledger

- `event_id`
- `parent_event_id`
- `timestamp`
- `event_type`

The event ledger should make seeding, harvest, transfer, bottleneck, and endpoint events traversable without relying on figure legends or prose reconstruction.

## Culture Context

- seeded and harvested cell counts
- vessel area
- split ratio or bottleneck ratio
- transfer threshold
- culture medium or major environmental context
- branch label and replicate identity

## Event-Linked Imaging

Image-derived phenotype is most useful when anchored to the event ledger:

- post-seeding baseline
- pre-transfer or harvest
- late passage or endpoint

## Derived Phenotype

Record derived phenotype with processing provenance:

- `cellCount`
- `correctedCount`
- `areaOccupied_um2`
- `cellSize_um2`
- `confluence_proxy`
- QC status
- segmentation or processing version

Derived values should not be treated as raw observations without processing context.

## Terminal Perspective Anchor

Terminal assay-specific Perspective records should point back to an upstream Event:

- assay event id
- upstream culture event id
- assay type
- sample source
- Perspective id or equivalent assay-specific identifier
- raw data pointer or feature-matrix pointer
- QC flag

Perspective is endpoint or assay-specific validation/support, not longitudinal growth phenotype.

## Provenance

Every derived field should preserve:

- source image or source record
- processing script or software version
- segmentation settings
- QC filters and exclusions
- date of processing
- operator or pipeline identifier when available
- derivation notes

This minimal structure is enough to make mechanistic model comparison auditable without requiring exhaustive omics at every passage.
