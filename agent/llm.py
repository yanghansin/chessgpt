"""Thin wrapper around the Ollama client, so tests can swap in a fake model."""

from dataclasses import dataclass
from typing import Protocol

import ollama

from agent.config import Config
from guardrails.schema import OUTPUT_SCHEMA


@dataclass(frozen=True)
class LLMReply:
    text: str
    tokens: int


class LLM(Protocol):
    def generate(self, prompt: str) -> LLMReply: ...


class OllamaLLM:
    def __init__(self, config: Config):
        self.config = config

    def generate(self, prompt: str) -> LLMReply:
        response = ollama.generate(
            model=self.config.model,
            prompt=prompt,
            format=OUTPUT_SCHEMA,
            options={
                "temperature": self.config.temperature,
                "num_predict": self.config.max_tokens,
            },
        )
        tokens = (response.prompt_eval_count or 0) + (response.eval_count or 0)
        return LLMReply(response.response, tokens)
