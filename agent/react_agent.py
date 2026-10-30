"""ReAct-style loop: the model reasons, acts, reads the observation, and repeats."""

import time
from dataclasses import dataclass, field

import chess

from agent.llm import LLM
from agent.prompts import build_prompt
from guardrails.fallback import fallback_move
from guardrails.schema import SchemaError, parse_decision
from guardrails.verification import verify_move
from tools.chess_tools import legal_moves_san


@dataclass
class MoveResult:
    move: chess.Move
    source: str  # "llm" or "fallback"
    steps: int = 0
    proposals: int = 0
    illegal_proposals: int = 0
    schema_errors: int = 0
    tokens: int = 0
    latency_s: float = 0.0
    transcript: list[str] = field(default_factory=list)


class ChessAgent:
    def __init__(self, llm: LLM, max_steps: int = 4):
        self.llm = llm
        self.max_steps = max_steps

    def choose_move(self, board: chess.Board) -> MoveResult:
        started = time.perf_counter()
        result = MoveResult(move=chess.Move.null(), source="fallback")

        for _ in range(self.max_steps):
            result.steps += 1
            reply = self.llm.generate(build_prompt(board, result.transcript))
            result.tokens += reply.tokens

            try:
                decision = parse_decision(reply.text)
            except SchemaError as exc:
                result.schema_errors += 1
                result.transcript.append(f"Observation: invalid reply, {exc}.")
                continue

            result.transcript.append(
                f"Thought: {decision.thought}\nAction: {decision.action} {decision.move}"
            )
            result.proposals += 1
            check = verify_move(board, decision.move)

            if not check.legal:
                result.illegal_proposals += 1
                legal = ", ".join(legal_moves_san(board))
                result.transcript.append(f"Observation: {check.reason}. Legal moves: {legal}.")
            elif decision.action == "play":
                result.move = check.move
                result.source = "llm"
                break
            else:
                result.transcript.append(f"Observation: {decision.move} is legal.")

        if result.source == "fallback":
            result.move = fallback_move(board)
        result.latency_s = time.perf_counter() - started
        return result
