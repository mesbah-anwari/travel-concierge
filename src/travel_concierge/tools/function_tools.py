"""Function tools the ADK agents call directly.

These wrap the same underlying helpers exposed by the MCP server so the
agents can also work without an MCP runtime (useful inside a Kaggle
notebook). The MCP server remains the production interface.
"""
from __future__ import annotations

from typing import Any

from travel_concierge.tools.travel_apis import (
    convert_currency as _convert_currency,
    geocode_city as _geocode_city,
    get_weather as _get_weather,
)


def get_weather(city: str, start_date: str, end_date: str) -> dict[str, Any]:
    """Daily forecast for `city` between `start_date` and `end_date` (YYYY-MM-DD)."""
    return _get_weather(city, start_date, end_date)


def convert_currency(amount: float, source_currency: str, target_currency: str) -> dict[str, Any]:
    """Convert `amount` from `source_currency` to `target_currency` (ISO codes)."""
    return _convert_currency(amount, source_currency, target_currency)


def geocode_city(city: str) -> dict[str, Any]:
    """Resolve a city to coordinates, country and timezone."""
    return _geocode_city(city)
