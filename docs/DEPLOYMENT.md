# Deployment

This project ships the Flask API as a Docker container so the Chrome extension
and Electron app can reach it from anywhere.

## Local Docker build

```bash
docker build -t upwork-cover-letter-api:latest .
docker run -p 5000:5000 --env-file .env upwork-cover-letter-api:latest

curl http://localhost:5000/health
```

## Docker Compose

```bash
docker compose up -d --build
```

## SSH deploy script

Everything needed is packaged and sent to a remote host:

```bash
VPS_IP=203.0.113.10 VPS_USER=root ./deploy.sh
```

The script tests SSH, packages the app (excluding secrets and dev files),
transfers it, installs Docker if missing, builds the image and starts the
container. It also copies `.env.example` to `.env` on first run so you can add
your API keys, then re-run.

## Hardening notes

- **Never commit `.env`.** Keys are injected via `--env-file` / environment.
- **CORS** is open by default for development. Restrict origins in production,
  e.g. to your extension's ID.
- **HTTPS** — terminate TLS with a reverse proxy (Nginx/Caddy) in front of the
  container; do not expose port 5000 directly.
- **Rate limiting** — add `flask-limiter` if the endpoint is public.