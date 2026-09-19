# Running the API server (no Docker)

The project runs in a plain Python virtual environment - no container needed.
Works on your workstation and on a small VPS alike.

## Local run

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add GEMINI_API_KEY if you use the LLM endpoints
python server.py              # http://localhost:5000
```

The server starts without an API key or `files/profile.md`. LLM-based endpoints
(`/api/generate-cover-letter`) will fail until a key is configured; the monitor
endpoints (`/api/queue-job`, `/api/log-application`) and the health/overview
routes always work.

## Optional: run monitor + scheduler

```bash
python tools/upwork_monitor.py --interval 600     # check for queued jobs
```

See `docs/SETUP.md` for the full manual workflow (queue jobs from the browser,
paste them into Claude, submit proposals yourself).

## Headless VPS

The default `server.py` uses Flask's dev server, which is fine for a single
user hitting it from your own browser/extension. If you want gunicorn on a VPS:

```bash
source venv/bin/activate && pip install gunicorn
gunicorn --bind 0.0.0.0:5000 server:app
```

Put it behind your VPS firewall / a reverse proxy if you expose it publicly.
`SERVER_HOST`/`SERVER_PORT` in `.env` control the bind address for `python server.py`.