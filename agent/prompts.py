"""Prompt templates for the ReAct loop."""

import chess

SYSTEM = """You are playing chess as {side}. Choose one good legal move.

Position (FEN): {fen}
Board:
{board}
Recent moves (UCI): {history}

Reply with one JSON object and nothing else:
{{"thought": "<one short sentence>", "action": "check_move" or "play", "move": "<move in SAN, such as Nf3>"}}

Use "check_move" to ask whether a move is legal without playing it.
Use "play" to play a move and end your turn.
"""


def build_prompt(board: chess.Board, transcript: list[str]) -> str:
    side = "White" if board.turn == chess.WHITE else "Black"
    history = " ".join(move.uci() for move in board.move_stack[-8:]) or "none"
    prompt = SYSTEM.format(side=side, fen=board.fen(), board=board, history=history)
    if transcript:
        prompt += "\nYour previous steps this turn:\n" + "\n".join(transcript) + "\n"
    return prompt
