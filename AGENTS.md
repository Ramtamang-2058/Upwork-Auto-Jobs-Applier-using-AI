# AGENTS.md

Python project that automates Upwork job applications: scrapes job listings, classifies them against `files/profile.md`, and generates AI cover letters via LiteLLM. Exposes a Flask API for a Chrome extension, Electron app, and bookmarklet.

## Commands

- Setup requires a venv — system pip is PEP-668 externally-managed on this machine:
  `python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt`
- Tests (offline, no API keys/network — agents are mocked): `python -m pytest tests/ -q`
- Pipeline (LLM mode): `python main.py --job-title "LangChain Developer" --num-jobs 15`
- No-API monitor (uses keyless matcher + guidelines gate): `python tools/upwork_monitor.py --interval 300`; one-shot handoff: `python tools/claude_handoff.py`
- API server: `python server.py` (default `0.0.0.0:5000`)
- Paste-a-job CLI: `python tools/paste_job.py`
- No linter/formatter/CI exist. Verify changes with `python -m pytest` + `python -m py_compile`.
- Always run from the repo root.

## Architecture (not obvious from filenames)

- `src/cover_letter.py` is the single place LLM JSON responses are parsed (`strip_json_fences` / `parse_json_payload`). CLI (`tools/`), pipeline (`src/graph.py`), and server all reuse `CoverLetterGenerator`/`JobClassifier` — never add ad-hoc JSON/markdown-fence parsing elsewhere.
- `src/config.py` is the single source of truth; overridden via env (see `.env.example`: `MODEL_WRITER`, `MODEL_CLASSIFIER`, `LLM_TEMPERATURE`, `UPWORK_JOB_TITLE`, etc.). Change models by env/config, not by editing prompts or entrypoints.
- `server.py` builds `CoverLetterGenerator()` lazily on first `/api/generate-cover-letter` call, so the server boots fine without a key or `files/profile.md`.
- LangGraph flow in `src/graph.py`: scrape → classify → (no matches → done) → generate → save → repeat per match. `check_for_job_matches` returns a route string, not state.
- Clients (extension/Electron/bookmarklet) all POST to `/api/generate-cover-letter`; `chrome-extension/content.js` `API_URL` is the one knob that points them at the server.

## Gotchas

- LLM entrypoints (`main.py`, `tools/paste_job.py`) need a provider key (copy `.env.example` → `.env`, add `GEMINI_API_KEY`) and `files/profile.md`; the LLM cover-letter endpoint fails at runtime without a key. The no-API monitor/handoff flow and `/api/queue-job` never touch the LLM.
- Upwork scraping is unreliable: login walls and anti-bot often return 0 jobs. 0 results ≠ broken code. All selectors are isolated in `src/scraper.py` — when Upwork changes its DOM, edit there only.
- No Docker. Run everything in a venv (see `docs/DEPLOYMENT.md`; gunicorn `server:app` only if you want it on a VPS).
- The repo supports a **no-API-key mode**: `src/matcher.py` (keyless scoring) + `src/eligibility.py` (reads `guidelines/apply.md`) + `src/handoff.py` (Claude clipboard handoff) power `tools/upwork_monitor.py`. The user runs Claude in their own Firefox tab; AGENTS must not invent new "send" automations — humans submit.
- All generated outputs (`files/*.txt`, `files/*.json`, `files/*.jsonl`, `files/proposals/`, `files/claude_prompts/`) are gitignored — don't commit them. `files/profile.md` and `guidelines/apply.md` are tracked; profile.md contains real personal data; edit/commit it cautiously.