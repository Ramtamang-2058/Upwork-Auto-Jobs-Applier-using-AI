"""Thin wrapper around LiteLLM's completion API."""
from litellm import completion


class Agent:
    """A stateless LLM agent with a fixed system prompt."""

    def __init__(self, name, model, system_prompt="", temperature=0.1):
        self.name = name
        self.model = model
        self.temperature = temperature
        self.system_prompt = system_prompt

    def invoke(self, message):
        print(f"\nCalling Agent: {self.name}")
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": message},
        ]
        response = completion(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        return response.choices[0].message.content