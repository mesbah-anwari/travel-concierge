"""Async runner that ties the ADK agent system to the security layer.

Use `plan_trip(message)` from notebooks and scripts; use `__main__` for
the CLI (see `main.py`).
"""
from __future__ import annotations

import asyncio
import uuid
from typing import AsyncIterator

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

from travel_concierge.agents.coordinator import root_agent
from travel_concierge.config import require_api_key
from travel_concierge.security.guards import guard_input, guard_output

APP_NAME = "travel_concierge"


def _new_runner() -> Runner:
    require_api_key()
    return Runner(
        app_name=APP_NAME,
        agent=root_agent,
        session_service=InMemorySessionService(),
    )


async def _stream(message: str, user_id: str, session_id: str) -> AsyncIterator[str]:
    runner = _new_runner()
    # Some ADK versions return a coroutine, others return directly — handle both.
    create = runner.session_service.create_session(
        app_name=APP_NAME, user_id=user_id, session_id=session_id
    )
    if asyncio.iscoroutine(create):
        await create

    content = genai_types.Content(
        role="user", parts=[genai_types.Part(text=message)]
    )
    async for event in runner.run_async(
        user_id=user_id, session_id=session_id, new_message=content
    ):
        # Only the final response from the coordinator is shown to the user;
        # intermediate sub-agent traces are useful for debugging but noisy.
        if event.is_final_response() and event.content and event.content.parts:
            for part in event.content.parts:
                txt = getattr(part, "text", None)
                if txt:
                    yield txt


async def plan_trip_async(user_message: str) -> str:
    """End-to-end: guard input → run agents → guard output."""
    g = guard_input(user_message)
    if not g.allowed:
        return f"⚠️  Request blocked by safety guard: {g.reason}"

    user_id = f"user-{uuid.uuid4().hex[:8]}"
    session_id = f"sess-{uuid.uuid4().hex[:8]}"

    chunks: list[str] = []
    async for chunk in _stream(g.text, user_id, session_id):
        chunks.append(chunk)
    raw = "\n".join(chunks).strip() or "(no response)"

    out = guard_output(raw)
    if not out.allowed:
        return out.text  # already a safe fallback
    return out.text


def plan_trip(user_message: str) -> str:
    """Sync wrapper. Safe to call from notebooks and scripts."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # In a Jupyter/Kaggle notebook the loop is already running.
            import nest_asyncio  # type: ignore[import-not-found]

            nest_asyncio.apply()
            return loop.run_until_complete(plan_trip_async(user_message))
    except RuntimeError:
        pass
    return asyncio.run(plan_trip_async(user_message))
