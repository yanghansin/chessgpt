"""Deterministic fallback for when the LLM doesn't produce a legal move in time."""

import chess

PIECE_VALUES = {
    chess.PAWN: 1,
    chess.KNIGHT: 3,
    chess.BISHOP: 3,
    chess.ROOK: 5,
    chess.QUEEN: 9,
    chess.KING: 0,
}
MATE_SCORE = 1000


def _score(board: chess.Board, move: chess.Move) -> int:
    score = 0
    if board.is_capture(move):
        captured = board.piece_type_at(move.to_square) or chess.PAWN  # None means en passant
        score += PIECE_VALUES[captured]
    if move.promotion:
        score += PIECE_VALUES[move.promotion]
    board.push(move)
    if board.is_checkmate():
        score = MATE_SCORE
    board.pop()
    return score


def fallback_move(board: chess.Board) -> chess.Move:
    """Pick mate, then the biggest material gain. Ties go to the first move in UCI order."""
    moves = sorted(board.legal_moves, key=lambda move: move.uci())
    if not moves:
        raise ValueError("no legal moves in this position")
    return max(moves, key=lambda move: _score(board, move))
