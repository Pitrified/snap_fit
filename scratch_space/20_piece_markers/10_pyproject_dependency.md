# Step 10 - Add `qrcode` Dependency

> **Status:** not started
> **Target file:** `pyproject.toml`
> **Depends on:** nothing

---

## Objective

Add the `qrcode` Python package to project dependencies. This is required by
`QRChunkHandler.encode()` (Step 03) for generating QR code images.

## Change

```toml
# In pyproject.toml, add to [project.dependencies]:
"qrcode>=8.0",
```

### Package details

- **PyPI:** https://pypi.org/project/qrcode/
- **License:** BSD
- **Pure Python:** Yes (no C extensions)
- **Transitive deps:** Only `pypng` (for PNG output) - but we use `make_image()`
  which returns a PIL Image, then convert to numpy, so `Pillow` (already
  implicitly available via matplotlib) is the actual backend
- **Version constraint:** `>=8.0` - version 8 introduced type hints and modern API

### Why not use OpenCV for encoding?

OpenCV has `cv2.QRCodeEncoder` (since 4.5.3) but:
- Its API is less mature and less documented
- `qrcode` library provides more control over version, ECC, box size, border
- `qrcode` is widely used and well-tested

OpenCV's `cv2.QRCodeDetector` is used for decoding (no extra dependency needed).

## Verification

After adding:

```bash
uv sync
uv run python -c "import qrcode; print(qrcode.__version__)"
```

## File touchmap

| File | Change |
|------|--------|
| `pyproject.toml` | Add `"qrcode>=8.0"` to dependencies list |

## Acceptance criteria

- [ ] `qrcode` is importable in the project environment
- [ ] `uv run pytest` still passes (no conflicts)
- [ ] `uv run ruff check .` passes
