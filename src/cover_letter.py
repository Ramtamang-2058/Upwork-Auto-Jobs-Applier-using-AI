"""Shared AI services: job classification and cover-letter generation.

Both services wrap the raw :class:`Agent` and normalise the LLM's JSON
response so the rest of the application never has to scrape markdown fences
or tolerate malformed JSON.
"""
import json
import re

from .agent import Agent
from .config import Config
from .prompts import classify_jobs_prompt, generate_cover_letter_prompt
from .storage import read_profile


def strip_json_fences(text):
    """Remove ```json ... ``` markers the model may wrap its answer in."""
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*$", "", text)
    return text.strip()


def parse_json_payload(text):
    """Best-effort parse of an LLM response into a dict. Returns {} on failure."""
    cleaned = strip_json_fences(text)
    try:
        data = json.loads(cleaned, strict=False)
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


class BaseAgentService:
    def __init__(self, agent_name, model, prompt_template, profile=None, temperature=None):
        self.profile = profile or read_profile()
        self.model = model or Config.MODEL_WRITER
        self.temperature = temperature if temperature is not None else Config.LLM_TEMPERATURE
        self.agent = Agent(
            name=agent_name,
            model=self.model,
            system_prompt=prompt_template.format(profile=self.profile),
            temperature=self.temperature,
        )


class JobClassifier(BaseAgentService):
    """Classifies scraped jobs against the freelancer profile."""

    def __init__(self, profile=None, model=None, temperature=None):
        super().__init__(
            agent_name="Job Classifier",
            model=model or Config.MODEL_CLASSIFIER,
            prompt_template=classify_jobs_prompt,
            profile=profile,
            temperature=temperature,
        )

    def classify(self, jobs_text):
        """Return the list of matching jobs (each with 'job' and 'reason')."""
        matches = parse_json_payload(self.agent.invoke(jobs_text)).get("matches", [])
        return matches if isinstance(matches, list) else []


class CoverLetterGenerator(BaseAgentService):
    """Generates a personalised cover letter for a single job description."""

    def __init__(self, profile=None, model=None, temperature=None):
        super().__init__(
            agent_name="Cover Letter Writer",
            model=model or Config.MODEL_WRITER,
            prompt_template=generate_cover_letter_prompt,
            profile=profile,
            temperature=temperature,
        )

    def generate(self, job_description):
        """Return the raw letter text, falling back to the raw model output."""
        raw = self.agent.invoke(job_description)
        letter = parse_json_payload(raw).get("letter")
        return (letter if letter else raw).strip()