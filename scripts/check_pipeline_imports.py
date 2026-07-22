"""Check that pipeline entries still import against the current API.

Freshness guard for `pipelines/` (D9/D16 of the pipelines-cleanup effort): for
each entry it resolves the imports without running the body. Scripts are
imported, so their work must be guarded under `if __name__ == "__main__"`;
notebooks have only their import statements executed. Exits non-zero if any
entry fails to import.

Usage: python scripts/check_pipeline_imports.py [pipelines_dir]
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
from pathlib import Path
import sys

_MAGIC_PREFIXES = ("%", "!")


def _strip_magics(source: str) -> str:
    """Drop notebook magic and shell lines that are not valid Python."""
    return "\n".join(
        line
        for line in source.splitlines()
        if not line.lstrip().startswith(_MAGIC_PREFIXES)
    )


def _notebook_import_source(path: Path) -> str:
    """Return just the import statements from a notebook's code cells."""
    notebook = json.loads(path.read_text())
    imports: list[str] = []
    for cell in notebook.get("cells", []):
        if cell.get("cell_type") != "code":
            continue
        source = _strip_magics("".join(cell.get("source", [])))
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        imports.extend(
            ast.get_source_segment(source, node) or ""
            for node in tree.body
            if isinstance(node, (ast.Import, ast.ImportFrom))
        )
    return "\n".join(line for line in imports if line)


def _check_notebook(path: Path) -> None:
    """Execute a notebook's import statements in a throwaway namespace."""
    code = _notebook_import_source(path)
    exec(compile(code, str(path), "exec"), {})


def _check_script(path: Path) -> None:
    """Import a script module without running its `__main__` body."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        msg = f"cannot load module spec for {path}"
        raise ImportError(msg)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)


def check(pipelines_dir: Path) -> int:
    """Check every pipeline entry; return the number of failures."""
    entries = sorted(
        p
        for p in pipelines_dir.rglob("*")
        if p.suffix in {".py", ".ipynb"} and ".ipynb_checkpoints" not in p.parts
    )
    if not entries:
        print(f"no pipeline entries found under {pipelines_dir}")
        return 0
    failures = 0
    for path in entries:
        rel = path.relative_to(pipelines_dir.parent)
        try:
            if path.suffix == ".ipynb":
                _check_notebook(path)
            else:
                _check_script(path)
        except Exception as exc:
            failures += 1
            print(f"FAIL  {rel}  ({type(exc).__name__}: {exc})")
        else:
            print(f"ok    {rel}")
    print(f"\n{len(entries) - failures}/{len(entries)} pipeline entries import cleanly")
    return failures


def main() -> int:
    """Parse arguments and run the check; return a process exit code."""
    parser = argparse.ArgumentParser(description="Check pipeline imports.")
    parser.add_argument(
        "pipelines_dir",
        nargs="?",
        default="pipelines",
        type=Path,
        help="directory holding pipeline scripts and notebooks",
    )
    args = parser.parse_args()
    return 1 if check(args.pipelines_dir) else 0


if __name__ == "__main__":
    sys.exit(main())
