# Step 03 - `QRChunkHandler` Encode/Decode

> **Status:** **done**
> **Target file:** `src/snap_fit/aruco/sheet_metadata.py` (same file as SheetMetadata)
> **Depends on:** Step 02 (SheetMetadata)

---

## Objective

Create a class that encodes a payload string into N identical QR code images and
decodes the payload from any image containing at least one readable QR code. All
N codes carry the full payload (redundancy, not chunking). Chunked mode is
explicitly deferred.

## Dependencies

- **Generation:** `qrcode` (pure-Python) - must be added to `pyproject.toml` (Step 10)
- **Detection:** `cv2.QRCodeDetector` - already available via `opencv-contrib-python`

## Code stub

```python
import cv2
import numpy as np
import qrcode
from qrcode.constants import ERROR_CORRECT_L, ERROR_CORRECT_M, ERROR_CORRECT_Q, ERROR_CORRECT_H


ECC_MAP: dict[str, int] = {
    "L": ERROR_CORRECT_L,
    "M": ERROR_CORRECT_M,
    "Q": ERROR_CORRECT_Q,
    "H": ERROR_CORRECT_H,
}


class QRChunkHandler:
    """Encodes/decodes a payload across N identical QR images.

    All N codes carry the full payload. Decode succeeds on any one.
    Chunked split-and-reconstruct or majority ECC is deferred.
    """

    def __init__(self, n_codes: int = 3, ecc: str = "M") -> None:
        self.n_codes = n_codes
        self.ecc = ecc

    def encode(self, payload: str) -> list[np.ndarray]:
        """Return list of N identical QR code images (numpy uint8 arrays)."""
        qr = qrcode.QRCode(
            error_correction=ECC_MAP[self.ecc],
            box_size=7,            # 7 px per module
            border=4,              # standard quiet zone
        )
        qr.add_data(payload)
        qr.make(fit=True)
        pil_img = qr.make_image(fill_color="black", back_color="white")
        arr = np.array(pil_img.convert("L"), dtype=np.uint8)
        return [arr.copy() for _ in range(self.n_codes)]

    def decode_first(self, image: np.ndarray) -> str | None:
        """Detect and decode any QR code in image. Returns payload or None."""
        detector = cv2.QRCodeDetector()
        data, _, _ = detector.detectAndDecode(image)
        if data:
            return data
        return None
```

### Design notes

- `box_size=7` matches the plan's calculation: `(21+8) * 7 = 203 px` per QR
  code, fitting comfortably in the strip
- `border=4` is the QR spec's standard quiet zone
- `encode()` returns copies so callers can modify independently
- `decode_first()` uses OpenCV's built-in detector (no extra dependency)
- The class name "ChunkHandler" signals future extensibility; current behavior is
  full-redundancy only

## File touchmap

| File | Change |
|------|--------|
| `src/snap_fit/aruco/sheet_metadata.py` | Add `QRChunkHandler` class |

## Test strategy

- **Encode-decode round-trip:** encode payload, decode from single image, assert match
- **Multi-code redundancy:** encode 3 codes, verify each individually decodes
- **Empty/long payload:** edge case strings
- **Image noise robustness:** (optional) add Gaussian noise and verify decode still works
- **Test file:** `tests/aruco/test_sheet_metadata.py`

## Acceptance criteria

- [ ] `encode()` returns `n_codes` numpy arrays, each decodable
- [ ] `decode_first()` recovers the original payload from any single code
- [ ] `decode_first()` returns `None` on an image with no QR code
- [ ] Works with all ECC levels (L, M, Q, H)
