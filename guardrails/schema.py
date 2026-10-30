"""Output schema validation for LLM replies."""

import json
from dataclasses import dataclass

ACTIONS = ("check_move", "play")
MAX_MOVE_LENGTH = 10

# Passed to Ollama so the model is constrained to this shape when it supports structured output.
OUTPUT_SCHEMA = {
    "type": "object",
    "properties": {
        "thought": {"type": "string"},
        "action": {"type": "string", "enum": list(ACTIONS)},
        "move": {"type": "string"},
    },
    "required": ["thought", "action", "move"],
}


class SchemaError(ValueError):
    """The LLM reply doesn't match the output schema."""


@dataclass(frozen=True)
class Decision:
    thought: str
    action: str
    move: str


def parse_decision(text: str) -> Decision:
    """Parse one reply. Raises SchemaError with a message that can be shown to the model."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`").removeprefix("json").strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise SchemaError(f"reply is not valid JSON: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise SchemaError("reply must be a JSON object")

    action = data.get("action")
    if action not in ACTIONS:
        raise SchemaError(f"action must be one of {list(ACTIONS)}")

    move = data.get("move")
    if not isinstance(move, str) or not move.strip():
        raise SchemaError("move must be a non-empty string")
    move = move.strip()
    if len(move) > MAX_MOVE_LENGTH or any(ch.isspace() for ch in move):
        raise SchemaError("move must be a single move, such as Nf3")

    thought = data.get("thought", "")
    return Decision(thought if isinstance(thought, str) else "", action, move)
