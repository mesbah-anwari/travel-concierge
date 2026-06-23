"""Weather Agent — wraps the `get_weather` tool with travel context."""
from __future__ import annotations

from google.adk.agents import Agent

from travel_concierge.config import GEMINI_MODEL
from travel_concierge.tools.function_tools import get_weather, geocode_city

INSTRUCTION = """\
You are the Weather Specialist for a travel concierge.

Your job: given a destination city and a date range (YYYY-MM-DD), call the
`get_weather` tool exactly once, then summarise the forecast for a traveller.

Output rules:
- Begin with a one-line headline (e.g. "Mostly sunny, 22-28°C, light rain on Day 3").
- Follow with a short markdown table: date | high | low | precip | wind.
- End with 1-2 practical clothing/gear tips (umbrella, sunscreen, layers...).
- If the requested dates fall outside the 16-day horizon, say so honestly
  and give general seasonal expectations for that city.
- Never invent numbers. If the tool returns no data, say "forecast unavailable".
- Keep total response under 200 words.
"""

weather_agent = Agent(
    name="weather_agent",
    model=GEMINI_MODEL,
    description=(
        "Provides daily weather forecasts and packing-relevant weather tips "
        "for a destination over a date range."
    ),
    instruction=INSTRUCTION,
    tools=[get_weather, geocode_city],
)
