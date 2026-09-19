"""Unified Flask API server for the Upwork Cover Letter Generator.

Endpoints:
    GET  /health                 health check
    GET  /api                    API overview
    POST /api/generate-cover-letter   generate a cover letter for a job
    POST /api/log-application    record a submitted application

Used by the Chrome extension, the Electron app and the browser bookmarklet.
"""
import re

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

from src.config import Config
from src.cover_letter import CoverLetterGenerator
from src.storage import append_cover_letter, log_application, record_application

load_dotenv()

app = Flask(__name__)
CORS(app)

generator = CoverLetterGenerator()
jobs_processed = 0


def extract_rate_suggestion(budget_str):
    """Guess a sensible bid rate from a budget string."""
    budget_lower = (budget_str or "").lower()

    if "hr" in budget_lower or "hourly" in budget_lower:
        numbers = re.findall(r"\$(\d+)", budget_str)
        if numbers:
            return f"${numbers[-1]}.00"
        return Config.DEFAULT_RATE

    if "fixed" in budget_lower:
        numbers = re.findall(r"\$[\d,]+", budget_str)
        if numbers:
            return numbers[0]

    return Config.DEFAULT_RATE


@app.get("/health")
def health():
    return jsonify(
        status="ok",
        message="Upwork cover letter API is running",
        jobs_processed=jobs_processed,
    )


@app.get("/api")
def api_overview():
    return jsonify(
        endpoints={
            "health": "/health",
            "generate-cover-letter": "/api/generate-cover-letter",
            "log-application": "/api/log-application",
        },
        success=True,
    )


@app.post("/api/generate-cover-letter")
def generate_cover_letter():
    global jobs_processed

    job_data = request.get_json(silent=True) or {}
    if not job_data.get("description"):
        return jsonify(error="Missing job description"), 400

    try:
        letter = generator.generate(_format_job_description(job_data))
    except Exception as exc:
        return jsonify(error=str(exc), message="Failed to generate cover letter"), 500

    append_cover_letter(letter)
    jobs_processed += 1

    return jsonify(
        success=True,
        cover_letter=letter,
        suggested_rate=extract_rate_suggestion(job_data.get("budget", "")),
        job_title=job_data.get("title", ""),
        length=len(letter),
        jobs_processed=jobs_processed,
    )


@app.post("/api/log-application")
def track_application():
    data = request.get_json(silent=True) or {}
    record_application(data)
    return jsonify(success=True)


def _format_job_description(job_data):
    """Render job dict fields into a single block of text for the LLM."""
    parts = [job_data.get("title", ""), job_data.get("description", "")]

    for field in ("budget", "experience_level", "job_type", "client_info"):
        if job_data.get(field):
            parts.append(f"{field.replace('_', ' ').title()}: {job_data[field]}")

    return "\n\n".join(part for part in parts if part)


if __name__ == "__main__":
    print("Upwork cover letter API starting...")
    print(f"  http://localhost:{Config.SERVER_PORT}")
    app.run(host=Config.SERVER_HOST, port=Config.SERVER_PORT, debug=False)