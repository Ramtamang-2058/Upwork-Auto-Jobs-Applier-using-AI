"""Centralised configuration for the Upwork automation suite.

All settings live here so the rest of the codebase reads from a single source
of truth. Values can be overridden through environment variables.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class Config:
    # --- Paths --------------------------------------------------------------
    FILES_DIR = ROOT / "files"
    PROFILE_FILE = FILES_DIR / "profile.md"
    SCRAPED_JOBS_FILE = FILES_DIR / "upwork_job_listings.txt"
    COVER_LETTERS_FILE = FILES_DIR / "cover_letter.txt"
    LATEST_LETTER_FILE = FILES_DIR / "latest_cover_letter.txt"
    APPLICATION_LOG_FILE = FILES_DIR / "application_log.txt"
    APPLICATIONS_SENT_FILE = FILES_DIR / "applications_sent.json"

    # --- Monitor / handoff ----------------------------------------------------
    INBOX_FILE = FILES_DIR / "inbox_jobs.jsonl"        # jobs dropped in by client/browser
    MATCHES_FILE = FILES_DIR / "queue_matches.jsonl"   # strong matches awaiting a proposal
    EVENTS_LOG_FILE = FILES_DIR / "application_log.jsonl"  # every decision, structured
    SEEN_FILE = FILES_DIR / "monitor_seen.json"        # links already processed
    PROPOSALS_DIR = FILES_DIR / "proposals"            # captured Claude proposals
    CLAUDE_PROMPTS_DIR = FILES_DIR / "claude_prompts"  # ready-to-paste handoff prompts
    GUIDELINES_FILE = ROOT / "guidelines" / "apply.md"

    # --- Pipeline defaults --------------------------------------------------
    DEFAULT_JOB_TITLE = os.getenv("UPWORK_JOB_TITLE", "AI Agent Developer")
    DEFAULT_NUM_JOBS = int(os.getenv("UPWORK_NUM_JOBS", "10"))

    # --- LLM -------------------------------------------------------------------
    MODEL_CLASSIFIER = os.getenv("MODEL_CLASSIFIER", "gemini/gemini-2.5-flash-preview-05-20")
    MODEL_WRITER = os.getenv("MODEL_WRITER", "gemini/gemini-2.5-flash-preview-05-20")
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.1"))

    # --- API server ---------------------------------------------------------
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", "5000"))

    # --- Monitor --------------------------------------------------------------
    MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", "300"))  # seconds between passes
    DEFAULT_MIN_SCORE = int(os.getenv("MIN_MATCH_SCORE", "60"))

    # --- Profile / rate -------------------------------------------------------
    FREELANCER_NAME = os.getenv("FREELANCER_NAME", "Christopher")
    DEFAULT_RATE = os.getenv("UPWORK_DEFAULT_RATE", "$85.00")