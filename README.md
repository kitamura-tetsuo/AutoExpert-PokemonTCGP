# AutoExpert-PokemonTCGP

A Voyager-like expert system that automatically constructs and improves Pokemon TCG Pocket gameplay strategies using LLMs (Jules API).

## Features
- **Curriculum Manager**: Automatically decides the next strategic goal for the agent.
- **Code Generator**: Uses Google's Jules API to write Python strategy code based on game state observations.
- **Skill Library**: Stores and manages successful strategies (skills) as reusable code.
- **Automated Verification**: Runs 1000+ simulations via `deckgym-core` to evaluate the performance of generated strategies.

## Requirements
- Python 3.11+
- Rust (for deckgym-core)
- `uv` for package management
- Jules API Key (set in `.env` as `JULES_API_KEY`)

## Installation
1. Ensure `deckgym-core` is built:
   ```bash
   cd deckgym-core
   uv sync
   maturin develop --features python
   ```
2. Setup AutoExpert:
   ```bash
   uv sync
   ```

## Usage
### Start Learning
To start the automatic construction and improvement process:
```bash
python main.py learn --max-iter 10
```
This will iterate 10 times, each time trying to improve a specific strategic goal.

### View Learned Skills
```bash
python main.py skills
```

### Match Against Past Code
To compare the current best expert against an expert from a past version of the repository:
```bash
python main.py vs-past --past-dir past_repo --matches 5
```
This will run 5 matches between the current best skill and the best skill in `past_repo/skill_library`, and generate a visualization of the last match.

### Detailed Battle Analysis (for LLM)
To examine the game state encoding and actions step-by-step for a specific match:
```bash
python main.py vs-past-detail --deck-a mewtwoex.txt --deck-b mewtwoex.txt --seed 4250
```
This command outputs the detailed internal state (encoded observation) and available actions for each step, which is useful for LLM debugging and understanding the Deep Learning model's input.

## Structure
- `autoexpert/autoexpert.py`: Main loop.
- `autoexpert/utils/llm_client.py`: Jules API interface.
- `autoexpert/env.py`: Simulator wrapper.
- `skill_library/`: JSON files containing learned python code.
