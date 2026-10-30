"""Agent and harness tests, using a scripted fake model so no Ollama server is needed."""

import json
import random

import chess

from agent.config import Config
from agent.llm import LLMReply
from agent.react_agent import ChessAgent
from eval.harness import play_game, run_eval


class ScriptedLLM:
    def __init__(self, *replies):
        self.replies = list(replies)
        self.prompts = []

    def generate(self, prompt):
        self.prompts.append(prompt)
        text = self.replies.pop(0) if self.replies else "not json"
        return LLMReply(text, tokens=10)


def reply(action, move):
    return json.dumps({"thought": "t", "action": action, "move": move})


def test_plays_a_legal_move():
    result = ChessAgent(ScriptedLLM(reply("play", "e4"))).choose_move(chess.Board())
    assert result.source == "llm"
    assert result.move == chess.Move.from_uci("e2e4")
    assert result.illegal_proposals == 0


def test_check_then_play():
    llm = ScriptedLLM(reply("check_move", "Nf3"), reply("play", "Nf3"))
    result = ChessAgent(llm).choose_move(chess.Board())
    assert result.steps == 2
    assert "Nf3 is legal" in llm.prompts[1]


def test_illegal_move_is_reported_back_to_the_model():
    llm = ScriptedLLM(reply("play", "Qh5"), reply("play", "e4"))
    result = ChessAgent(llm).choose_move(chess.Board())
    assert result.illegal_proposals == 1
    assert result.move == chess.Move.from_uci("e2e4")
    assert "Legal moves:" in llm.prompts[1]


def test_falls_back_when_model_never_succeeds():
    board = chess.Board()
    result = ChessAgent(ScriptedLLM(), max_steps=3).choose_move(board)
    assert result.source == "fallback"
    assert result.schema_errors == 3
    assert result.move in board.legal_moves


def test_check_move_alone_does_not_end_the_turn():
    llm = ScriptedLLM(reply("check_move", "e4"), reply("check_move", "d4"))
    result = ChessAgent(llm, max_steps=2).choose_move(chess.Board())
    assert result.source == "fallback"


def test_game_never_plays_an_illegal_move():
    game = play_game(ChessAgent(ScriptedLLM()), chess.WHITE, random.Random(1), max_plies=30)
    board = chess.Board()
    for uci in game["moves_uci"]:
        move = chess.Move.from_uci(uci)
        assert move in board.legal_moves
        board.push(move)
    assert game["fallback_moves"] == game["agent_moves"]


def test_run_eval_writes_results(tmp_path):
    config = Config(model="fake:model", max_steps=1)
    report, path = run_eval(ScriptedLLM(), config, games=2, max_plies=10, seed=1, out_dir=tmp_path)
    assert path.parent == tmp_path
    assert json.loads(path.read_text()) == report
    assert report["summary"]["games"] == 2
    assert report["summary"]["unfinished"] == 2
    assert report["summary"]["tokens_per_move"] == 10
