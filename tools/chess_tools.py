"""python-chess helpers the agent uses as tools."""

from dataclasses import dataclass

import chess


@dataclass(frozen=True)
class LegalityResult:
    legal: bool
    move: chess.Move | None
    reason: str


def check_legal(board: chess.Board, text: str) -> LegalityResult:
    """Check a move written in SAN or UCI. Never changes the board."""
    text = text.strip()
    if not text:
        return LegalityResult(False, None, "empty move")
    try:
        return LegalityResult(True, board.parse_san(text), "legal")
    except ValueError:
        pass
    try:
        move = chess.Move.from_uci(text.lower())
    except ValueError:
        return LegalityResult(False, None, f"'{text}' is not valid SAN or UCI")
    if move in board.legal_moves:
        return LegalityResult(True, move, "legal")
    return LegalityResult(False, None, f"'{text}' is not legal in this position")


def legal_moves_san(board: chess.Board) -> list[str]:
    return sorted(board.san(move) for move in board.legal_moves)


def apply_move(board: chess.Board, move: chess.Move) -> None:
    """Play a move, refusing anything illegal even if earlier checks were skipped."""
    if move not in board.legal_moves:
        raise ValueError(f"refusing to play illegal move {move.uci()}")
    board.push(move)
