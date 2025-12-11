## Overview

We want to streamline the creation of `SheetAruco` and `ArucoDetector`.
Currently:
```python
board_config = ArucoBoardConfig(...)
generator = ArucoBoardGenerator(board_config)
detector_config = ArucoDetectorConfig(...)
detector = ArucoDetector(generator, detector_config)
sheet = SheetAruco(detector)
```

Desired:
```python
# Ideally simpler
sheet = SheetAruco(config)
```

We need to analyze the configuration structure to support this.

### Analysis: Nested vs Flat Config Structure

**Option A: Nested Config Structure**
`ArucoDetectorConfig` contains `ArucoBoardConfig`.
`SheetArucoConfig` (if created) contains `ArucoDetectorConfig`.

*   **Structure**:
    ```python
    @dataclass
    class ArucoDetectorConfig:
        board: ArucoBoardConfig
        dictionary_id: ...
        # other detector params
    ```
*   **Pros**:
    *   **Single Source of Truth**: Passing `detector_config` automatically provides all necessary board info.
    *   **Simplified Init**: `ArucoDetector(config)` is enough. It can access `config.board` to create the generator.
    *   **Encapsulation**: The dependency of the detector on the board is reflected in the config.
*   **Cons**:
    *   **Coupling**: `ArucoDetectorConfig` is now tightly coupled to `ArucoBoardConfig`. Harder to use the detector with a board that doesn't match that specific config class (though less likely here).

**Option B: Flat Config Structure**
Keep `ArucoDetectorConfig` and `ArucoBoardConfig` separate. Pass them explicitly.

*   **Structure**:
    ```python
    # Configs stay substantialy as they are
    ```
*   **Pros**:
    *   **Decoupling**: Configs are independent.
    *   **Flexibility**: Can mix and match easily.
*   **Cons**:
    *   **Verbose Init**: `ArucoDetector(detector_config, board_config)`.
    *   **Propagating Params**: `SheetAruco` would need `(detector_config, board_config)` in its init, which is less "streamlined" than just one config.

**Recommendation**: **Option A (Nested)**.
The goal is to "streamline". Having `ArucoDetectorConfig` own `ArucoBoardConfig` makes sense because `ArucoDetector` owns `ArucoBoardGenerator` (in the new plan). Conceptually, the detector setup *includes* the board setup in this application context.

If we go with Nested:
1.  Modify `ArucoDetectorConfig` to include `board: ArucoBoardConfig`.
2.  Refactor `ArucoDetector.__init__` to take `config` (which checks for `board` presence or takes it separately? No, strict nesting is cleaner).
    *   Actually, maybe `ArucoDetector` should just take `config` and `config.board` must be present.
3.  Refactor `SheetAruco.__init__` to take `detector_config` (and optional `board_config` override? No, keep it simple).

## Plan

1.  [x] **Modify Configs**: Update `ArucoDetectorConfig` to allow nesting or composition of `ArucoBoardConfig`.
    *   Actually, checking `aruco_detector_config.py`, it likely has parameters for `cv2.aruco.DetectorParameters`.
    *   We can add a `board_config` field.
2.  [x] **Refactor `ArucoDetector`**:
    *   Update `__init__` to accept `ArucoDetectorConfig` (which now has board info) OR `ArucoDetectorConfig` + `ArucoBoardConfig`.
    *   Let's go with: `__init__(self, config: ArucoDetectorConfig)`.
    *   It instantiates `ArucoBoardGenerator(config.board)`.
3.  [x] **Refactor `SheetAruco`**:
    *   Update `__init__` to accept `detector_config: ArucoDetectorConfig`.
    *   It instantiates `ArucoDetector(detector_config)`.
4.  [ ] **Update Usage**: Fix any breaking changes in tests/notebooks.
