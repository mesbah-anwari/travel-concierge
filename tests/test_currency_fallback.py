"""Tests for the offline currency fallback path (no internet required).

We deliberately point httpx at an invalid URL so the public FX call fails
and the static fallback table kicks in. This guarantees the test runs on
Kaggle's offline notebooks too.
"""
from __future__ import annotations

import travel_concierge.tools.travel_apis as api


def test_currency_fallback_when_api_down(monkeypatch):
    monkeypatch.setattr(api, "_FX_BASE", "http://127.0.0.1:1")  # unreachable
    r = api.convert_currency(100.0, "USD", "EUR")
    assert r["ok"] is True
    assert r["from"] == "USD" and r["to"] == "EUR"
    assert r["source"] == "offline-fallback-table"
    assert 50.0 < r["converted"] < 200.0  # sanity check


def test_currency_rejects_unknown_currency(monkeypatch):
    monkeypatch.setattr(api, "_FX_BASE", "http://127.0.0.1:1")
    r = api.convert_currency(100.0, "XXX", "EUR")
    assert r["ok"] is False
