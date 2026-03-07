def get_system_prompt(deck_path=None, opponent_deck_path=None, workflow_type="pr_vs_past"):
    cmd_suffix = f" --deck-a {deck_path}" if deck_path else ""
    if opponent_deck_path:
        cmd_suffix += f" --deck-b {opponent_deck_path}"
    
    target_matches = "1000"
    
    if workflow_type == "pr_vs_past_deck":
        target_win_rate = "at least 1% higher than the previous version"
        validation_cmd = f"python vs_past_deck.py --deck_a {deck_path} --num_matches {target_matches} --league_decks_teacher train_data/teacher.csv"
    elif workflow_type == "student_deck_vs_teacher_deck":
        target_win_rate = "at least 1% higher than the previous version"
        # We assume deck_b is the teacher deck or league
        teacher_arg = f"--league_decks_teacher {opponent_deck_path}" if opponent_deck_path and opponent_deck_path.endswith(".csv") else f"--deck_b {opponent_deck_path}"
        validation_cmd = f"python vs_past_deck.py --deck_a {deck_path} {teacher_arg} --num_matches {target_matches} --threshold 0.01"
    else: # pr_vs_past
        target_win_rate = "51%"
        validation_cmd = f"python main.py vs-past --matches {target_matches}{cmd_suffix}"
    
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
3. Your ultimate goal is to achieve a win rate of {target_win_rate} over at least {target_matches} matches against the version of the opponent using the following command:
   `{validation_cmd}`
4. If you want to analyze a specific match in detail (e.g., to debug an error or see why you lost), use the following command:
   `python main.py vs-past-detail --deck-a [FAILING_DECK] --deck-b [OPPONENT_DECK] --seed [FAIL_SEED]`

You can change this prompt if you think it is useful.
"""

def get_task_prompt(goal, feedback=None, deck_path=None, deck_contents=None, opponent_deck_path=None, opponent_deck_contents=None, evaluation_log=None):
    prompt = f"""
GOAL: {goal}
"""
    if deck_path and deck_contents:
        prompt += f"\nTARGET DECK ({deck_path}):\n```\n{deck_contents}\n```\n"
        if opponent_deck_path and opponent_deck_contents:
            prompt += f"\nOPPONENT DECK ({opponent_deck_path}):\n```\n{opponent_deck_contents}\n```\n"
            prompt += f"Please take a strategy specifically tuned to win with {deck_path} against {opponent_deck_path}.\n"
        else:
            prompt += "Please take a strategy specifically tuned to win with this deck.\n"

    if feedback:
        prompt += f"\nFEEDBACK (Errors or Performance): {feedback}\nPlease improve the code based on this feedback."
    
    # We do not append the full evaluation log here as it often triggers an HTTP 400 Payload Too Large
    # error from the Jules API when combined with the large `candidate_player.py` file in the repo context.
    if evaluation_log:
        # Extract just the top lines (e.g. win rates) to provide a tiny hint without breaking limits
        summary = "\n".join(evaluation_log.split("\n")[:10])
        prompt += f"\nEVALUATION SUMMARY:\n```\n{summary}\n```"
        
    prompt += "\n\nWrite the `play(state, game)` function now."
    return prompt
