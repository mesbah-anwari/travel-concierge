# Travel Concierge — Kaggle Capstone Writeup

> **Track:** Concierge Agents
> **Course:** 5-Day AI Agents: Intensive Vibe Coding with Google
> **Repo:** https://github.com/mesbah-anwari/travel-concierge
> **Demo notebook:** https://www.kaggle.com/code/anwarim/travel-concierge-kaggle-capstone-demo
> **Video walkthrough:** *(link to be added after recording — see `SUBMIT.md`)*

## 1. Problem & motivation

Planning a trip is one of the most common, time-consuming and high-stakes
personal tasks: dozens of tabs, conflicting blog posts, currency
conversions, weather checks, and last-minute repacks. The information is
public — but assembling it into a coherent, traveller-shaped plan is
where the friction lives. That makes it a textbook **concierge** use
case for AI agents.

## 2. Solution

Travel Concierge is a single command-line (and notebook) interface that
turns a one-sentence trip brief into a complete, opinionated plan:

- **Day-by-day itinerary** grouped geographically.
- **Daily weather forecast** with packing-relevant tips.
- **Local know-how** — etiquette, safety, transport, packing list.
- **Realistic budget** with per-category costs and FX-converted total.

Under the hood, a **coordinator agent** delegates to **four specialist
sub-agents**, all built with **Google ADK**. Two of those specialists
call a **custom MCP server** for real-world data (weather and currency).
Every input and output is filtered through a **four-layer security
guard**.

## 3. Course concepts demonstrated

The Capstone requires at least three concepts from the 5-day course. We
cover four:

### 3.1 Multi-agent system with Google ADK
The system is composed of five `google.adk.agents.Agent` instances:

- `travel_concierge` (root / coordinator)
- `itinerary_agent`
- `weather_agent`
- `budget_agent`
- `local_info_agent`

The coordinator's instruction explicitly describes the delegation order
and the output schema, so ADK handles the routing automatically through
its sub-agent dispatch.

### 3.2 Custom MCP server
`src/travel_concierge/mcp_server/server.py` runs a **FastMCP** server
that exposes three tools any MCP-aware client can call:

- `get_weather(city, start_date, end_date)`
- `convert_currency(amount, source, target)`
- `geocode_city(city)`

The server is launched with `python -m travel_concierge.mcp_server` and
communicates over stdio — the standard MCP transport, compatible with
Claude Desktop, GitHub Copilot CLI, and any ADK client that wires an
MCP toolset.

### 3.3 Agent skills / function tools
Each specialist is intentionally scoped to a tight skill:

| Agent | Tool(s) bound |
|---|---|
| `weather_agent` | `get_weather`, `geocode_city` |
| `budget_agent` | `convert_currency` |
| `itinerary_agent` | *(no tools — reasoning only)* |
| `local_info_agent` | *(no tools — reasoning only)* |

Tool signatures are plain typed Python functions (`src/travel_concierge/tools/function_tools.py`),
which ADK auto-converts into JSON schemas for the model.

### 3.4 Security features
Four guardrails live in `src/travel_concierge/security/guards.py` and
wrap every conversation turn:

1. **Input validation** — length, control-char and emptiness checks.
2. **Prompt-injection detection** — heuristic blocklist for jailbreaks,
   system-prompt leaks, "ignore previous instructions" patterns.
3. **PII redaction** — emails, phone numbers, SSNs, Luhn-valid credit
   cards, Google AI Studio keys, OpenAI keys. Runs on **every agent
   output** so even a compromised sub-agent can't leak credentials.
4. **Output safety filter** — blocks obvious disallowed content categories.

Secrets are env-only; `.env` is git-ignored; a `TRAVEL_CONCIERGE_INSECURE_SSL`
escape hatch exists for corporate networks but defaults to verifying.

The guards are covered by **14 unit tests** (`tests/test_security.py`
and `tests/test_currency_fallback.py`) that run without a network or
API key.

## 4. Architecture

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the mermaid flow + sequence
diagrams. In short:

```
User → Input Guard → Coordinator → [Itinerary | Weather → MCP
                                  | Local-Info | Budget → MCP]
                                  → Coordinator synthesis → Output Guard → User
```

## 5. Implementation highlights

- **Graceful offline mode.** Every external HTTP call is wrapped; on a
  network failure the FX call drops to a static rate table and the
  weather tool returns a structured "use seasonal knowledge" payload.
  This means the demo notebook still runs end-to-end inside Kaggle's
  occasionally-offline environment.
- **Notebook-friendly runner.** `runner.plan_trip()` detects an existing
  event loop (Jupyter / Kaggle) and reuses it via `nest_asyncio`, so the
  same code path works in CLI, scripts and notebooks.
- **Honest prompts.** Each specialist's instruction explicitly forbids
  inventing numbers (the budget agent must use the FX tool; the weather
  agent must use the forecast tool) and tells the coordinator to ask
  one consolidated follow-up if essential info is missing.

## 6. Real-world value

A traveller spending 2-4 hours assembling a trip plan can now get a
first-draft plan in **under 30 seconds** that is:

- coherent (the four sections reference each other),
- grounded (weather + FX numbers come from real APIs),
- safe by construction (PII never leaks, prompt-injection blocked),
- portable (the MCP server lets any AI client reuse the same tools).

## 7. What's next

- **Flight + hotel agent** that calls Amadeus / Skyscanner.
- **Visa & vaccination agent** wired to authoritative gov APIs.
- **Multimodal output** — generate a PDF travel pack with maps.
- **Memory / personalisation** — remember prior trips and dietary
  constraints via ADK's `Session` state.

## 8. Reproducibility

Anyone with a free Gemini API key can reproduce every screenshot in
this writeup:

```bash
git clone <repo>
cd travel-concierge
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # add GOOGLE_API_KEY
python main.py "Plan a 4-day food-focused trip to Bangkok for two in November, mid-range, home currency USD"
```

Or open `notebooks/kaggle_demo.ipynb` and run all cells.
