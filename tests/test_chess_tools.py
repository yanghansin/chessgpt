import chess
import pytest

from tools.chess_tools import apply_move, check_legal, legal_moves_san


def test_accepts_san_and_uci():
    board = chess.Board()
    assert check_legal(board, "e4").move == chess.Move.from_uci("e2e4")
    assert check_legal(board, "e2e4").move == chess.Move.from_uci("e2e4")


@pytest.mark.parametrize("text", ["e5", "Qh5", "e2e5", "castle", "", "   "])
def test_rejects_illegal_or_malformed_moves(text):
    result = check_legal(chess.Board(), text)
    assert not result.legal
    assert result.move is None
    assert result.reason


def test_rejects_ambiguous_san():
    board = chess.Board("4k3/8/8/8/8/8/8/R3K2R w - - 0 1")
    board.remove_piece_at(chess.E1)
    board.set_piece_at(chess.H8, chess.Piece.from_symbol("K"))
    assert not check_legal(board, "Rd1").legal
    assert check_legal(board, "Rad1").legal


def test_check_does_not_change_the_board():
    board = chess.Board()
    fen = board.fen()
    check_legal(board, "e4")
    check_legal(board, "nonsense")
    assert board.fen() == fen


def test_legal_moves_are_all_accepted():
    board = chess.Board()
    moves = legal_moves_san(board)
    assert len(moves) == 20
    assert all(check_legal(board, move).legal for move in moves)


def test_apply_move_refuses_illegal_moves():
    board = chess.Board()
    with pytest.raises(ValueError):
        apply_move(board, chess.Move.from_uci("e2e5"))
    assert board.ply() == 0
