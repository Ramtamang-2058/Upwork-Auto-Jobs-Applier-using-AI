"""Decision gate: decides *whether* to draft a proposal for a job.

The rules live in ``guidelines/apply.md`` (plain text, see that file for the
format). If the file is missing or empty, permissive defaults are used so the
monitor still works out of the box.
"""
import re
from pathlib import Path

from .config import Config

_HASH_COMMENT = re.compile(r"#.*")
_COMPARE_RE = re.compile(r"^\s*(?P<key>\w[\w ]*?)\s*(?P<op><|>|<=|>=)\s*(?P<val>\d+(?:\.\d+)?)\s*$")
_EQUALS_RE = re.compile(r"^\s*(?P<key>\w[\w ]*?)\s*:\s*(?P<val>.+?)\s*$")

DEFAULT_RULES = """
# Defaults used when guidelines/apply.md is absent.
# Strong match only, but no strict status/proposal limits.
hiring_status: HIRING
min_match_score: 60
"""

_RULE_KEYS = {
    "hiring_status": "statuses",
    "experience_level": "experience",
    "proposals": "proposals_max",
    "min_budget": "min_budget",
    "min_match_score": "min_score",
}


def load_rules(filename=None):
    """Parse guidelines/apply.md into a rules dict.

    Recognised rules:
      hiring_status: HIRING            (comma-separated acceptable values)
      experience_level: Expert, Inter. (comma-separated acceptable values)
      proposals < 5                    (numeric comparison: <, <=, >, >=)
      min_budget: 50                   (min hourly/fixed dollars in the post)
      min_match_score: 60              (0-100 skill-match threshold)
    """
    path = Path(filename or Config.GUIDELINES_FILE)
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    if not text.strip():
        text = DEFAULT_RULES

    rules = {
        "statuses": None,
        "experience": None,
        "proposals_op": None,
        "proposals_max": None,
        "min_budget": None,
        "min_score": 60,
    }

    for raw in text.splitlines():
        line = _HASH_COMMENT.sub("", raw).strip()
        if not line:
            continue

        compare = _COMPARE_RE.match(line)
        if compare:
            key = _RULE_KEYS.get(compare.group("key").strip())
            if key == "proposals_max":
                rules["proposals_op"] = compare.group("op")
                rules["proposals_max"] = float(compare.group("val"))
            continue

        equals = _EQUALS_RE.match(line)
        if equals:
            key = equals.group("key").strip()
            value = equals.group("val").strip()
            rule_key = _RULE_KEYS.get(key)
            if rule_key == "statuses":
                rules["statuses"] = {v.strip().upper() for v in value.split(",") if v.strip()}
            elif rule_key == "experience":
                rules["experience"] = {v.strip().lower() for v in value.split(",") if v.strip()}
            elif rule_key == "min_budget":
                rules["min_budget"] = float(value.replace("$", "").replace(",", ""))
            elif rule_key == "min_score":
                rules["min_score"] = float(value)

    return rules


def extract_budget_dollars(budget_str):
    """Highest dollar figure found in a budget string (None if unparsable)."""
    if not budget_str:
        return None
    amounts = re.findall(r"\$([\d,]+)", budget_str)
    if not amounts:
        return None
    return max(int(a.replace(",", "")) for a in amounts)


def _as_int(value):
    if value is None:
        return None
    try:
        return int(str(value).replace("+", "").replace(" ", ""))
    except (ValueError, TypeError):
        return None


def check(job, rules=None, score=None):
    """Apply the rules to a job. Returns {eligible, reasons, checklist}.

    ``score`` is the numeric match score from :mod:`src.matcher`; if omitted the
    job's own ``match_score`` key is used.
    """
    rules = rules if rules is not None else load_rules()
    reasons = []
    checklist = {}

    status = str(job.get("hiring_status") or "HIRING").upper()
    if rules["statuses"]:
        ok = status in rules["statuses"]
        checklist["hiring_status"] = status
        if not ok:
            reasons.append(f"hiring_status={status} not in {sorted(rules['statuses'])}")

    experience = str(job.get("experience_level") or "").lower()
    if rules["experience"]:
        ok = experience in rules["experience"]
        checklist["experience_level"] = experience
        if not ok:
            reasons.append(f"experience_level={experience or 'unknown'} not allowed")

    proposals = _as_int(job.get("proposals"))
    if rules["proposals_max"] is not None and proposals is not None:
        op = rules["proposals_op"]
        ok = (proposals < rules["proposals_max"]) if op == "<" else (
            proposals <= rules["proposals_max"] if op == "<=" else
            proposals > rules["proposals_max"] if op == ">" else proposals >= rules["proposals_max"]
        )
        checklist["proposals"] = proposals
        if not ok:
            reasons.append(f"proposals={proposals} fails rule proposals {op} {rules['proposals_max']}")

    budget = extract_budget_dollars(job.get("budget") or "")
    if rules["min_budget"] is not None:
        checklist["budget"] = budget
        if budget is None:
            reasons.append("could not parse a budget figure")
        elif budget < rules["min_budget"]:
            reasons.append(f"budget=${budget} below min ${int(rules['min_budget'])}")

    match_score = score if score is not None else job.get("match_score")
    checklist["match_score"] = match_score
    if match_score is None or match_score < rules["min_score"]:
        reasons.append(f"match_score={match_score} below min {rules['min_score']}")

    return {
        "eligible": not reasons,
        "reasons": reasons,
        "checklist": checklist,
    }