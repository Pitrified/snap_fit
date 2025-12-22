# Grid Model Feature

## Overview

A grid model to represent puzzle piece placement with positions, orientations, and scoring.

### Key Requirements

- **Grid structure:** Rows × columns with typed positions (corner, edge, inner)
- **Piece classification:** Type derived from flat edge count; base edge orientation stored
- **Orientation math:** Compute rotation needed to place a piece in a target grid cell
- **Scoring:** Total grid score with cached segment-pair match lookups
- **Dynamic size:** Grid dimensions set at init (total pieces known, actual rows/cols configurable)

---

### Option A: Single Monolithic `GridModel` Class

A single class holding grid state, piece placements, orientation logic, and scoring.

**Pros:**

- Simple API surface; everything in one place
- Fewer files to maintain initially
- Easy to prototype in a notebook

**Cons:**

- Can grow unwieldy as complexity increases
- Harder to unit-test individual responsibilities
- Orientation math mixed with grid state management

---

### Option B: Layered Composition (Grid + PiecePlacement + OrientationUtils)

Separate concerns into:

1. `GridModel` – grid structure, position types, neighbor lookups
2. `PiecePlacement` – piece ↔ position assignments, orientations
3. `orientation_utils` – pure functions for rotation math
4. Scoring logic kept in `PieceMatcher` or a thin wrapper

**Pros:**

- Each unit is small and testable
- Orientation math reusable elsewhere
- Clearer boundaries for future extensions (e.g., solvers)

**Cons:**

- More files / imports to manage
- Slightly higher initial setup cost

---

### Option C: Data-Class-First Approach with Functional Scoring

Lean on Pydantic models for `GridCell`, `PlacedPiece`, `GridState`. Keep mutation minimal; scoring is a pure function over the state.

**Pros:**

- Immutable-friendly; easy to snapshot states for backtracking
- Pydantic validation for grid dimensions, orientations, etc.
- Functional scoring simplifies caching strategies

**Cons:**

- May require more boilerplate for state updates
- Less idiomatic if heavy mutation is expected during solving

---

**Please select an approach (A, B, or C)** so I can flesh out the detailed plan.

---

## Plan

_To be populated after approach selection._
