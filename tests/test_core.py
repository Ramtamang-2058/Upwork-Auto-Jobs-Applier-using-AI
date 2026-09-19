"""Unit tests that do not require API keys or a network connection."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pytest  # noqa: E402

from src import cover_letter, storage  # noqa: E402
from src.config import Config  # noqa: E402
from src.storage import save_jobs_to_file  # noqa: E402


SAMPLE_JOBS = [
    {
        "title": "AI Agent Developer",
        "link": "https://www.upwork.com/jobs/x",
        "description": "Build an agent with LangChain.",
        "job_type": "Hourly",
        "experience_level": "Expert",
        "budget": "$50-$100/hr",
    },
    {
        "title": "React Developer",
        "link": "https://www.upwork.com/jobs/y",
        "description": "Build a dashboard.",
        "job_type": "Fixed Price",
        "experience_level": "Intermediate",
        "budget": "$1000",
    },
]


class TestStorage:
    def test_save_and_read_jobs_roundtrip(self, tmp_path):
        target = tmp_path / "jobs.txt"
        save_jobs_to_file(SAMPLE_JOBS, target)
        content = target.read_text(encoding="utf-8")
        assert "AI Agent Developer" in content
        assert "React Developer" in content
        assert "---\n" in content

    def test_read_text_file_strips_and_joins(self, tmp_path):
        profile = tmp_path / "profile.md"
        profile.write_text("Line one\n\n  Line two  \n", encoding="utf-8")
        assert storage.read_text_file(profile) == "Line oneLine two"

    def test_append_cover_letter(self, tmp_path):
        target = tmp_path / "letters.txt"
        storage.append_cover_letter("Hello", target)
        storage.append_cover_letter("World", target)
        content = target.read_text(encoding="utf-8")
        assert "Hello" in content and "World" in content


class TestCoverLetterParsing:
    def test_strip_json_fences(self):
        assert cover_letter.strip_json_fences("```json\n{}\n```") == "{}"

    def test_parse_json_payload_valid(self):
        payload = cover_letter.parse_json_payload('{"letter": "Hi there"}')
        assert payload == {"letter": "Hi there"}

    def test_parse_json_payload_fenced(self):
        payload = cover_letter.parse_json_payload('```json\n{"letter": "Hi"}\n```')
        assert payload == {"letter": "Hi"}

    def test_parse_json_payload_invalid_returns_empty_dict(self):
        assert cover_letter.parse_json_payload("not json at all") == {}

    def test_generator_falls_back_to_raw_text(self):
        class FakeAgent:
            def invoke(self, message):
                return "Plain text letter."

        gen = object.__new__(cover_letter.CoverLetterGenerator)
        gen.agent = FakeAgent()
        assert gen.generate("job") == "Plain text letter."

    def test_generator_uses_letter_key(self):
        class FakeAgent:
            def invoke(self, message):
                return '{"letter": "Structured letter"}'

        gen = object.__new__(cover_letter.CoverLetterGenerator)
        gen.agent = FakeAgent()
        assert gen.generate("job") == "Structured letter"

    def test_classifier_returns_matches_list(self):
        class FakeAgent:
            def invoke(self, message):
                return '{"matches": [{"job": "A"}]}'

        classifier = object.__new__(cover_letter.JobClassifier)
        classifier.agent = FakeAgent()
        assert classifier.classify("jobs") == [{"job": "A"}]

    def test_config_has_expected_defaults(self):
        assert Config.DEFAULT_NUM_JOBS > 0
        assert Config.FILES_DIR.exists()