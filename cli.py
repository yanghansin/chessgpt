"""Play a game against the agent from the terminal."""

import argparse
import random
from dataclasses import replace

import chess

from agent.config import load_config
from agent.llm import OllamaLLM
from agent.react_agent import ChessAgent
from eval.harness import random_baseline
from tools.chess_tools import apply_move, check_legal


def ask_human(board: chess.Board) -> chess.Move:
    while True:
        text = input("Your move (SAN or UCI): ")
        check = check_legal(board, text)
        if check.legal:
            return check.move
        print(check.reason)


def main() -> None:
    parser = argparse.ArgumentParser(description="Play chess against a local LLM agent.")
    parser.add_argument("--color", choices=["white", "black"], default="white", help="your color")
    parser.add_argument("--opponent", choices=["human", "random"], default="human", help="who plays the agent")
    parser.add_argument("--max-plies", type=int, help="stop the game after this many plies")
    parser.add_argument("--model", help="Ollama model, overriding config.yaml")
    args = parser.parse_args()

    config = load_config()
    if args.model:
        config = replace(config, model=args.model)
    agent = ChessAgent(OllamaLLM(config), max_steps=config.max_steps)
    other_color = chess.WHITE if args.color == "white" else chess.BLACK
    rng = random.Random()

    board = chess.Board()
    while not board.is_game_over(claim_draw=True):
        if args.max_plies and board.ply() >= args.max_plies:
            print("Stopped at the ply limit.")
            break
        print(f"\n{board}\n")
        if board.turn == other_color:
            move = ask_human(board) if args.opponent == "human" else random_baseline(board, rng)
            print(f"{args.opponent}: {board.san(move)}")
        else:
            result = agent.choose_move(board)
            move = result.move
            print(f"agent: {board.san(move)} ({result.source}, {result.latency_s:.1f}s)")
        apply_move(board, move)

    print(f"\n{board}\nResult: {board.result(claim_draw=True)}")


if __name__ == "__main__":
    main()
