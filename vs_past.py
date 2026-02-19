import argparse
import sys
import os
import random
import datetime
import logging
import traceback
import deckgym
from pathlib import Path
from typing import Dict, Any, List, Optional

# Set up paths for imports
sys.path.append(os.getcwd())

from autoexpert.skill_library import SkillLibrary
from autoexpert.config import settings
from show_battle import extract_state_info, generate_html

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_args():
    parser = argparse.ArgumentParser(description="Battle between Current Expert and Past Expert.")
    parser.add_argument("--past_dir", type=str, default="past_repo", help="Path to the past repository.")
    parser.add_argument("--deck_a", type=str, default="mewtwoex.txt", help="Path to deck 1 file.")
    parser.add_argument("--deck_b", type=str, default="mewtwoex.txt", help="Path to deck 2 file.")
    parser.add_argument("--output", type=str, default="vs_past_battle.html", help="Path to output HTML file.")
    parser.add_argument("--seed", type=int, default=int(datetime.datetime.now().timestamp()), help="Random seed.")
    parser.add_argument("--num_matches", type=int, default=1, help="Number of matches to run (only last one visualized).")
    return parser.parse_args()

def get_play_func(skill_data: Optional[Dict[str, Any]]):
    if not skill_data:
        logging.warning("No skill data provided. Using random strategy.")
        def play_func(state, game):
            return random.choice(game.legal_actions())
        return play_func
    
    code = skill_data["code"]
    local_vars = {}
    try:
        exec(code, {"deckgym": deckgym}, local_vars)
        play_func = local_vars.get("play")
        if not play_func:
            raise ValueError("No 'play' function found in skill code.")
        return play_func
    except Exception as e:
        logging.error(f"Error executing skill code: {e}")
        def play_func(state, game):
            return random.choice(game.legal_actions())
        return play_func

def run_match(game, play_funcs, record_history=False):
    history = []
    max_steps = 300
    step_count = 0
    
    while not game.get_state().is_game_over() and step_count < max_steps:
        state = game.get_state()
        current_player = state.current_player
        
        if record_history:
            info = extract_state_info(state)
            info["acting_player"] = current_player
        
        # Get action from the corresponding player's play_func
        try:
            action_id = play_funcs[current_player](state, game)
            action_name = game.action_name(action_id)
        except Exception as e:
            logging.error(f"Error during play_func: {e}")
            action_id = random.choice(game.legal_actions())
            action_name = f"ERROR_FALLBACK: {game.action_name(action_id)}"
            
        if record_history:
            info["action_name"] = action_name
            history.append(info)
        
        game.step_with_id(action_id)
        step_count += 1
        
    final_state = game.get_state()
    if record_history:
        final_info = extract_state_info(final_state)
        final_info["acting_player"] = final_state.current_player
        final_info["action_name"] = "Game Over"
        history.append(final_info)
    
    # winner is a PyGameOutcome or similar
    winner_val = -1
    outcome = final_state.winner
    import re
    if hasattr(outcome, "winner"):
        winner_val = outcome.winner
    else:
        match = re.search(r"Win\((\d+)\)", str(outcome))
        if match:
            winner_val = int(match.group(1))
            
    return winner_val, history

def main():
    args = parse_args()
    
    # 1. Load Current Best Skill
    current_library = SkillLibrary()
    current_best = current_library.get_best_skill()
    if current_best:
        logging.info(f"Current Best Skill: {current_best['name']} (Win Rate: {current_best['win_rate']:.2%})")
    else:
        logging.info("Current Library is empty. Using random strategy for Player 0.")
        
    # 2. Load Past Best Skill
    past_skill_dir = Path(args.past_dir) / "skill_library"
    past_library = SkillLibrary(directory=past_skill_dir)
    past_best = past_library.get_best_skill()
    if past_best:
        logging.info(f"Past Best Skill: {past_best['name']} (Win Rate: {past_best['win_rate']:.2%})")
    else:
        logging.info(f"Past Library ({past_skill_dir}) is empty. Using random strategy for Player 1.")

    play_funcs = [
        get_play_func(current_best),
        get_play_func(past_best)
    ]

    deck_a_path = str(settings.DECK_DIR / args.deck_a)
    deck_b_path = str(settings.DECK_DIR / args.deck_b)
    
    wins = [0, 0]
    last_history = []
    
    for i in range(args.num_matches):
        seed = args.seed + i
        logging.info(f"Starting Match {i+1}/{args.num_matches} (Seed: {seed})")
        game = deckgym.PyGameState(deck_a_path, deck_b_path, seed)
        
        winner, history = run_match(game, play_funcs, record_history=(i == args.num_matches - 1))
        
        if winner != -1:
            wins[winner] += 1
            logging.info(f"Match {i+1} Winner: Player {winner} ({'Current' if winner == 0 else 'Past'})")
        else:
            logging.info(f"Match {i+1} ended in a draw/limit.")
            
        if i == args.num_matches - 1:
            last_history = history

    print("\n--- Battle Results ---")
    print(f"Current (P0) Wins: {wins[0]}")
    print(f"Past (P1) Wins: {wins[1]}")
    if sum(wins) > 0:
        print(f"Current Win Rate: {wins[0] / sum(wins):.2%}")

    # Generate HTML for the last match
    generate_html(last_history, args.output)
    print(f"\nLast match visualization saved to: {args.output}")

if __name__ == "__main__":
    main()
