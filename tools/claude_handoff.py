"""Interactive one-shot: paste a job, gate it, hand off to Claude in your browser.

Works with no API key. Flow:
  1. Paste a job description (title/budget/experience/proposals if known) or pass
     a JSON job object via --job-file.
  2. The job is scored against your profile and checked against
     guidelines/apply.md.
  3. If eligible, a ready-to-paste prompt for Claude is built and copied to your
     clipboard; open Claude in Firefox, paste, tweak, copy the reply, and paste
     it back here.
  4. The proposal is saved to files/proposals/ and logged.

Usage:
    python tools/claude_handoff.py                     # paste a job
    python tools/claude_handoff.py --job-file job.json
    python tools/claude_handoff.py --min-score 70
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from src import handoff
from src.eligibility import check, load_rules
from src.matcher import score_job
from src.storage import append_event

load_dotenv()


def read_multiline_input():
    lines = []
    while True:
        line = input()
        if not line and lines and not lines[-1]:
            break
        lines.append(line)
    return "\n".join(lines).strip()


def job_from_stdin():
    """Build a job dict from a pasted description (best-effort parsing)."""
    text = read_multiline_input()
    if not text:
        print("No job provided.")
        return None
    job = {"title": text.splitlines()[0].strip(), "description": text, "link": ""}
    for line in text.splitlines():
        low = line.lower()
        if "$" in line and ("budget" in low or "hr" in low or "fixed" in low):
            job.setdefault("budget", line.strip())
    return job


def main():
    parser = argparse.ArgumentParser(description="Gate a job and hand off to Claude")
    parser.add_argument("--job-file", type=Path, help="JSON file with the job dict")
    parser.add_argument("--min-score", type=float, default=None,
                        help="Override the min_match_score rule")
    args = parser.parse_args()

    if args.job_file:
        job = json.loads(args.job_file.read_text(encoding="utf-8"))
    else:
        print("Paste the full Upwork job (title, budget, description); blank line to finish:\n")
        job = job_from_stdin()
        if job is None:
            return 1

    score = score_job(job)
    rules = load_rules()
    if args.min_score is not None:
        rules["min_score"] = args.min_score

    verdict = check(job, rules, score)
    append_event("gate", job, {"score": score, "eligible": verdict["eligible"],
                               "reasons": verdict["reasons"]})

    print(f"Match score: {score}/100")
    if not verdict["eligible"]:
        print("Not eligible - skipping:")
        for reason in verdict["reasons"]:
            print(f"  - {reason}")
        return 0

    prompt = handoff.build_prompt(job, score=score, reasons=verdict["reasons"])
    prompt_file = handoff.save_prompt(job, prompt)

    try:
        import pyperclip

        pyperclip.copy(prompt)
        print("\nHandoff prompt copied to clipboard.")
    except ImportError:
        pass

    print(f"\nSaved to: {prompt_file}")
    print("\n1. Open Claude in Firefox and paste the prompt.")
    print("2. Tweak the proposal if you want.")
    print("3. Copy Claude's reply and paste it back here (blank line to finish):\n")

    proposal = read_multiline_input()
    if not proposal:
        print("No proposal captured.")
        return 1

    target = handoff.capture_proposal(job, proposal)
    print(f"\nProposal saved to: {target}")
    print("Review it on Upwork and hit Send yourself.")
    return 0


if __name__ == "__main__":
    sys.exit(main())