"""find_undocumented.py - List src/snap_fit submodules that lack a docs/library/ page.

Usage:
    uv run python .github/skills/docs-write/scripts/find_undocumented.py

Output: one line per undocumented submodule, relative to the repo root.
"""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "src" / "snap_fit"
LIBRARY = ROOT / "docs" / "library"


def main() -> None:
    """Check each src/snap_fit submodule for corresponding docs/library/ page."""
    missing: list[str] = []

    for init in sorted(SRC.rglob("__init__.py")):
        package_dir = init.parent
        # Skip the root package itself and __pycache__
        if package_dir == SRC:
            continue
        rel = package_dir.relative_to(SRC)
        parts = rel.parts
        # Skip internal/cache dirs
        if any(p.startswith("_") for p in parts):
            continue

        submodule = "/".join(parts)
        doc_dir = LIBRARY / Path(*parts)

        # Consider documented if index.md or any .md exists in the matching dir
        has_docs = doc_dir.exists() and any(doc_dir.glob("*.md"))
        if not has_docs:
            missing.append(submodule)

    if missing:
        print(f"{len(missing)} undocumented submodule(s):\n")
        for m in missing:
            print(f"  missing  src/snap_fit/{m}/")
        sys.exit(1)
    else:
        print("All submodules have at least one docs/library/ page.")
        sys.exit(0)


if __name__ == "__main__":
    main()
