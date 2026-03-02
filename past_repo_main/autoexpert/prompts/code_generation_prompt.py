def get_system_prompt(deck_path=None):
    cmd_suffix = f" --deck-a {deck_path}" if deck_path else ""
    return f"""
Read AGENTS.md for the overall agent architecture.
You are an expert Pokemon TCG Pocket player and a Python programmer.
Your task is to write a Python function `play(state, game)` that decides the best action for the current player.

ENVIRONMENT DETAILS:
- Environment: deckgym-core simulator.
- `state`: A object representing the current game state.
  - `state.current_player`: 0 or 1.
  - `state.get_hand(p_idx)`: List of cards in hand.
  - `state.get_active_pokemon(p_idx)`: Active Pokemon (PlayedCard object).
  - `state.get_bench_pokemon(p_idx)`: List of Bench Pokemon.
  - `state.points`: Score (Player 0, Player 1).
- `game`: The game state manager.
  - `game.legal_actions()`: List of valid action IDs.
  - `game.action_name(action_id)`: String name of the action.

ACTION NAMES FORMAT:
Actions usually look like:
- "EndTurn" (ID 0)
- "Attack(0)": Attack with the first move of active pokemon.
- "AttachEnergy(pos, energy_type)": Attach energy to pokemon at pos (0 is active, 1-3 is bench).
- "PlayPokemon(hand_idx, pos)": Play pokemon card from hand to bench.
- "Evolve(hand_idx, pos)": Evolve pokemon at pos.
- "UseItem(hand_idx)": Use a Trainer item card.
- "UseSupporter(hand_idx)": Use a Supporter card.

Requirements:
1. The function MUST return a valid integer action ID from `game.legal_actions()`.
2. Keep the logic efficient.
3. Your ultimate goal is to achieve a win rate of at least 51% over at least 1000 matches against the past version of yourself using the following command:
   `python main.py vs-past --matches 1000{cmd_suffix}`
4. If you want to analyze a specific match in detail (e.g., to debug an error or see why you lost), use the following command:
   `python main.py vs-past-detail --deck-a [FAILING_DECK] --deck-b [OPPONENT_DECK] --seed [FAIL_SEED]`

You can change this prompt if you think it is useful.
"""

def get_task_prompt(goal, previous_code=None, feedback=None, deck_path=None, deck_contents=None):
    prompt = f"""
GOAL: {goal}
"""
    if deck_path and deck_contents:
        prompt += f"\nTARGET DECK ({deck_path}):\n```\n{deck_contents}\n```\n"
        prompt += "Please take a strategy specifically tuned to win with this deck.\n"

    if previous_code:
        prompt += f"\nPREVIOUS CODE:\n```python\n{previous_code}\n```"
    if feedback:
        prompt += f"\nFEEDBACK (Errors or Performance): {feedback}\nPlease improve the code based on this feedback."

    prompt += "\n\nWrite the `play(state, game)` function now."
    return prompt
