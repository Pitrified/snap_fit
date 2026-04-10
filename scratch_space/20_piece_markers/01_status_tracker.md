# High level status tracker for piece identity markers

## Overview

Implements `scratch_space/20_piece_markers/00_sheet_identity_plan.md`.

This tracker covers the full implementation of sheet identity QR codes, slot grid
labelling, and board image composition. Each step has a dedicated sub-file with
detailed plans, code stubs, data models, and test strategies.

**Branch target:** `feat/sheet-identity`

## Steps

| # | File | Title | Status | Dependencies |
|---|------|-------|--------|--------------|
| 02 | [02_sheet_metadata_model.md](02_sheet_metadata_model.md) | `SheetMetadata` Pydantic model | **done** | - |
| 03 | [03_qr_chunk_handler.md](03_qr_chunk_handler.md) | `QRChunkHandler` encode/decode | **done** | 02 |
| 04 | [04_metadata_zone_config.md](04_metadata_zone_config.md) | `MetadataZoneConfig` + `SlotGridConfig` | **done** | - |
| 05 | [05_slot_grid.md](05_slot_grid.md) | `SlotGrid` geometry + label rendering | **done** | 04 |
| 06 | [06_sheet_metadata_codec.md](06_sheet_metadata_codec.md) | `SheetMetadataEncoder` + `SheetMetadataDecoder` | **done** | 02, 03, 04 |
| 07 | [07_board_image_composer.md](07_board_image_composer.md) | `BoardImageComposer` full assembly | **done** | 05, 06 |
| 08 | [08_contour_centroid.md](08_contour_centroid.md) | Add `centroid` property to `Contour` | not started | - |
| 09 | [09_sheet_integration.md](09_sheet_integration.md) | Wire into `Sheet`, `SheetAruco`, records | not started | 02, 05, 06, 08 |
| 10 | [10_pyproject_dependency.md](10_pyproject_dependency.md) | Add `qrcode` dependency | **done** | - |

## Dependency graph

```
02 SheetMetadata ──┬──> 03 QRChunkHandler ──┐
                   │                         ├──> 06 MetadataCodec ──┐
04 Configs ────────┼──> 05 SlotGrid ─────────┘                      ├──> 07 Composer
                   │                                                 │
08 Centroid ───────┼─────────────────────────────────────────────────┤
                   │                                                 │
10 Dependency ─────┘                                                 └──> 09 Integration
```

## Notes

- Steps 02, 04, 08, 10 have no intra-plan dependencies and can be done in parallel
- Step 09 (integration) is the final wiring step and depends on most prior steps
- Each sub-file includes: objective, file touchmap, code stubs, test strategy
