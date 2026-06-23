"""Centralised config for the agent system.

All LLM model selection, env-loading and constants live here so individual
agent modules stay declarative.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

# Load .env from project root if present (no-op in Kaggle where env vars
# are usually set via the secrets UI). We try a few strategies so the file
# is found whether the user runs from the project root, from src/, or has
# `pip install -e .`'d the package into a different venv.
#
# Layout:  <project_root>/src/travel_concierge/config.py
# So the project root is parents[2] of this file.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_dotenv_path = _PROJECT_ROOT / ".env"
if _dotenv_path.is_file():
    load_dotenv(_dotenv_path, override=False)
else:
    # Walk upward from cwd looking for the nearest .env
    discovered = find_dotenv(usecwd=True)
    if discovered:
        load_dotenv(discovered, override=False)

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
DEFAULT_HOME_CURRENCY = os.getenv("DEFAULT_HOME_CURRENCY", "USD")


def require_api_key() -> str:
    """Return the Google AI Studio key or raise a friendly error."""
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set.\n"
            "Get a free key at https://aistudio.google.com/apikey and either:\n"
            "  - copy .env.example to .env and fill it in, OR\n"
            "  - set the env var: $env:GOOGLE_API_KEY='...'  (PowerShell)\n"
            "                     export GOOGLE_API_KEY=...  (bash)"
        )
    # Ensure ADK / google-generativeai both see it.
    os.environ.setdefault("GOOGLE_API_KEY", key)
    os.environ.setdefault("GEMINI_API_KEY", key)
    return key
