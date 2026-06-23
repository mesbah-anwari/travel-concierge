# ✈️ Travel Concierge — Kaggle Capstone Project

**Track:** Concierge Agents
**Course:** 5-Day AI Agents: Intensive Vibe Coding with Google
**Capstone:** [AI Agents: Intensive Vibe Coding Capstone Project](https://www.kaggle.com/competitions/vibecoding-agents-capstone-project)

Travel Concierge is a **multi-agent personal trip planner** built with
**Google ADK**. A coordinator orchestrates four specialist agents (itinerary,
weather, budget, local-info) that share tools through a **custom MCP server**.
Every user input and agent output flows through a **security guard layer**
(validation, prompt-injection detection, PII redaction, content safety).

> *"Plan a 5-day trip to Lisbon in mid-July for a couple, mid-range budget,
> food + history focus, home currency EUR"* → a complete trip plan with day-by-day
> itinerary, daily weather forecast, cultural know-how, packing list, and a
> currency-converted budget.

---

## Course concepts demonstrated (≥3 required → 4 covered)

| # | Concept | Where it lives |
|---|---------|----------------|
| 1 | **Multi-agent system with ADK**       | `src/travel_concierge/agents/` — 1 coordinator + 4 specialists |
| 2 | **MCP server**                        | `src/travel_concierge/mcp_server/server.py` (fastmcp) — 3 tools |
| 3 | **Agent skills / function tools**     | `src/travel_concierge/tools/function_tools.py` — typed tools per agent |
| 4 | **Security features**                 | `src/travel_concierge/security/guards.py` — 4 guardrails, 14 unit tests |

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for the architecture
diagram and [`docs/WRITEUP.md`](docs/WRITEUP.md) for the full Kaggle writeup.

---

## Quick start

### 1. Prerequisites
- Python ≥ 3.10
- A free Google AI Studio API key — https://aistudio.google.com/apikey

### 2. Install
```powershell
git clone <your-fork-url> travel-concierge
cd travel-concierge
python -m venv .venv
.\.venv\Scripts\Activate.ps1            # Windows
# source .venv/bin/activate              # macOS / Linux
pip install -r requirements.txt
```

### 3. Configure
```powershell
copy .env.example .env
# open .env and paste your GOOGLE_API_KEY
```

### 4. Run

> ⚠️ **Make sure you use the virtual-env Python** — that's where all the
> dependencies (`google-adk`, `fastmcp`, …) were installed.
> Either activate it (`.\.venv\Scripts\Activate.ps1`) or call its
> interpreter directly: `.\.venv\Scripts\python.exe main.py …`.

**CLI** (single-shot):
```powershell
.\.venv\Scripts\python.exe main.py "Plan a 5-day trip to Lisbon in mid-July for a couple, mid-range budget, food + history, home currency EUR"
```

**CLI** (interactive):
```powershell
.\.venv\Scripts\python.exe main.py
```

**Standalone MCP server** (for Claude Desktop, ADK clients, Copilot CLI):
```powershell
.\.venv\Scripts\python.exe run_mcp_server.py
```

**Kaggle notebook demo:** open [`notebooks/kaggle_demo.ipynb`](notebooks/kaggle_demo.ipynb).

### 5. Tests
```powershell
.\.venv\Scripts\python.exe -m pytest -q
```
14 unit tests cover the security guards and the offline-mode currency
fallback — no API key required to run them.

---

## Project layout

```
src/travel_concierge/
├── agents/
│   ├── coordinator.py        # root agent (delegates to specialists)
│   ├── itinerary_agent.py
│   ├── weather_agent.py
│   ├── budget_agent.py
│   └── local_info_agent.py
├── mcp_server/
│   ├── server.py             # FastMCP server exposing 3 tools
│   └── __main__.py
├── security/
│   └── guards.py             # input validation, injection guard, PII, safety
├── tools/
│   ├── travel_apis.py        # Open-Meteo + exchangerate.host wrappers
│   └── function_tools.py     # ADK-shaped tool surface
├── config.py                 # env loading, model selection
├── runner.py                 # asyncio runner that wires guards + agents
└── __main__.py               # CLI
tests/
├── test_security.py
└── test_currency_fallback.py
notebooks/
└── kaggle_demo.ipynb         # end-to-end demo for Kaggle judges
docs/
├── ARCHITECTURE.md
├── WRITEUP.md
└── SUBMIT.md                 # step-by-step Kaggle submission guide
```

---

## Security model

| Layer | What it does | File |
|---|---|---|
| Input validation | Length + control-char + emptiness checks | `security/guards.py::validate_user_input` |
| Prompt-injection guard | Heuristic block of jailbreak/system-prompt-leak attempts | `security/guards.py::detect_prompt_injection` |
| PII redaction | Email, phone, SSN, Luhn-valid credit cards, Google/OpenAI API keys | `security/guards.py::redact_pii` |
| Output safety filter | Blocks obvious unsafe content categories | `security/guards.py::is_unsafe_output` |

Secrets are **never** committed: `.env` is git-ignored and all keys come
from environment variables. The `redact_pii` step runs on every agent
response so that a buggy or jailbroken sub-agent can't accidentally leak
credentials.

---

## License
MIT — see [`LICENSE`](LICENSE).
