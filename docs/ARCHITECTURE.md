# Architecture

## High-level overview

```mermaid
flowchart TD
    U[👤 User] -->|trip request| G1[🛡️ Input Guard<br/>validate + injection check]
    G1 -->|allowed| C[🧭 Coordinator Agent<br/>travel_concierge<br/>Gemini 2.5 Flash]

    C --> A1[📅 Itinerary Agent]
    C --> A2[☀️ Weather Agent]
    C --> A3[🏛️ Local-Info Agent]
    C --> A4[💰 Budget Agent]

    A2 -->|get_weather<br/>geocode_city| M[(🔌 MCP Server<br/>travel-concierge-tools)]
    A4 -->|convert_currency| M

    M -->|HTTPS| W[Open-Meteo<br/>geocode + forecast]
    M -->|HTTPS| F[exchangerate.host<br/>FX rates]
    M -.->|offline fallback| OFF[(Static FX table)]

    A1 --> C
    A2 --> C
    A3 --> C
    A4 --> C

    C -->|synthesised plan| G2[🛡️ Output Guard<br/>PII redact + safety filter]
    G2 -->|safe markdown| U
```

## Why this design

- **Coordinator + specialists** keeps each prompt tight, lets sub-agents
  reason in parallel and makes it easy to add new specialists (e.g. a
  Visa Agent or Flight Agent) later without touching the others.
- **MCP server** is the contract layer between the LLM agents and the
  outside world. Any MCP-aware client (Claude Desktop, GitHub Copilot
  CLI, another ADK app) can plug in and reuse the same tools.
- **Guards run on both sides** of the agent loop, so a compromised
  sub-agent can't leak secrets and a malicious user can't easily smuggle
  jailbreak instructions through.
- **Graceful offline mode** — every external call is wrapped; on network
  failure the agents still produce a useful (if less precise) answer,
  which is essential for Kaggle's offline-notebook judging environment.

## Component reference

| Component | Type | Purpose | File |
|---|---|---|---|
| `travel_concierge` | ADK `Agent` (root) | Orchestrates sub-agents and synthesises the final response | `agents/coordinator.py` |
| `itinerary_agent` | ADK `Agent` | Builds day-by-day plan from interests + duration | `agents/itinerary_agent.py` |
| `weather_agent` | ADK `Agent` + tools | Forecasts weather for the trip dates | `agents/weather_agent.py` |
| `budget_agent` | ADK `Agent` + tools | Per-category cost estimate + FX conversion | `agents/budget_agent.py` |
| `local_info_agent` | ADK `Agent` | Culture, etiquette, safety, packing list | `agents/local_info_agent.py` |
| `travel-concierge-tools` | MCP server (fastmcp) | Exposes `get_weather`, `convert_currency`, `geocode_city` | `mcp_server/server.py` |
| `guards` | Pure-Python module | 4 guardrails wrapping every input/output | `security/guards.py` |
| `runner` | asyncio wrapper | Wires guards → ADK Runner → final markdown | `runner.py` |

## Sequence of a request

```mermaid
sequenceDiagram
    actor U as User
    participant G as Guards
    participant C as Coordinator
    participant I as Itinerary
    participant W as Weather
    participant L as Local-Info
    participant B as Budget
    participant M as MCP Server

    U->>G: "Plan 5 days in Lisbon..."
    G->>G: validate + injection-check
    G->>C: cleaned prompt
    C->>I: build itinerary
    I-->>C: day-by-day plan
    C->>W: forecast for dates
    W->>M: get_weather()
    M-->>W: daily JSON
    W-->>C: weather summary
    C->>L: culture + packing
    L-->>C: local brief
    C->>B: estimate cost
    B->>M: convert_currency()
    M-->>B: FX result
    B-->>C: budget table
    C->>C: synthesise final markdown
    C-->>G: response
    G->>G: PII redact + safety filter
    G-->>U: ✈️ Your trip to Lisbon...
```
