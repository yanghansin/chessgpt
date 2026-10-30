# chessgpt

A chess agent that runs on local LLMs through Ollama. The model proposes moves in a ReAct-style loop, python-chess checks them, and guardrails make sure nothing illegal ever reaches the board.

## Tech stack

Python 3.11+, [python-chess](https://python-chess.readthedocs.io/), and [Ollama](https://ollama.com/). No cloud APIs are involved.

| Folder | What it does |
| --- | --- |
| `agent/` | ReAct loop, prompt templates, Ollama wrapper, and config |
| `tools/` | python-chess legality checker and move execution |
| `guardrails/` | Output schema validation, pre-execution verification, and a deterministic fallback |
| `eval/` | Eval harness that plays against a random baseline and writes to `eval/results/` |
| `cli.py` | Play a game from the terminal |

## How it works

On each turn the model replies with JSON containing a thought, an action, and a move:

1. `check_move` asks whether a move is legal, and the result goes back to the model.
2. `play` submits a move, which is verified before it is played.
3. An illegal move or a malformed reply is reported back to the model, along with the legal moves when the move was illegal.
4. If the model has no legal move after `max_steps` attempts, a deterministic fallback plays instead. It takes checkmate if available, then the biggest material gain.

## How to run

Install [Ollama](https://ollama.com/download), then pull the default model (about 4.4 GB):

```bash
ollama pull mistral
```

Set up the project:

```bash
git clone https://github.com/yanghansin/chessgpt.git
cd chessgpt
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Play, test, and evaluate:

```bash
python cli.py                            # play as White against the agent
python cli.py --color black              # play as Black
python cli.py --opponent random          # watch the agent play the random baseline
pytest                                   # no Ollama needed
python -m eval.harness --games 2         # needs Ollama, writes to eval/results/
```

### Configuration

Settings live in [`config.yaml`](config.yaml): `model`, `temperature`, `max_tokens`, and `max_steps`. The environment variables `CHESSGPT_MODEL`, `CHESSGPT_TEMPERATURE`, `CHESSGPT_MAX_TOKENS`, and `CHESSGPT_MAX_STEPS` override them.

## Results so far

The only run so far is a smoke test that confirms the harness works: [2 games against the random baseline](eval/results/20261030T165852Z-mistral.json) with `mistral`, stopped at 24 plies each. **Both games were unfinished, so this says nothing about playing strength.**

| Metric | Value |
| --- | --- |
| Win rate | 0 of 2 (both games unfinished) |
| Illegal-move rate | 54.7% (35 of 64 proposals) |
| Moves decided by the fallback | 25% (6 of 24) |
| Tokens per move | 1,244 |
| Latency per move | 4.1 s |

The illegal-move rate counts every proposal the model made, including `check_move` requests. Those moves were caught before reaching the board.

## Project status

The agent, guardrails, CLI, and harness all work, and the tests pass. A full evaluation hasn't been run yet.

## Roadmap

- Run a full evaluation with complete games.
- Compare models and prompt variations.
- Add a stronger baseline than random moves.

## License

[MIT](LICENSE)
