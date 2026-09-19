# Architecture

The project is split into three layers: a reusable **core package** (`src/`), a
thin **API server** (`server.py`) that the browser extension / Electron app talk
to, and **CLI entry points** (`main.py`, `tools/`) for interactive use.

```
┌─────────────────────────────┐    ┌──────────────────────────────┐
│  Chrome extension           │    │  Electron app / bookmarklet  │
└──────────────┬──────────────┘    └──────────────┬───────────────┘
               │  HTTP (JSON)                     │  HTTP (JSON)
               └────────────────┬─────────────────┘
                                ▼
                       ┌────────────────┐
                       │    server.py   │  Flask API
                       └───────┬────────┘
                               │
┌────────────────── Core package (src/) ──────────────────┐
│                                                          │
│  config.py      single source of truth for settings      │
│  agent.py       LiteLLM wrapper                           │
│  cover_letter.py JobClassifier + CoverLetterGenerator     │
│  prompts.py     prompt templates                          │
│  scraper.py     Selenium job scraper                      │
│  storage.py     file I/O (profile, letters, logs)         │
│  graph.py       LangGraph pipeline                        │
└──────────────────────────────────────────────────────────┘
```

## Modules

- **`src/config.py`** — All settings (model ids, file paths, server host/port,
  pipeline defaults) live here, overridable through environment variables.
- **`src/agent.py`** — A stateless wrapper around LiteLLM's `completion()`.
- **`src/cover_letter.py`** — Wires an `Agent` to a prompt template and
  normalises the LLM's JSON response (strips ``` fences, tolerates malformed
  JSON). Both the pipeline and the API server reuse these classes, so response
  handling logic lives in exactly one place.
- **`src/prompts.py`** — The job-classification and cover-letter prompt
  templates, with the freelancer profile injected at runtime.
- **`src/scraper.py`** — Selenium-based Upwork scraper. Isolated selectors so
  Upwork DOM changes only require editing this one file.
- **`src/storage.py`** — All file persistence: profile reading, job listing,
  cover-letter and application-log writes.
- **`src/graph.py`** — The LangGraph workflow:
  *scrape → classify → [no matches → end] → generate → save → repeat*.

## API

`server.py` exposes:

| Method | Path                         | Purpose                                  |
|--------|------------------------------|------------------------------------------|
| GET    | `/health`                    | Health check                              |
| GET    | `/api`                       | Endpoint overview                         |
| POST   | `/api/generate-cover-letter` | Generate a cover letter from a job dict   |
| POST   | `/api/log-application`       | Record a submitted application            |

The server shares the same `CoverLetterGenerator` used by the CLI, so behaviour
is consistent across every client.

## Entry points

- `python main.py` — full scrape → classify → generate pipeline.
- `python server.py` — Flask API server.
- `python tools/paste_job.py` — paste a job description, get a cover letter.
- `python -m pytest` — unit tests (no API keys or network needed).