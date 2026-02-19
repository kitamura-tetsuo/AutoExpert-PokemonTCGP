# AutoExpert-PokemonTCGP

A Voyager-like expert system that automatically constructs and improves Pokemon TCG Pocket gameplay strategies using LLMs (Jules API).

## Features
- **Curriculum Manager**: Automatically decides the next strategic goal for the agent.
- **Code Generator**: Uses Google's Jules API to write Python strategy code based on game state observations.
- **Skill Library**: Stores and manages successful strategies (skills) as reusable code.
- **Automated Verification**: Runs 100+ simulations via `deckgym-core` to evaluate the performance of generated strategies.

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

## Structure
- `autoexpert/autoexpert.py`: Main loop.
- `autoexpert/utils/llm_client.py`: Jules API interface.
- `autoexpert/env.py`: Simulator wrapper.
- `skill_library/`: JSON files containing learned python code.
