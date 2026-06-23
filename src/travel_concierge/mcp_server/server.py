"""Custom MCP server exposing travel-domain tools.

Run as a standalone process:

    python -m travel_concierge.mcp_server.server

The server speaks the Model Context Protocol over stdio and exposes three
tools that any MCP-aware client (Claude Desktop, ADK agents, the
GitHub Copilot CLI, etc.) can call:

* `get_weather`     — daily forecast for a city between two dates
* `convert_currency`— FX conversion between two ISO-4217 codes
* `geocode_city`    — resolve a city name to lat/lon + country + timezone
"""
from __future__ import annotations

from fastmcp import FastMCP

from travel_concierge.tools.travel_apis import (
    convert_currency as _convert_currency,
    geocode_city as _geocode_city,
    get_weather as _get_weather,
)

mcp = FastMCP("travel-concierge-tools")


@mcp.tool()
def get_weather(city: str, start_date: str, end_date: str) -> dict:
    """Return a daily forecast for `city` between two ISO dates (YYYY-MM-DD).

    Powered by Open-Meteo (free, no API key).
    """
    return _get_weather(city, start_date, end_date)


@mcp.tool()
def convert_currency(amount: float, source: str, target: str) -> dict:
    """Convert `amount` from ISO currency `source` to `target`.

    Uses exchangerate.host when online, falls back to a static rate table
    when the network is unreachable (e.g. inside a Kaggle offline notebook).
    """
    return _convert_currency(amount, source, target)


@mcp.tool()
def geocode_city(city: str) -> dict:
    """Resolve a city name to {latitude, longitude, country, timezone}."""
    return _geocode_city(city)


if __name__ == "__main__":  # pragma: no cover
    # FastMCP defaults to stdio transport, which is what ADK / Claude Desktop
    # / Copilot CLI all consume.
    mcp.run()
