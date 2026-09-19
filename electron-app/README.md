# Upwork Cover Letter Generator - Electron App

Desktop app that uses Puppeteer (with anti-detection plugins) to open Upwork,
lets you log in, extracts the current job and generates a cover letter through
the Python API server.

## Prerequisites

- Node.js 18+
- Python 3.9+ with the project's virtual environment set up

## Install

```bash
cd electron-app
npm install
```

## Usage

1. Start the API server from the project root:

   ```bash
   source venv/bin/activate
   python server.py
   ```

2. Launch the app:

   ```bash
   npm start
   ```

3. Enter a search query and click **Launch Browser**.
4. Log in to Upwork in the browser window that opens and navigate to a job page.
5. Click **Extract & Generate** - the cover letter appears and is copied to the
   clipboard.

## Controls

- **Launch Browser** - opens Puppeteer with stealth settings
- **Extract & Generate** - extracts the current job and generates a letter
- **Close Browser** - closes the automation browser
- **Copy to Clipboard** - copies the generated letter

## Building installers

```bash
npm run build-mac     # .app / .dmg
npm run build-win     # .exe installer
npm run build-linux   # .AppImage / .deb
```

## Configuration

- **AI model**: set `MODEL_WRITER` in the `.env` file (see `.env.example`)
  instead of editing server code.
- **API server**: `PYTHON_SERVER` in `main.js` defaults to
  `http://localhost:5000`.

## Troubleshooting

- **"Cannot connect to Python server"**: make sure `server.py` is running on
  port 5000.
- **Browser doesn't launch**: confirm Chrome/Chromium is installed.
- **Bot detection**: stealth mode is not guaranteed; logging in manually first
  improves reliability. The Chrome extension is a lower-risk alternative.

## Alternatives

1. **Chrome extension** (see `../chrome-extension/`) - zero automation risk.
2. **Paste tool** - `python tools/paste_job.py` with a copied job description.