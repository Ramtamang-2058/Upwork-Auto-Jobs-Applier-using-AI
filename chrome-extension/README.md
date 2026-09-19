# Upwork Cover Letter Generator - Chrome Extension

Chrome extension that generates personalised cover letters while you browse
Upwork jobs. It extracts the job details from the page, sends them to the
Python API server, and copies the resulting letter to your clipboard.

## Installation

### 1. Start the API server

```bash
# From the project root
source venv/bin/activate
python server.py
```

The server runs on `http://localhost:5000`.

### 2. Load the extension

1. Open Chrome and go to `chrome://extensions/`
2. Enable **Developer mode**
3. Click **Load unpacked** and select the `chrome-extension` folder

## Usage

1. Make sure `server.py` is running
2. Log in to Upwork and open any job page (`/jobs/...`)
3. Click the floating **Generate Cover Letter** button (bottom right)
4. Wait 2-5 seconds - the letter is copied to your clipboard
5. Paste it into Upwork's cover letter field and apply

## Configuration

`content.js` defines the API endpoint:

```js
const API_URL = 'http://localhost:5000';   // development
// const API_URL = 'https://api.yourdomain.com';  // production
```

Check the popup (click the extension icon) to see server status and the latest
generated letter.

## Troubleshooting

- **Button doesn't appear**: make sure you're on a job page and refresh.
- **"Cannot connect to server"**: confirm `server.py` is running on port 5000
  and that `API_URL` points at it.
- **Letter not copying**: check browser clipboard permissions, or copy the
  letter from the popup.

## Files

```
chrome-extension/
├── manifest.json      # Extension configuration
├── content.js         # Runs on Upwork pages (extraction + button)
├── background.js      # Background service worker (notifications)
├── popup.html         # Extension popup UI
├── popup.js           # Popup logic (server status, latest letter)
├── styles.css         # Button and notification styles
└── README.md          # This file
```

See `../docs/DEPLOYMENT.md` for running the backend (venv, no Docker required).