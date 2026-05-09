# Minimum Longitudinal Evolution Record

This compact standard defines the low-cost record needed for auditable mechanistic comparison in long-term evolution experiments. The point is not only collecting more data; it is preserving the relationships that make proliferation-only, branch-specific fitness, and density-history hypotheses distinguishable.

The standard is question-specific. For density-history model discrimination, a low-cost gold-standard-style LTEE record must preserve enough structure to answer which observations are growth episodes, which records are transfer resets, which density/confluence exposure preceded each harvest, and which terminal Perspective anchors to which upstream event.

## Question-Specific Minimum Data

| Question | Minimum required data |
|---|---|
| Can fixed fitness be separated from density-history dependence? | branch labels; seed/harvest episodes; elapsed time; seeded and harvested counts; event-linked confluence or areaOccupied proxy |
| Are passaging events growth intervals or schedule resets? | event type; parent event id; seed/harvest/transfer classification; split or bottleneck ratio |
| Which density exposure preceded endpoint assay? | ordered event graph; cumulative confluence exposure; Perspective origin or upstream event id |
| Can an agent create an auditable model schedule? | event ledger; vessel context; phenotype provenance; transfer semantics; endpoint assay anchor |

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
