"""Settings from config.yaml, with environment variables taking priority."""

import os
from dataclasses import dataclass
from pathlib import Path

import yaml

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "config.yaml"


@dataclass(frozen=True)
class Config:
    model: str = "mistral"
    temperature: float = 0.2
    max_tokens: int = 200
    max_steps: int = 4


def load_config(path: Path = DEFAULT_PATH) -> Config:
    data = yaml.safe_load(path.read_text()) if path.exists() else {}
    data = data or {}
    defaults = Config()
    return Config(
        model=os.getenv("CHESSGPT_MODEL", data.get("model", defaults.model)),
        temperature=float(os.getenv("CHESSGPT_TEMPERATURE", data.get("temperature", defaults.temperature))),
        max_tokens=int(os.getenv("CHESSGPT_MAX_TOKENS", data.get("max_tokens", defaults.max_tokens))),
        max_steps=int(os.getenv("CHESSGPT_MAX_STEPS", data.get("max_steps", defaults.max_steps))),
    )
