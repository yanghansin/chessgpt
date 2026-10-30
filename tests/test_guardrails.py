import chess
import pytest

from guardrails.fallback import fallback_move
from guardrails.schema import SchemaError, parse_decision
from guardrails.verification import verify_move


def test_parses_valid_reply():
    decision = parse_decision('{"thought": "Control the center.", "action": "play", "move": "e4"}')
    assert (decision.action, decision.move) == ("play", "e4")


def test_parses_fenced_reply():
    assert parse_decision('```json\n{"action": "check_move", "move": "Nf3"}\n```').move == "Nf3"


@pytest.mark.parametrize(
    "text",
    [
        "I would play e4",
        "[]",
        '{"action": "resign", "move": "e4"}',
        '{"action": "play"}',
        '{"action": "play", "move": ""}',
        '{"action": "play", "move": 7}',
        '{"action": "play", "move": "e4 then Nf3"}',
    ],
)
def test_rejects_invalid_replies(text):
    with pytest.raises(SchemaError):
        parse_decision(text)


def test_verification_blocks_illegal_move():
    assert verify_move(chess.Board(), "e4").legal
    assert not verify_move(chess.Board(), "Ke2").legal


def test_fallback_is_deterministic_and_legal():
    board = chess.Board()
    first = fallback_move(board)
    assert first == fallback_move(board)
    assert first in board.legal_moves


def test_fallback_takes_mate():
    board = chess.Board("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1")
    assert fallback_move(board) == chess.Move.from_uci("a1a8")


def test_fallback_takes_most_valuable_piece():
    board = chess.Board("k7/8/8/3q4/2P1P3/8/8/K6r w - - 0 1")
    board.remove_piece_at(chess.H1)
    assert fallback_move(board).to_square == chess.D5


def test_fallback_leaves_board_unchanged():
    board = chess.Board()
    fen = board.fen()
    fallback_move(board)
    assert board.fen() == fen


def test_fallback_raises_when_no_moves():
    board = chess.Board("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1")
    with pytest.raises(ValueError):
        fallback_move(board)
