"""Scheduled Upwork job monitor.

Every pass it:
  1. Reads new jobs from files/inbox_jobs.jsonl  (drop jobs here via the
     POST /api/queue-job endpoint, the bookmarklet, or a script).
  2. Scores each unseen job against the profile and applies guidelines/apply.md.
  3. Logs every decision to files/application_log.jsonl.
  4. For eligible jobs, saves a ready-to-paste Claude handoff prompt to
     files/claude_prompts/ and copies it to the clipboard.

No API key is required for matching or the decision gate; proposals are written
by Claude in the user's browser.

Usage:
    python tools/upwork_monitor.py                 # loop every 300s
    python tools/upwork_monitor.py --interval 900
    python tools/upwork_monitor.py --once          # single pass (cron-friendly)
    python tools/upwork_monitor.py --min-score 75
"""
import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from src import handoff
from src.config import Config
from src.eligibility import check, load_rules
from src.matcher import score_job
from src.storage import append_event, append_jsonl, read_jsonl

load_dotenv()


def load_seen():
    seen = Config.SEEN_FILE
    if seen.exists():
        return json.loads(seen.read_text(encoding="utf-8"))
    return {}


def save_seen(seen):
    Config.SEEN_FILE.write_text(json.dumps(seen, indent=2), encoding="utf-8")


def process_inbox(rules, min_score_override=None, copy_each=False):
    """Score + gate every new job in the inbox. Returns counts."""
    jobs = read_jsonl(Config.INBOX_FILE)
    seen = load_seen()
    eligible = rejected = duplicate = 0
    copies = []

    for job in jobs:
        link = (job.get("link") or "").strip()
        key = link or json.dumps(job)
        if key in seen:
            duplicate += 1
            continue

        score = score_job(job)
        rules["min_score"] = min_score_override if min_score_override is not None \
            else rules["min_score"]
        verdict = check(job, rules, score)
        seen[key] = datetime.now(timezone.utc).isoformat(timespec="seconds")

        if verdict["eligible"]:
            eligible += 1
            prompt_file = handoff.save_prompt(job, score=score)
            append_jsonl(Config.MATCHES_FILE, {
                "ts": seen[key],
                "link": link,
                "title": job.get("title"),
                "score": score,
                "prompt_file": str(prompt_file),
            })
            append_event("eligible", job, {"score": score, "checklist": verdict["checklist"]})
            if copy_each:
                copies.append((prompt_file, handoff.build_prompt(job, score=score)))
        else:
            rejected += 1
            append_event("rejected", job, {"score": score, "reasons": verdict["reasons"]})

    save_seen(seen)
    return {"jobs": len(jobs), "new": eligible + rejected, "eligible": eligible,
            "rejected": rejected, "duplicate": duplicate, "copies": copies}


def main():
    parser = argparse.ArgumentParser(description="Upwork job monitor")
    parser.add_argument("--interval", type=int, default=Config.MONITOR_INTERVAL,
                        help="Seconds between passes (default 300)")
    parser.add_argument("--once", action="store_true",
                        help="Run a single pass and exit (for cron)")
    parser.add_argument("--min-score", type=float, default=None,
                        help="Override the min_match_score rule")
    parser.add_argument("--copy", action="store_true",
                        help="Copy each eligible job's prompt to the clipboard")
    args = parser.parse_args()

    rules = load_rules()
    first = True
    while True:
        if first:
            print(f"Monitoring {Config.INBOX_FILE} every {args.interval}s "
                  f"(rules: {Config.GUIDELINES_FILE})...")
            first = False

        counts = process_inbox(rules, args.min_score, args.copy)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] inbox={counts['jobs']} "
              f"new={counts['new']} eligible={counts['eligible']} "
              f"rejected={counts['rejected']} dup={counts['duplicate']}")

        if args.copy:
            import pyperclip

            for prompt_file, prompt in counts["copies"]:
                pyperclip.copy(prompt)
                print(f"Copied prompt: {prompt_file}")

        if args.once or args.interval <= 0:
            break

        try:
            time.sleep(args.interval)
        except KeyboardInterrupt:
            print("\nStopped.")
            return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())