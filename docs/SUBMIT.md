# How to submit to the Kaggle Capstone

> **Competition:** [AI Agents: Intensive Vibe Coding Capstone Project](https://www.kaggle.com/competitions/vibecoding-agents-capstone-project)
> **Deadline:** Jul 6, 2026 at 11:59 PM PT
> **Track for this project:** Concierge Agents

The Kaggle Capstone has four deliverables. This guide walks through each.

---

## ✅ Pre-flight checklist

- [ ] All tests pass: `pytest -q` shows **14 passed**.
- [ ] Smoke run works: `python main.py "Plan 3 days in Rome for a solo traveller, budget, history focus, home currency USD"` produces a full plan.
- [ ] `.env` is **NOT** committed (already in `.gitignore`).
- [ ] `README.md`, `docs/WRITEUP.md`, `docs/ARCHITECTURE.md` are up to date.

---

## 1. Push the code to a **public GitHub repo**

Kaggle requires a public codebase URL.

```powershell
cd c:\workspace\VibeCodingCapstoneProject
git init -b main
git add .
git status                       # confirm .env is NOT listed
git commit -m "Travel Concierge — Kaggle Capstone (Concierge Agents track)"

# Create an empty public repo on github.com first (no README/license/gitignore).
git remote add origin https://github.com/<your-username>/travel-concierge.git
git push -u origin main
```

If you'd rather use the GitHub CLI:
```powershell
gh repo create travel-concierge --public --source=. --remote=origin --push
```

After pushing, **open the repo URL in a private browser window** to
confirm it's actually public and the `.env` file is absent.

---

## 2. Create the **Kaggle Notebook** (demo)

1. Go to <https://www.kaggle.com/code> → **New Notebook**.
2. **File → Import Notebook**, upload `notebooks/kaggle_demo.ipynb`.
3. In the notebook sidebar:
   - **Settings → Accelerator:** None (CPU is enough — the LLM runs in Google's cloud).
   - **Settings → Internet:** **On** (required for Gemini + Open-Meteo).
   - **Add-ons → Secrets:** Add a secret named `GOOGLE_API_KEY` with your AI Studio key.
4. *(Optional but recommended)* Add this repo as a **Kaggle Dataset**
   so the notebook can `import` it without `pip install` magic:
   - Datasets → New Dataset → upload a zip of `src/` (or use the
     GitHub-import feature) → name it `travel-concierge`.
   - In the notebook: *Add Data → search "travel-concierge"*.
5. **Run All** to make sure every cell executes top-to-bottom.
6. **Save Version → Save & Run All (Commit)**. This produces a stable URL.

---

## 3. Record the **video demo** (≤ 3 minutes)

Suggested script:

| Time | Show | Say |
|---|---|---|
| 0:00–0:20 | README.md | "Travel Concierge — Concierge Agents track. Multi-agent ADK system + MCP server + security guards." |
| 0:20–0:50 | `docs/ARCHITECTURE.md` mermaid | "Coordinator delegates to 4 specialists; weather and budget call a custom MCP server; guards wrap every input/output." |
| 0:50–2:30 | Live CLI run with `python main.py "..."` | "One sentence in → a complete plan: itinerary, weather, local know-how, budget — synthesised by the coordinator." |
| 2:30–3:00 | `pytest -q` | "14 unit tests prove the security guards work — prompt-injection blocked, PII redacted, offline fallback covered." |

Record with **OBS Studio** (free), **Loom**, **Zoom**, or your OS recorder.
Upload to YouTube (Unlisted is fine) or Loom — copy the link.

---

## 4. File the **Kaggle Writeup**

1. Go to the competition page → **Writeups** tab → **New Writeup**.
2. Title: `Travel Concierge — Multi-Agent Trip Planner (Concierge Agents)`
3. Paste the content of `docs/WRITEUP.md`.
4. Replace the placeholder links:
   - **Repo:** your public GitHub URL (step 1)
   - **Demo notebook:** your committed Kaggle notebook URL (step 2)
   - **Video walkthrough:** your YouTube/Loom URL (step 3)
5. Pick the **Concierge Agents** track tag.
6. **Submit**.

---

## 5. Post-submission

- Watch the *Discussion* tab for judge questions.
- Star your own GitHub repo and share the writeup on LinkedIn/X with
  `#KaggleAIAgents` to maximise community visibility (top 3 per track
  get featured on Kaggle's social media).
- Winners are announced by end of July 2026.

Good luck! 🚀
