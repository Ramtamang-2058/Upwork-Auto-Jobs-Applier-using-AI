"""Tests for the keyless monitor: matcher, eligibility gate, handoff, logging."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src import eligibility, handoff, matcher, storage  # noqa: E402


PROFILE = """Christopher - Senior AI & Full Stack Engineer.
Python, LangChain, React, FastAPI, RAG, vector databases, AWS,
VR development with Unity, conversational AI agents."""


class TestMatcher:
    def test_high_score_for_relevant_job(self):
        job = {
            "title": "LangChain AI Agent Developer",
            "description": "Build a RAG conversational agent with Python, LangChain and FastAPI.",
            "skills": ["Python", "LangChain", "React"],
        }
        assert matcher.score_job(job, PROFILE) >= 60

    def test_low_score_for_unrelated_job(self):
        job = {
            "title": "WordPress content writer",
            "description": "Write blog posts about gardening and SEO keywords.",
            "skills": ["WordPress", "SEO"],
        }
        assert matcher.score_job(job, PROFILE) <= 20

    def test_title_boost_applies(self):
        base = {"title": "Accountant needed", "description": "Books, taxes, payroll.",
                "skills": []}
        boosted = {"title": "React Native Developer for Python app",
                   "description": "Books, taxes, payroll.", "skills": []}
        assert matcher.score_job(boosted, PROFILE) > matcher.score_job(base, PROFILE)


class TestEligibility:
    def test_parse_defaults(self):
        rules = eligibility.load_rules()
        assert rules["statuses"] == {"HIRING"}
        assert rules["min_score"] == 60

    def test_parse_custom_rules(self, tmp_path):
        rules_file = tmp_path / "apply.md"
        rules_file.write_text(
            "hiring_status: HIRING\nproposals < 3\nmin_budget: 100\n"
            "experience_level: Expert\nmin_match_score: 70\n",
            encoding="utf-8",
        )
        rules = eligibility.load_rules(rules_file)
        assert rules["statuses"] == {"HIRING"}
        assert rules["proposals_op"] == "<" and rules["proposals_max"] == 3
        assert rules["min_budget"] == 100
        assert rules["experience"] == {"expert"}
        assert rules["min_score"] == 70

    def test_eligible_job_passes(self):
        rules = eligibility.load_rules()
        job = {"hiring_status": "HIRING", "proposals": "2", "experience_level": "Expert",
               "budget": "$30-$100/hr"}
        verdict = eligibility.check(job, rules, score=80)
        assert verdict["eligible"] is True

    def test_rejects_too_many_proposals(self):
        rules = eligibility.load_rules()
        job = {"hiring_status": "HIRING", "proposals": "9", "experience_level": "Expert",
               "budget": "$80/hr"}
        verdict = eligibility.check(job, rules, score=80)
        assert verdict["eligible"] is False
        assert any("proposals" in r for r in verdict["reasons"])

    def test_rejects_below_min_budget(self):
        job = {"hiring_status": "HIRING", "proposals": "0", "budget": "$20/hr"}
        verdict = eligibility.check(job, eligibility.load_rules(), score=90)
        assert verdict["eligible"] is False
        assert any("budget" in r for r in verdict["reasons"])

    def test_budget_extraction(self):
        assert eligibility.extract_budget_dollars("Hourly: $40 - $70/hr") == 70
        assert eligibility.extract_budget_dollars("Fixed price: $8,000") == 8000
        assert eligibility.extract_budget_dollars("unknown") is None


class TestHandoff:
    def test_build_prompt_contains_job_profile_format(self):
        job = {"title": "LangChain Dev", "link": "https://upwork.com/jobs/x",
               "budget": "$60-90/hr", "description": "Build agents with LangChain."}
        prompt = handoff.build_prompt(job, score=80, name="TestUser")
        assert "LangChain Dev" in prompt
        assert "TestUser" in prompt
        assert "OUTPUT FORMAT" in prompt

    def test_slugify(self):
        assert handoff.slugify("Hello, World!", "https://upwork.com/jobs/~123456789") \
            .startswith("hello-world-")


class TestStorageLogging:
    def test_read_jsonl_skips_bad_lines(self, tmp_path):
        f = tmp_path / "inbox.jsonl"
        f.write_text('{"a":1}\nnot json\n{"b":2}\n', encoding="utf-8")
        rows = storage.read_jsonl(f)
        assert rows == [{"a": 1}, {"b": 2}]

    def test_append_and_read_jsonl(self, tmp_path):
        f = tmp_path / "out.jsonl"
        storage.append_jsonl(f, {"link": "x", "score": 66})
        storage.append_jsonl(f, {"link": "y"})
        assert len(storage.read_jsonl(f)) == 2

    def test_append_event(self, tmp_path, monkeypatch):
        monkeypatch.setattr(storage.Config, "EVENTS_LOG_FILE", tmp_path / "events.jsonl")
        storage.append_event("gate", {"link": "l1", "title": "T"}, {"score": 50})
        rows = storage.read_jsonl(tmp_path / "events.jsonl")
        assert rows[0]["event"] == "gate"
        assert rows[0]["job"] == "l1"