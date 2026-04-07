# `params`

> Module: `src/snap_fit/params/`
> Related tests: `tests/params/`

## Purpose

Provides the `SnapFitParams` singleton and `SnapFitPaths` for centralized access to project-wide configuration and filesystem paths. Every module that needs to locate data files, cache directories, or the project root uses this module.

## Usage

### Minimal example

```python
from snap_fit.params.snap_fit_params import get_snap_fit_params, get_snap_fit_paths

params = get_snap_fit_params()  # Singleton - same instance every time
paths = get_snap_fit_paths()    # Shortcut to params.paths

print(paths.root_fol)         # Project root directory
print(paths.cache_fol)        # cache/
print(paths.data_fol)         # data/
print(paths.aruco_board_fol)  # data/aruco_boards/
print(paths.sample_img_fol)   # data/sample/
print(paths.static_fol)       # static/
```

## API Reference

### `SnapFitParams`

Singleton class (via `Singleton` metaclass). On first instantiation, creates a `SnapFitPaths` instance and stores it as `self.paths`. Subsequent calls return the same instance.

### `SnapFitPaths`

Derives all paths from the package source location. Key attributes:

| Attribute | Path | Description |
|-----------|------|-------------|
| `src_fol` | `src/snap_fit/` | Package source directory |
| `root_fol` | `.` (repo root) | Project repository root |
| `cache_fol` | `cache/` | Cached contours, metadata, matches |
| `data_fol` | `data/` | Input data (images, configs) |
| `aruco_board_fol` | `data/aruco_boards/` | ArUco board definitions |
| `sample_img_fol` | `data/sample/` | Sample images for testing |
| `static_fol` | `static/` | Static web assets |

### `get_snap_fit_params()`

Returns the `SnapFitParams` singleton instance.

### `get_snap_fit_paths()`

Shortcut that returns `get_snap_fit_params().paths`.

## Common Pitfalls

- **Singleton behavior**: `SnapFitParams` is a true singleton. If you need different paths in tests, you must patch the instance rather than creating a new one.
- **Path derivation**: All paths are derived from `snap_fit.__file__`, so they are absolute and depend on the installation location. Do not hard-code paths elsewhere.

## Related Modules

- [`puzzle/sheet_manager`](../puzzle/sheet_manager.md) - uses cache and data paths for persistence
- [`webapp/core/settings`](../webapp/index.md) - webapp-specific path overrides via environment variables
