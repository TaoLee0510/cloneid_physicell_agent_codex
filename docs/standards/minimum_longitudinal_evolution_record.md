# Minimum Longitudinal Evolution Record

This compact standard defines the low-cost record needed for auditable mechanistic comparison in long-term evolution experiments. The point is not just collecting more data; it is preserving the relationships that make fixed-state and history-dependent hypotheses distinguishable.

## Required Event Ledger

- `event_id`
- `parent_event_id`
- `timestamp`
- `event_type`

The event ledger should make seeding, harvest, transfer, bottleneck, and endpoint events traversable without relying on figure legends or prose reconstruction.

## Culture Context

- seeding count or density
- vessel area
- split ratio
- transfer threshold
- culture medium or major environmental context

## Event-Linked Imaging

Image at a few critical times is enough for a low-cost record when it is anchored to the event ledger:

- post-seeding baseline
- pre-transfer or harvest
- late passage or endpoint

## Derived Phenotype

Record derived phenotype with processing provenance:

- `cellCount`
- `areaOccupied`
- confluence proxy
- QC status
- segmentation or processing version

Derived values should not be treated as raw observations without their processing context.

## Terminal Perspective Anchor

Terminal assay-specific Perspective records should point back to an Event. Perspective is endpoint or assay-specific support, not longitudinal phenotype.

## Provenance

Every derived field should preserve:

- source image or source record
- processing script or software version
- QC filters and exclusions
- date of processing
- operator or pipeline identifier when available

This minimal structure is enough to make mechanistic model comparison auditable without requiring a heavy portal or exhaustive omics at every passage.
