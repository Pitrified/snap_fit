# Step 4: Migrate existing cache data to SQLite

> Part of [10_ui_scaling.md](./10_ui_scaling.md) - SQLite migration plan
> Depends on: [Step 1](./11_sqlite_persistence_module.md) (DatasetStore exists)
> Can run before or in parallel with: [Step 3](./13_services_sqlite_migration.md)

---

## Starting point

Existing cache on disk:

```
cache/
  metadata.json          <- stale root-level leftover (not used by webapp)
  matches.json           <- stale root-level leftover (not used by webapp)
  contours/              <- stale root-level leftover (not used by webapp)
    01_PXL_*_contours.npz
    01_PXL_*_corners.json
    ... (6 sheets)
  oca/
    metadata.json        <- 6 sheets, 6 pieces (321 lines)
    matches.json         <- 240 matches (4321 lines)
    contours/
      01_PXL_*_contours.npz
      01_PXL_*_corners.json
      ... (6 sheets)
```

The `cache/metadata.json`, `cache/matches.json`, and `cache/contours/` at the root level are leftovers from before the `sheets_tag` subdirectory refactor. They contain the same data as `cache/oca/` (duplicated). The webapp services only look inside tag subdirectories, so these root files are dead weight.

Only the `oca` dataset exists as a tagged subdirectory. Other datasets (`milano1`) have config files in `data/` but have not been ingested into the cache yet.

---

## What changes

### Migration notebook / script

Create a migration notebook cell (preferred - visible, reproducible, interactive) or a standalone script. The operation is:

For each tag directory in `cache/`:
1. Read `metadata.json` via `SheetManager.load_metadata()`
2. Convert raw dicts to `SheetRecord` and `PieceRecord` objects via `model_validate()`
3. Read `matches.json` via `PieceMatcher.load_matches_json()` (or direct JSON parse + `MatchResult.model_validate()`)
4. Create `DatasetStore(tag_dir / "dataset.db")`
5. Call `store.save_sheets(sheet_records)`, `store.save_pieces(piece_records)`, `store.save_matches(match_results)`
6. Close the store

This is a ~20-line operation per dataset. A notebook cell is the right place for this.

### Where to put the notebook cell

Option A: Add cells to the existing `scratch_space/fastapi_scaffold/01_db_ingestion.ipynb`
Option B: Create a new notebook `scratch_space/fastapi_scaffold/02_sqlite_migration.ipynb`

Decision: Option A - add to the existing notebook since it already covers ingestion patterns. Add a new section header "Phase 6: Migrate JSON cache to SQLite".

### Migration is idempotent

`DatasetStore.save_*` methods use DELETE + INSERT. Running the migration twice produces the same result. This is important for safety - no harm in re-running if something looks off.

### Clean up root-level stale files

After migration completes and is verified, delete:
- `cache/metadata.json`
- `cache/matches.json`
- `cache/contours/` (entire directory)

These are duplicates of `cache/oca/` and are never read by the webapp. This cleanup is a manual step (not automated) to avoid accidental data loss. The notebook should print a clear message like "Root-level cache files can now be safely removed" with the exact file paths.

### Add `cache/oca/dataset.db` to .gitignore?

Currently `cache/` is likely already in `.gitignore` (binary artifacts should not be committed). Verify this. If not, add it.

---

## Expected outcome

After migration:

```
cache/
  oca/
    metadata.json          <- kept for now (removed in step 5)
    matches.json           <- kept for now (removed in step 5)
    dataset.db             <- NEW: 3 tables, indexed
    contours/
      01_PXL_*_contours.npz
      01_PXL_*_corners.json
      ...
```

Root-level stale files are removed:

```
cache/
  oca/
    ...
```

The `dataset.db` for OCA should be very small (6 sheets, 6 pieces, 240 matches - a few KB).

---

## Validation

### Verification in the migration notebook itself

The migration notebook cell should include inline assertions:

1. **Record counts match:** `len(store.load_sheets()) == len(json_data["sheets"])` and same for pieces and matches
2. **Field spot-check:** Pick the first sheet from both sources, compare `sheet_id`, `piece_count`, `threshold`, `min_area` fields
3. **Match spot-check:** Load top 5 matches from both sources (sorted by similarity), compare `similarity` values and segment IDs
4. **Match count:** `store.match_count() == 240` (known value for OCA dataset)
5. **Query test:** `store.query_matches_for_piece("03_PXL_20251207_204139976.jpg:0")` returns results (this piece is in the top match pair in the OCA dataset)

### Webapp UI verification

After migration, start the dev server and verify:

- If step 3 (services migration) is already deployed: pages should work immediately since services now read from `dataset.db`
- If step 3 is not yet deployed: services still read `metadata.json`/`matches.json` which are still present, so pages work as before
- Either way, the webapp should function identically

### Database inspection

Open the `.db` file directly to inspect:

```python
import sqlite3
conn = sqlite3.connect("cache/oca/dataset.db")
cursor = conn.cursor()

# Check tables exist
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print(cursor.fetchall())  # -> [('sheets',), ('pieces',), ('matches',)]

# Check row counts
for table in ["sheets", "pieces", "matches"]:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")  # noqa: S608
    print(f"{table}: {cursor.fetchone()[0]} rows")

# Check indexes exist
cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
print(cursor.fetchall())

conn.close()
```

---

## Risk assessment

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| Data loss during migration | Very low | Migration only creates new files; does not modify or delete JSON originals |
| Mismatch between JSON and SQLite data | Low | Inline assertions in notebook verify equality |
| `similarity_manual_` alias not round-tripping | Medium | Known Pydantic alias complexity; test explicitly with a record that has a non-null `similarity_manual` value |
| Root-level file deletion breaks something | Very low | Webapp services only look in tag subdirectories; verify with grep before deleting |

---

## Execution order note

This step can be executed **before** step 3 (services migration). In fact, the recommended order is:

1. Step 1: build DatasetStore
2. Step 4: migrate existing data (this step)
3. Step 3: switch services to SQLite reads
4. Step 2: add SQLite methods to domain classes (can happen anytime after step 1)
5. Step 5: remove JSON code

The logical numbering (1-2-3-4-5) follows the architectural layers. The execution order prioritizes having data ready before switching read paths.
