"""Play the agent against a baseline engine and write measured results to eval/results/."""

import argparse
import json
import random
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path

import chess

from agent.config import Config, load_config
from agent.llm import LLM, OllamaLLM
from agent.react_agent import ChessAgent, MoveResult
from tools.chess_tools import apply_move

RESULTS_DIR = Path(__file__).resolve().parent / "results"


def random_baseline(board: chess.Board, rng: random.Random) -> chess.Move:
    return rng.choice(sorted(board.legal_moves, key=lambda move: move.uci()))


def play_game(agent: ChessAgent, agent_color: chess.Color, rng: random.Random, max_plies: int) -> dict:
    board = chess.Board()
    moves: list[MoveResult] = []
    while not board.is_game_over(claim_draw=True) and board.ply() < max_plies:
        if board.turn == agent_color:
            result = agent.choose_move(board)
            moves.append(result)
            apply_move(board, result.move)
        else:
            apply_move(board, random_baseline(board, rng))

    outcome = board.outcome(claim_draw=True)
    if outcome is None:
        result_label = "unfinished"
    elif outcome.winner is None:
        result_label = "draw"
    else:
        result_label = "win" if outcome.winner == agent_color else "loss"

    return {
        "agent_color": "white" if agent_color == chess.WHITE else "black",
        "result": result_label,
        "plies": board.ply(),
        "moves_uci": [move.uci() for move in board.move_stack],
        "agent_moves": len(moves),
        "fallback_moves": sum(move.source == "fallback" for move in moves),
        "proposals": sum(move.proposals for move in moves),
        "illegal_proposals": sum(move.illegal_proposals for move in moves),
        "schema_errors": sum(move.schema_errors for move in moves),
        "tokens": sum(move.tokens for move in moves),
        "latency_s": sum(move.latency_s for move in moves),
    }


def summarize(games: list[dict]) -> dict:
    agent_moves = sum(game["agent_moves"] for game in games)
    proposals = sum(game["proposals"] for game in games)
    count = {label: sum(game["result"] == label for game in games) for label in ("win", "loss", "draw", "unfinished")}
    return {
        "games": len(games),
        **count,
        "win_rate": count["win"] / len(games) if games else 0.0,
        "illegal_move_rate": sum(game["illegal_proposals"] for game in games) / proposals if proposals else 0.0,
        "fallback_rate": sum(game["fallback_moves"] for game in games) / agent_moves if agent_moves else 0.0,
        "tokens_per_move": sum(game["tokens"] for game in games) / agent_moves if agent_moves else 0.0,
        "latency_s_per_move": sum(game["latency_s"] for game in games) / agent_moves if agent_moves else 0.0,
    }


def run_eval(
    llm: LLM, config: Config, games: int, max_plies: int, seed: int, out_dir: Path = RESULTS_DIR
) -> tuple[dict, Path]:
    agent = ChessAgent(llm, max_steps=config.max_steps)
    rng = random.Random(seed)
    played = []
    for index in range(games):
        color = chess.WHITE if index % 2 == 0 else chess.BLACK
        played.append(play_game(agent, color, rng, max_plies))
        print(f"game {index + 1}/{games}: {played[-1]['result']} in {played[-1]['plies']} plies", flush=True)

    now = datetime.now(timezone.utc)
    report = {
        "run_at": now.isoformat(timespec="seconds"),
        "opponent": "random baseline",
        "seed": seed,
        "max_plies": max_plies,
        "config": asdict(config),
        "summary": summarize(played),
        "games": played,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{now:%Y%m%dT%H%M%SZ}-{config.model.replace(':', '_')}.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    return report, path


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the agent against a random baseline.")
    parser.add_argument("--games", type=int, default=2, help="games to play, alternating colors")
    parser.add_argument("--max-plies", type=int, default=40, help="stop a game after this many plies")
    parser.add_argument("--seed", type=int, default=1, help="seed for the baseline")
    parser.add_argument("--model", help="Ollama model, overriding config.yaml")
    args = parser.parse_args()

    config = load_config()
    if args.model:
        config = replace(config, model=args.model)
    report, path = run_eval(OllamaLLM(config), config, args.games, args.max_plies, args.seed)
    print(json.dumps(report["summary"], indent=2))
    print(f"Results written to {path}")


if __name__ == "__main__":
    main()
