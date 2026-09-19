# Application Guidelines

This file decides **whether** a proposal is drafted for a job. The monitor
(`tools/upwork_monitor.py`) and the handoff tool (`tools/claude_handoff.py`)
parse the rules below and reject jobs that fail any of them.

Edit these to match your approach. Lines starting with `#` are comments.

## Rules

# Only apply while the client is still hiring.
# Accepted values: HIRING (usually "Available" / open). HIRED/CLOSED posts are rejected.
hiring_status: HIRING

# Skip jobs that already have this many proposals or more.
proposals < 5

# Minimum budget in dollars (the top figure of the posted range is compared).
# Hourly jobs like "$40-$70/hr" compare as $70; keep this below your real floor.
min_budget: 50

# Experience levels we will apply to (comma-separated, case-insensitive).
experience_level: Expert, Intermediate

# Minimum skill-match score (0-100) from the profile keyword matcher.
min_match_score: 60

## Notes

- A job is "eligible" only if it passes every rule. Returned reasons are logged
  to `files/application_log.jsonl`.
- The min_score can be overridden per run with `--min-score N`.
- Budget strings that cannot be parsed are rejected (`could not parse a budget
  figure`) - make sure jobs dropped into the inbox include a `budget` field.