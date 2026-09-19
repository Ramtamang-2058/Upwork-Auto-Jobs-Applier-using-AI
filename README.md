# Upwork Auto Jobs Applier using AI

Automates the repetitive parts of applying to Upwork jobs: it scrapes job
listings, classifies them against your freelancer profile, and generates
personalised AI cover letters. A Flask API server exposes the same generation
engine to a Chrome extension and an Electron app.

> **Note**: automated scraping and auto-submission may violate Upwork's terms of
> service. Review generated letters before submitting, and use at your own risk.

## How it works

1. **Scrape** - pulls job listings for a search term (Selenium).
2. **Classify** - an LLM agent ranks listings against your `files/profile.md`.
3. **Generate** - a writer agent produces a personalised cover letter per match.
4. **Review** - letters accumulate in `files/cover_letter.txt` for review
   before you submit them manually.

The generation engine builds on [LangGraph](https://github.com/langchain-ai/langgraph)
for the workflow and [LiteLLM](https://github.com/BerriAI/litellm) so you can
swap the underlying model (Gemini, Groq, OpenAI, ...) with a config change.

## Project structure

```
├── src/                  # core package
│   ├── agent.py          # LiteLLM wrapper
│   ├── config.py         # centralised settings (+ env overrides)
│   ├── cover_letter.py   # classifier + writer services
│   ├── graph.py          # LangGraph pipeline
│   ├── prompts.py        # prompt templates
│   ├── scraper.py        # Selenium Upwork scraper
│   └── storage.py        # file I/O helpers
├── server.py             # Flask API for the extension / Electron app
├── main.py               # CLI pipeline entry point
├── tools/paste_job.py    # paste-a-job CLI
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

## API

| Method | Path                         | Description                        |
|--------|------------------------------|------------------------------------|
| GET    | `/health`                    | health check                       |
| GET    | `/api`                       | endpoint overview                  |
| POST   | `/api/generate-cover-letter` | body: `{title, description, budget, ...}` |
| POST   | `/api/log-application`       | record a submitted application     |

## Clients

- **Chrome extension** - `chrome-extension/README.md`
- **Electron app** - `electron-app/README.md`
- **Bookmarklet** - `upwork_bookmarklet.js` (install as a browser bookmark URL)

## Deployment

See `docs/DEPLOYMENT.md` - Docker image, `docker compose`, or the `deploy.sh`
SSH deploy script.

## License

MIT (see `electron-app/package.json`). Part of the Upwork Auto Jobs Applier
project.