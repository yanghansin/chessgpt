"""Pre-execution verification: nothing reaches the board without passing here."""

import chess

from tools.chess_tools import LegalityResult, check_legal


def verify_move(board: chess.Board, text: str) -> LegalityResult:
    return check_legal(board, text)
