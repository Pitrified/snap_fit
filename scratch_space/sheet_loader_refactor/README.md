# Sheet Loader Refactor Plan

## Overview

The goal is to decouple `SheetManager` from the specifics of file loading and ArUco processing. We will introduce a `SheetArucoLoader` configured via a Pydantic model.

**Option A: Loader drives the Manager (Dependency Injection)**
The `SheetArucoLoader` is initialized with a `SheetManager` instance.
```python
loader = SheetArucoLoader(config, manager)
loader.load_from_folder(path) # Internally calls manager.add_sheet()
```
- **Pros:** Simple usage in the main script.
- **Cons:** Couples Loader to Manager.

**Option B: Iterator Pattern (Pure Decoupling)**
The `SheetArucoLoader` yields `Sheet` objects. The consumer (script) is responsible for adding them to the manager.
```python
loader = SheetArucoLoader(config)
for sheet in loader.scan_folder(path):
    manager.add_sheet(sheet, sheet.id)
```
- **Pros:** High cohesion, low coupling. Loader doesn't know about Manager. Manager doesn't know about Loader.
- **Cons:** Slightly more boilerplate in the consuming script.

**Option C: Batch Return**
The `SheetArucoLoader` returns a list of sheets.
```python
loader = SheetArucoLoader(config)
sheets = loader.load_all(path)
for sheet in sheets:
    manager.add_sheet(sheet, sheet.id)
```
- **Pros:** Simple.
- **Cons:** Loads everything into memory before processing (though we likely do that anyway).

## Plan

1. [ ] Define `SheetArucoLoaderConfig` (Pydantic).
    - Use `SheetArucoConfig` for sheet-level params (min_area, crop_margin) and embed `ArucoDetectorConfig` for detector settings.
2. [ ] Create `SheetArucoLoader` class.
3. [ ] Implement folder iteration and `SheetAruco` creation logic.
4. [ ] Remove `add_sheets` from `SheetManager`.
5. [ ] Update usage examples/notebooks.
