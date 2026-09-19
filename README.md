# Upwork Auto Jobs Applier

Automates the repetitive parts of applying to Upwork jobs: it scrapes job
listings, classifies them against your freelancer profile, and generates
personalised AI cover letters. A Flask API server exposes the same generation
engine to a Chrome extension and an Electron app.

Works with **two backends**:

- **LLM API** - the scrape/classify/generate pipeline via LiteLLM (needs a key).
- **No-API mode** - a keyless skill matcher + guidelines gate, with proposals
  written by Claude in your own Firefox tab (copy/paste handoff). You review
  and hit Send yourself. Fully offline and logged to `files/application_log.jsonl`.

> **Note**: automated scraping and auto-submission may violate Upwork's terms of
> service. Review generated letters before submitting, and use at your own risk.

## How it works

1. **Scrape** - pulls job listings for a search term (Selenium) or queue them
   from the browser (`POST /api/queue-job`).
2. **Score + gate** - the keyless matcher (`src/matcher.py`) scores each job
   against your `files/profile.md`; `src/eligibility.py` applies the rules in
   `guidelines/apply.md` (hiring status, proposal count, budget, match score).
3. **Write** - for LLM mode an agent drafts letters;
   in no-API mode `tools/upwork_monitor.py` and `tools/claude_handoff.py`
   prepare a pastable prompt for Claude in your browser.
4. **Review** - proposals accumulate in `files/proposals/` and the event log,
   and you submit them manually after a final read.

The generation engine builds on [LangGraph](https://github.com/langchain-ai/langgraph)
for the workflow and [LiteLLM](https://github.com/BerriAI/litellm) so you can
swap the underlying model (Gemini, Groq, OpenAI, ...) with a config change.

## Project structure

```
├── src/                  # core package
│   ├── agent.py          # LiteLLM wrapper
│   ├── config.py         # centralised settings (+ env overrides)
│   ├── cover_letter.py   # classifier + writer services
│   ├── eligibility.py    # guidelines gate (guidelines/apply.md)
│   ├── graph.py          # LangGraph pipeline
│   ├── handoff.py        # Claude clipboard handoff (no API key)
│   ├── matcher.py        # keyless profile skill matcher
│   ├── prompts.py        # prompt templates
│   ├── scraper.py        # Selenium Upwork scraper
│   └── storage.py        # file I/O + JSONL logging
├── server.py             # Flask API for the extension / Electron app
├── main.py               # CLI pipeline entry point
├── guidelines/apply.md   # eligibility rules you edit
├── tools/
│   ├── paste_job.py      # paste-a-job CLI (LLM mode)
│   ├── claude_handoff.py # one-shot no-API proposal handoff
│   └── upwork_monitor.py # scheduled monitor + gating
├── chrome-extension/     # browser extension
├── electron-app/         # desktop app
├── files/                # user data (profile.md, generated letters)
├── tests/                # unit tests (no API keys required)
└── docs/                 # setup, strategy, architecture, deployment
```

See `docs/ARCHITECTURE.md` for details.

## Getting started

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# configure your API key(s)
cp .env.example .env
# edit .env, then add your profile to files/profile.md
```

### No-API mode (recommended)

```bash
# 1. queue jobs while browsing Upwork (bookmarklet/extension POST /api/queue-job)
python server.py

# 2. watch for strong matches and stage handoff prompts
python tools/upwork_monitor.py --interval 300

# or one-shot, interactive: paste a job, get a Claude prompt
python tools/claude_handoff.py
```

The gate reads `guidelines/apply.md` - edit it to control which jobs get
drafted for. Every decision lands in `files/application_log.jsonl`.

### Run the full pipeline

```bash
python main.py
python main.py --job-title "LangChain Developer" --num-jobs 15
```

### Generate a letter by pasting a job description

```bash
python tools/paste_job.py
```

### Run the API server (for extension / Electron app)

```bash
python server.py
curl http://localhost:5000/health
```

### Tests

```bash
python -m pytest
```

## Configuration

All settings live in `src/config.py` and can be overridden via environment
variables (see `.env.example`):

| Variable             | Default                                  | Purpose                    |
|----------------------|------------------------------------------|----------------------------|
| `MODEL_WRITER`       | `gemini/gemini-2.5-flash-preview-05-20`  | cover letter model         |
| `MODEL_CLASSIFIER`   | `gemini/gemini-2.5-flash-preview-05-20`  | job classifier model       |
| `LLM_TEMPERATURE`    | `0.1`                                    | sampling temperature       |
| `UPWORK_JOB_TITLE`   | `AI Agent Developer`                     | default search term        |
| `UPWORK_NUM_JOBS`    | `10`                                     | default listings to scrape |
| `UPWORK_DEFAULT_RATE`| `$85.00`                                 | fallback suggested rate    |
| `SERVER_HOST`/`PORT` | `0.0.0.0` / `5000`                       | API server binding         |
| `MONITOR_INTERVAL`   | `300`                                     | seconds between passes     |
| `MIN_MATCH_SCORE`    | `60`                                      | default eligibility floor  |
| `FREELANCER_NAME`    | `Christopher`                             | sign-off in proposals      |

## API

| Method | Path                         | Description                        |
|--------|------------------------------|------------------------------------|
| GET    | `/health`                    | health check                       |
| GET    | `/api`                       | endpoint overview                  |
| POST   | `/api/generate-cover-letter` | body: `{title, description, budget, ...}` |
| POST   | `/api/queue-job`             | drop a job into the monitor inbox  |
| POST   | `/api/log-application`       | record a submitted application     |

## Clients

- **Chrome extension** - `chrome-extension/README.md`
- **Electron app** - `electron-app/README.md`
- **Bookmarklet** - `upwork_bookmarklet.js` (install as a browser bookmark URL)

## Deployment

Venv-only (no Docker). See `docs/DEPLOYMENT.md` - local run, the optional
gunicorn setup for a VPS, and how the monitor/handoff tools fit in.

## License

MIT (see `electron-app/package.json`). Part of the Upwork Auto Jobs Applier
project.