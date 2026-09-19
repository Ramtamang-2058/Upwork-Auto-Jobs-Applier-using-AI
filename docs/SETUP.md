# Setup Guide

## Prerequisites

- Python 3.9+
- An LLM provider key accepted by [LiteLLM](https://docs.litellm.ai/)
  (e.g. a Gemini API key for the default models).

## Installation

```bash
git clone git@github.com:Ramtamang-2058/Upwork-Auto-Jobs-Applier-using-AI.git
cd Upwork-Auto-Jobs-Applier-using-AI

python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Create a `.env` file (copy `.env.example`) and add your API key:

```env
GEMINI_API_KEY=your_gemini_key
```

Add your freelancer profile to `files/profile.md`.

## Ways to generate cover letters

### 1. Full pipeline (scrape + classify + generate)

```bash
python main.py
python main.py --job-title "LangChain Developer" --num-jobs 15
```

Job listings are saved to `files/upwork_job_listings.txt` and every generated
letter is appended to `files/cover_letter.txt`.

### 2. Paste a job description

```bash
python tools/paste_job.py
```

Paste a job description, press Enter twice, and the letter is written to
`files/latest_cover_letter.txt` and copied to your clipboard.

### 3. API server (for the Chrome extension / Electron app)

```bash
python server.py
```

Then load `chrome-extension/` as an unpacked extension (`chrome://extensions` →
Developer mode → Load unpacked) and point `content.js`'s `API_URL` at your
server. See `chrome-extension/README.md` and `electron-app/README.md`.

## Running the tests

```bash
python -m pytest
```

Tests are self-contained and require neither API keys nor a network connection.