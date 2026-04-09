# Step 06 - `SheetMetadataEncoder` + `SheetMetadataDecoder`

> **Status:** not started
> **Target file:** `src/snap_fit/aruco/sheet_metadata.py` (same file as Steps 02-03)
> **Depends on:** Steps 02, 03, 04

---

## Objective

Implement the encoder that renders QR codes and human-readable text onto a board
image, and the decoder that extracts `SheetMetadata` from a raw photo.

## Encoder: `SheetMetadataEncoder`

Renders 3 QR codes horizontally in the bottom interior strip, plus optional
human-readable text to the right.

### QR strip layout (default config)

```
Interior width:  700 px (x=120..820)
Strip height:    120 px (y=1100..1220)

3 QR codes at ~203 px each = 609 px
Spacing between codes: ~20 px
Remaining for text: ~50 px (may place text above or use second row)
```

If text does not fit beside QR codes, place it as a single line immediately
above the QR strip (y ~= 1090).

### Code stub

```python
import cv2
import numpy as np

from snap_fit.aruco.sheet_metadata import QRChunkHandler, SheetMetadata
from snap_fit.config.aruco.metadata_zone_config import MetadataZoneConfig


class SheetMetadataEncoder:
    """Renders QR codes + human text onto a board image."""

    def render(
        self,
        board_img: np.ndarray,
        metadata: SheetMetadata,
        config: MetadataZoneConfig,
    ) -> np.ndarray:
        """Return modified board image with QR strip and text."""
        img = board_img.copy()
        payload = metadata.to_qr_payload()

        # Encode QR codes
        handler = QRChunkHandler(n_codes=config.qr_n_codes, ecc=config.qr_ecc)
        qr_images = handler.encode(payload)

        # Place QR codes in the strip
        # Must compute strip position from board dimensions
        # (ring_band derived from board config, passed via constructor or params)
        self._place_qr_codes(img, qr_images, strip_region=...)

        # Place human-readable text
        if config.text_enabled:
            self._place_text(img, metadata, text_region=...)

        return img

    def _place_qr_codes(
        self,
        img: np.ndarray,
        qr_images: list[np.ndarray],
        strip_region: tuple[int, int, int, int],
    ) -> None:
        """Place QR images side by side in the strip region."""
        x0, y0, x1, y1 = strip_region
        strip_h = y1 - y0
        for i, qr_img in enumerate(qr_images):
            # Resize QR to fit strip height
            qr_resized = cv2.resize(qr_img, (strip_h, strip_h), interpolation=cv2.INTER_NEAREST)
            x_offset = x0 + i * (strip_h + 10)  # 10 px gap
            img[y0:y1, x_offset:x_offset + strip_h] = qr_resized

    def _place_text(
        self,
        img: np.ndarray,
        metadata: SheetMetadata,
        text_region: tuple[int, int],
    ) -> None:
        """Render human-readable text."""
        ts = f"{metadata.total_sheets:02d}" if metadata.total_sheets else "??"
        text = f"PUZZLE: {metadata.tag_name}  SHEET: {metadata.sheet_index + 1:02d}/{ts}  {metadata.printed_at}"
        x, y = text_region
        cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1, cv2.LINE_AA)
```

## Decoder: `SheetMetadataDecoder`

Extracts `SheetMetadata` from a raw (pre-rectification) photo by detecting any
QR code in the image.

### Code stub

```python
from loguru import logger as lg


class SheetMetadataDecoder:
    """Extracts SheetMetadata from a raw (pre-rectified) photo."""

    def decode(self, image: np.ndarray) -> SheetMetadata | None:
        """Try to decode metadata. Returns None with warning if not found."""
        handler = QRChunkHandler()
        payload = handler.decode_first(image)
        if payload is None:
            lg.warning("No QR code found in image")
            return None
        try:
            return SheetMetadata.from_qr_payload(payload)
        except (ValueError, IndexError):
            lg.warning(f"QR payload could not be parsed: {payload!r}")
            return None
```

### Pre-rectification decoding rationale

The plan specifies pre-rectification decoding (Decision #3). Reasons:
- Photos are already nearly straight (placed on a flat surface)
- Rectification crops the image, possibly cutting off QR codes at edges
- `cv2.QRCodeDetector` handles moderate perspective distortion

## File touchmap

| File | Change |
|------|--------|
| `src/snap_fit/aruco/sheet_metadata.py` | Add `SheetMetadataEncoder`, `SheetMetadataDecoder` classes |

## Test strategy

- **Encoder visual:** Compose board, render metadata, save, inspect in notebook
- **Encode-decode round-trip:** Encode onto blank image, decode back, assert match
- **Decoder on real-ish image:** Use `BoardImageComposer` output (post Step 07)
- **Decoder failure:** Image with no QR returns `None` without raising
- **Test file:** `tests/aruco/test_sheet_metadata.py`

## Open design questions

1. The encoder needs board geometry (ring band offset) to compute the strip
   region. Options:
   - Pass `ArucoBoardConfig` to the encoder
   - Accept strip region as explicit coordinates
   - Compute from the image dimensions (assuming standard layout)

   Recommendation: Accept `ArucoBoardConfig` in the encoder constructor or
   `render()` method. This keeps the encoder aware of the board geometry.

## Acceptance criteria

- [ ] Encoder places 3 QR codes in the bottom interior strip
- [ ] Encoder renders human-readable text with sheet identity
- [ ] Decoder recovers `SheetMetadata` from an encoded board image
- [ ] Decoder returns `None` gracefully on images without QR codes
- [ ] Decoder logs a warning (via loguru) when no QR is found
