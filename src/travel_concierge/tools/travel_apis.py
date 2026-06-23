"""Thin HTTP wrappers around free, no-auth APIs used by the MCP server.

* Open-Meteo for forecast + geocoding (https://open-meteo.com/)
* exchangerate.host for currency conversion (https://exchangerate.host/)

These functions are dependency-light (httpx only) and return plain dicts so
they can be re-used both from the MCP server and from agent tools.

All network calls are wrapped: any failure (DNS, SSL, timeout, 5xx) returns
a structured fallback payload so the agents can still produce a useful
answer even on Kaggle's offline notebooks or behind a strict corporate
proxy.
"""
from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Any

import httpx

_TIMEOUT = httpx.Timeout(15.0, connect=10.0)
_OPEN_METEO_GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"
_OPEN_METEO_FORECAST = "https://api.open-meteo.com/v1/forecast"
_FX_BASE = "https://api.exchangerate.host"

# Escape hatch for corporate networks with self-signed root CAs.
_VERIFY = os.getenv("TRAVEL_CONCIERGE_INSECURE_SSL", "").lower() not in {
    "1", "true", "yes",
}


def _client() -> httpx.Client:
    return httpx.Client(timeout=_TIMEOUT, verify=_VERIFY)


def geocode_city(city: str) -> dict[str, Any]:
    """Resolve a city name to lat/lon, country, timezone."""
    try:
        with _client() as c:
            r = c.get(
                _OPEN_METEO_GEOCODE,
                params={"name": city, "count": 1, "language": "en", "format": "json"},
            )
            r.raise_for_status()
            data = r.json()
    except Exception as exc:
        return {"found": False, "query": city, "error": f"network error: {exc.__class__.__name__}"}
    results = data.get("results") or []
    if not results:
        return {"found": False, "query": city}
    top = results[0]
    return {
        "found": True,
        "query": city,
        "name": top.get("name"),
        "country": top.get("country"),
        "country_code": top.get("country_code"),
        "latitude": top.get("latitude"),
        "longitude": top.get("longitude"),
        "timezone": top.get("timezone"),
    }


def get_weather(city: str, start: str, end: str) -> dict[str, Any]:
    """Daily forecast for `city` between ISO dates `start` and `end`.

    Open-Meteo's free forecast endpoint covers up to ~16 days ahead. For
    longer horizons (or any network failure) we return a structured
    "no forecast" payload so the agent can fall back to seasonal advice.
    """
    geo = geocode_city(city)
    if not geo["found"]:
        return {
            "ok": False,
            "city": city,
            "error": geo.get("error") or f"could not geocode city '{city}'",
            "note": "Forecast unavailable; ask the user to confirm spelling or supply seasonal expectations.",
        }

    today = date.today()
    try:
        s = date.fromisoformat(start)
        e = date.fromisoformat(end)
    except ValueError as exc:
        return {"ok": False, "error": f"bad date format: {exc}"}
    if e < s:
        s, e = e, s

    max_end = today + timedelta(days=15)
    s_clip = max(s, today)
    e_clip = min(e, max_end)
    if s_clip > e_clip:
        return {
            "ok": True,
            "city": geo["name"],
            "country": geo["country"],
            "note": (
                "Requested dates are outside the 16-day forecast horizon; "
                "returning seasonal placeholder."
            ),
            "daily": [],
        }

    try:
        with _client() as c:
            r = c.get(
                _OPEN_METEO_FORECAST,
                params={
                    "latitude": geo["latitude"],
                    "longitude": geo["longitude"],
                    "daily": ",".join([
                        "temperature_2m_max",
                        "temperature_2m_min",
                        "precipitation_sum",
                        "weather_code",
                        "wind_speed_10m_max",
                    ]),
                    "timezone": geo["timezone"] or "auto",
                    "start_date": s_clip.isoformat(),
                    "end_date": e_clip.isoformat(),
                },
            )
            r.raise_for_status()
            d = r.json().get("daily", {})
    except Exception as exc:
        return {
            "ok": False,
            "city": geo["name"],
            "country": geo["country"],
            "error": f"weather service unreachable: {exc.__class__.__name__}",
            "note": "Use general seasonal knowledge instead of a precise forecast.",
            "daily": [],
        }

    days = []
    for i, day in enumerate(d.get("time", [])):
        days.append(
            {
                "date": day,
                "t_max_c": d["temperature_2m_max"][i],
                "t_min_c": d["temperature_2m_min"][i],
                "precip_mm": d["precipitation_sum"][i],
                "wind_kmh": d["wind_speed_10m_max"][i],
                "weather_code": d["weather_code"][i],
            }
        )
    return {
        "ok": True,
        "city": geo["name"],
        "country": geo["country"],
        "latitude": geo["latitude"],
        "longitude": geo["longitude"],
        "daily": days,
    }


# Lightweight static FX fallback (USD per 1 unit) — used when the network
# call to exchangerate.host fails (e.g. Kaggle without internet).
_FX_FALLBACK_USD = {
    "USD": 1.0, "EUR": 1.08, "GBP": 1.27, "JPY": 0.0064, "CHF": 1.12,
    "AUD": 0.66, "CAD": 0.73, "CNY": 0.14, "INR": 0.012, "AED": 0.27,
    "TRY": 0.031, "BRL": 0.20, "MXN": 0.058, "ZAR": 0.054, "KRW": 0.00073,
    "SGD": 0.74, "HKD": 0.13, "SEK": 0.095, "NOK": 0.094, "DKK": 0.14,
    "PLN": 0.25, "RUB": 0.011, "THB": 0.028, "IDR": 0.000063, "MYR": 0.21,
}


def convert_currency(amount: float, source: str, target: str) -> dict[str, Any]:
    """Convert `amount` from `source` to `target`. Falls back to a static
    table if the public FX API is unreachable (Kaggle offline mode)."""
    source = (source or "").upper()
    target = (target or "").upper()
    if not source or not target:
        return {"ok": False, "error": "source/target currency required"}

    try:
        with _client() as c:
            r = c.get(
                f"{_FX_BASE}/convert",
                params={"from": source, "to": target, "amount": amount},
            )
            r.raise_for_status()
            data = r.json()
        if data.get("success") and data.get("result") is not None:
            return {
                "ok": True,
                "amount": amount,
                "from": source,
                "to": target,
                "rate": data.get("info", {}).get("rate"),
                "converted": data["result"],
                "source": "exchangerate.host",
            }
    except Exception:
        pass

    if source not in _FX_FALLBACK_USD or target not in _FX_FALLBACK_USD:
        return {
            "ok": False,
            "error": f"unsupported currency pair {source}->{target} in offline mode",
        }
    usd_amount = amount * _FX_FALLBACK_USD[source]
    converted = usd_amount / _FX_FALLBACK_USD[target]
    rate = _FX_FALLBACK_USD[source] / _FX_FALLBACK_USD[target]
    return {
        "ok": True,
        "amount": amount,
        "from": source,
        "to": target,
        "rate": round(rate, 6),
        "converted": round(converted, 2),
        "source": "offline-fallback-table",
    }
