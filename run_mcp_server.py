"""Convenience MCP server launcher: `python run_mcp_server.py`.

Self-bootstraps `src/` onto `sys.path` so it works from a fresh clone.
"""
from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from travel_concierge.mcp_server.server import mcp  # noqa: E402

if __name__ == "__main__":
    mcp.run()
