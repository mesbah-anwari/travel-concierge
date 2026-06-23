"""Convenience top-level CLI: `python main.py "..."`.

This shim makes the project runnable directly from a fresh clone without
having to `pip install -e .` first: it prepends the local `src/` folder
to `sys.path` before importing the package.
"""
from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from travel_concierge.__main__ import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
