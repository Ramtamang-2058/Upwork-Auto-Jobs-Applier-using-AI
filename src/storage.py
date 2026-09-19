"""Persistence helpers: reading the profile and writing generated artifacts."""
import json
from datetime import datetime, timezone
from pathlib import Path

from .config import Config


def read_text_file(filename):
    """Read a UTF-8 text file, dropping empty lines and surrounding whitespace."""
    with open(filename, "r", encoding="utf-8") as file:
        lines = [line.strip() for line in file if line.strip()]
        return "".join(lines)


def read_profile(filename=None):
    """Return the freelancer profile as a single string."""
    return read_text_file(filename or Config.PROFILE_FILE)


def save_jobs_to_file(job_listings, filename=None):
    """Persist a list of job dicts in a human-readable plain-text format."""
    filename = Path(filename or Config.SCRAPED_JOBS_FILE)
    with open(filename, "w", encoding="utf-8") as file:
        for job in job_listings:
            file.write(f"Title: {job['title']}\n")
            file.write(f"Link: {job['link']}\n")
            file.write(f"Description: {job['description']}\n")
            file.write(f"Job Type: {job['job_type']}\n")
            file.write(f"Experience Level: {job['experience_level']}\n")
            file.write(f"Budget: {job['budget']}\n")
            file.write("\n---\n\n")


def append_cover_letter(letter, filename=None):
    """Append a generated cover letter to the output file."""
    filename = Path(filename or Config.COVER_LETTERS_FILE)
    with open(filename, "a", encoding="utf-8") as file:
        file.write(f"{letter}\n{'-' * 70}\n")


def save_latest_letter(letter, filename=None):
    """Overwrite the 'latest' letter file with a single letter."""
    filename = Path(filename or Config.LATEST_LETTER_FILE)
    with open(filename, "w", encoding="utf-8") as file:
        file.write(letter)


def log_application(job_data, letter, filename=None):
    """Append a human-readable application log entry."""
    filename = Path(filename or Config.APPLICATION_LOG_FILE)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with open(filename, "a", encoding="utf-8") as file:
        file.write(f"\n{'=' * 70}\n")
        file.write(f"Timestamp: {timestamp}\n")
        file.write(f"Job: {job_data.get('title', '')}\n")
        file.write(f"Budget: {job_data.get('budget', '')}\n")
        file.write(f"Generated: {letter}\n")
        file.write(f"{'=' * 70}\n")


def record_application(data, filename=None):
    """Append a structured application record (JSONL)."""
    filename = Path(filename or Config.APPLICATIONS_SENT_FILE)
    with open(filename, "a", encoding="utf-8") as file:
        file.write(json.dumps(data) + "\n")