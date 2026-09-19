"""Clipboard handoff to Claude in the user's browser.

This flow works with **no API key**: OpenCode prepares a well-formed prompt
(job + profile + output format), copies it to the clipboard, you paste it into
Claude in Firefox, copy the proposal back, and the tool captures+saves+logs it.
"""
import re
from datetime import datetime, timezone
from pathlib import Path

from .config import Config
from .storage import append_event, append_jsonl, ensure_dir, read_profile

PROPOSAL_FORMAT = """\
# OUTPUT FORMAT (follow exactly)

1. First line: "Hi," then a hook referencing something SPECIFIC from their job post.
   Do not open with your name or a generic greeting like "Hey"/"Hello".
2. Short paragraphs, 2-3 sentences max each, no more than 3 paragraphs.
3. 3-4 bullets of directly relevant experience with concrete numbers if available.
4. One technical recommendation OR one sharp clarifying question about their stack.
5. Close with a call to action (ask when they are free to call/talk).
6. Under 250 words total.
7. If the post asks to include a keyword or answer a question (e.g. to avoid bots),
   answer it prominently.
8. Sign off with "Best," followed by the freelancer name.
Return ONLY the proposal text. No preamble, no markdown fences.
"""


def _job_block(job):
    lines = [
        f"Title: {job.get('title')}",
        f"Link: {job.get('link')}",
        f"Budget: {job.get('budget')}",
        f"Job Type: {job.get('job_type')}",
        f"Experience Level: {job.get('experience_level')}",
        f"Proposals so far: {job.get('proposals')}",
        f"Hiring status: {job.get('hiring_status')}",
    ]
    if job.get("skills"):
        skills = job["skills"] if isinstance(job["skills"], list) else [job["skills"]]
        lines.append(f"Skills: {', '.join(str(s) for s in skills)}")
    head = "\n".join(f"{ln}" for ln in lines if ln and not ln.endswith(": "))
    return f"{head}\n\nDescription:\n{job.get('description', '')}".strip()


def build_prompt(job, score=None, reasons=None, name=None):
    """Compose the copy-paste prompt for Claude."""
    name = name or Config.FREELANCER_NAME
    gate_line = f"Match score: {score}/100 (passed the eligibility gate)"
    if reasons:
        gate_line += f"\nGate notes: {', '.join(reasons)}"

    return f"""\
You are writing an Upwork proposal on behalf of {name}.

# THE JOB
{_job_block(job)}

# FREELANCER PROFILE
{read_profile()}

# ELIGIBILITY (already checked)
{gate_line}

{PROPOSAL_FORMAT}
""".strip()


def slugify(title, link=""):
    slug = re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-")[:60]
    job_id = re.sub(r"\D", "", link or "")[-8:]
    return f"{slug}-{job_id}" if job_id else slug


def save_prompt(job, prompt=None, score=None, reasons=None):
    """Write the handoff prompt to files/claude_prompts/<slug>.md."""
    ensure_dir(Config.CLAUDE_PROMPTS_DIR)
    prompt = prompt or build_prompt(job, score=score, reasons=reasons)
    target = Path(Config.CLAUDE_PROMPTS_DIR) / f"{slugify(job.get('title'), job.get('link'))}.md"
    target.write_text(prompt + "\n", encoding="utf-8")
    return target


def capture_proposal(job, proposal):
    """Save a captured proposal and append it to the event log."""
    ensure_dir(Config.PROPOSALS_DIR)
    target = Path(Config.PROPOSALS_DIR) / f"{slugify(job.get('title'), job.get('link'))}.md"
    target.write_text(
        f"# {job.get('title')}\n{job.get('link')}\n\n{proposal}\n",
        encoding="utf-8",
    )
    append_jsonl(Config.MATCHES_FILE, {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "link": job.get("link"),
        "title": job.get("title"),
        "proposal_file": str(target),
    })
    append_event("proposal_captured", job, {"proposal_file": str(target)})
    return target