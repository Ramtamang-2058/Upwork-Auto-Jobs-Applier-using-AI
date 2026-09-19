"""Keyless skill matching: score a job against the freelancer profile.

This requires no LLM/API key - it counts how many meaningful terms from the
profile appear in the job's title/description/skills. It is fast, deterministic
and used by the monitor to pre-filter jobs before a proposal is written.
"""
import re
from collections import Counter

from .storage import read_profile

_STOPWORDS = {
    "about", "after", "also", "been", "being", "best", "but", "can", "could",
    "don't", "from", "good", "have", "having", "here", "into", "just", "like",
    "more", "most", "much", "must", "need", "never", "only", "other", "our",
    "over", "really", "should", "some", "such", "than", "that", "their",
    "them", "then", "there", "these", "they", "this", "those", "through",
    "very", "were", "when", "where", "which", "will", "with", "would", "your",
    "years", "experience", "project", "working", "looking", "client",
}

_TOKEN_RE = re.compile(r"[a-z][a-z0-9+#.-]{2,}")


def tokenize(text):
    """Lower-case token list with stopwords removed."""
    tokens = _TOKEN_RE.findall(text.lower())
    return [t for t in tokens if t not in _STOPWORDS]


def profile_terms(profile_text):
    """Distinct meaningful terms extracted from the profile."""
    return set(tokenize(profile_text))


def _job_haystack(job):
    parts = [
        job.get("title", ""),
        job.get("description", ""),
        job.get("skills", ""),
    ]
    if isinstance(job.get("skills"), list):
        parts[2] = " ".join(job["skills"])
    return " ".join(str(p) for p in parts if p)


def score_job(job, profile_text=None):
    """Return a match score 0-100 for a job dict against the profile.

    Metric: share of the job's meaningful tokens that appear in the profile,
    boosted +15 (capped at 100) when the title hits a profile term. A job
    written in the same vocabulary as the profile scores high; an unrelated
    job scores near zero.
    """
    profile_text = profile_text or read_profile()
    terms = profile_terms(profile_text)
    if not terms:
        return 50

    job_tokens = set(tokenize(_job_haystack(job)))
    if not job_tokens:
        return 0

    matched = job_tokens & terms
    base = int(100 * len(matched) / len(job_tokens))

    title = (job.get("title") or "").lower()
    if any(term in title for term in terms):
        base = min(100, base + 15)

    return base


def top_skill_terms(profile_text, limit=8, min_len=4):
    """Most common profile terms, for display/logging."""
    return Counter(tokenize(profile_text)).most_common(limit)