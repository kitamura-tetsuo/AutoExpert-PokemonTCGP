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
    parser.add_argument("--repo_url", type=str, default="https://github.com/kitamura-tetsuo/AutoExpert-PokemonTCGP", help="URL of the past repository to clone.")
    parser.add_argument("--deck_a", type=str, default="mewtwoex.txt", help="Path to deck 1 file.")
    parser.add_argument("--deck_b", type=str, default="mewtwoex.txt", help="Path to deck 2 file.")
    parser.add_argument("--output", type=str, default="vs_past_battle.html", help="Path to output HTML file.")
    parser.add_argument("--seed", type=int, default=int(datetime.datetime.now().timestamp()), help="Random seed.")
    parser.add_argument("--num_matches", type=int, default=1, help="Number of matches to run (only last one visualized).")
    parser.add_argument("--league_decks_student", type=str, default="train_data/teacher.csv", help="CSV file for student league decks")
    parser.add_argument("--league_decks_teacher", type=str, default="train_data/teacher.csv", help="CSV file for teacher league decks")
    return parser.parse_args()

def ensure_past_repo(past_dir: str, repo_url: str):
    path = Path(past_dir)
    if not path.exists():
        logging.info(f"Past repository not found at {past_dir}. Downloading from {repo_url}...")
        import subprocess
        import shutil
        try:
            # zip_url is like https://github.com/kitamura-tetsuo/AutoExpert-PokemonTCGP/archive/refs/heads/main.zip
            zip_url = f"{repo_url.rstrip('/')}/archive/refs/heads/main.zip"
            zip_path = Path("repo_temp.zip")
            
            logging.info(f"Downloading ZIP from {zip_url}...")
            subprocess.run(["curl", "-L", "-o", str(zip_path), zip_url], check=True)
            
            logging.info("Extracting ZIP...")
            subprocess.run(["unzip", "-q", str(zip_path)], check=True)
            
            # The unzipped folder name is usually {repo_name}-{branch}
            repo_name = repo_url.rstrip("/").split("/")[-1]
            # Try main branch first
            unzipped_dirs = list(Path(".").glob(f"{repo_name}-*"))
            if not unzipped_dirs:
                raise Exception(f"Could not find unzipped directory starting with {repo_name}-")
            
            unzipped_dir = unzipped_dirs[0]
            unzipped_dir.rename(past_dir)
            zip_path.unlink()
            logging.info("Download and extraction successful.")
        except Exception as e:
            logging.error(f"Failed to download repository: {e}")
            # Fallback to depth 1 clone if download fails
            logging.info("Falling back to shallow clone...")
            try:
                subprocess.run(["git", "clone", "--depth", "1", repo_url, past_dir], check=True)
                logging.info("Shallow clone successful.")
            except subprocess.CalledProcessError as e2:
                logging.error(f"Failed to clone repository: {e2}")
                sys.exit(1)
    else:
        logging.info(f"Using existing past repository at {past_dir}")

def get_play_func(skill_data: Optional[Dict[str, Any]]):
    if not skill_data:
        logging.warning("No skill data provided. Using random strategy.")
        def play_func(state, game):
            return random.choice(game.legal_actions())
        return play_func
    
    code = skill_data["code"]
    namespace = {"deckgym": deckgym}
    try:
        exec(code, namespace)
        play_func = namespace.get("play")
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
            
    return winner_val, history, step_count

def load_league_decks(csv_path: str):
    if not csv_path:
        return None, None
    
    import csv
    decks = []
    weights = []
    
    try:
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Assuming signature column contains the deck filename without .txt
                # and lower_ci contains the weight
                sig = row['signature']
                weight = float(row['lower_ci'])
                decks.append(f"{sig}.txt")
                weights.append(weight)
    except Exception as e:
        logging.error(f"Error loading league decks from {csv_path}: {e}")
        return None, None
        
    return decks, weights

def main():
    args = parse_args()
    
    # Ensure past repository exists
    ensure_past_repo(args.past_dir, args.repo_url)
    
    # 1. Load Current Best Skill (Use candidate_player directly)
    try:
        import candidate_player
        import importlib
        importlib.reload(candidate_player)
        current_best_func = candidate_player.play
        logging.info("Using candidate_player.play for Player 0.")
    except ImportError:
        logging.error("Could not import candidate_player. Using random strategy.")
        def current_best_func(state, game):
            return random.choice(game.legal_actions())

    # 2. Load Past Best Skill
    past_skill_dir = Path(args.past_dir) / "skill_library"
    past_library = SkillLibrary(directory=past_skill_dir)
    past_best = past_library.get_best_skill()
    if past_best:
        logging.info(f"Past Best Skill: {past_best['name']} (Win Rate: {past_best['win_rate']:.2%})")
    else:
        logging.info(f"Past Library ({past_skill_dir}) is empty. Using random strategy for Player 1.")

    play_funcs = [
        current_best_func,
        get_play_func(past_best)
    ]

    # Handle League Decks
    student_decks, student_weights = load_league_decks(args.league_decks_student)
    teacher_decks, teacher_weights = load_league_decks(args.league_decks_teacher)

    wins = [0, 0]
    last_history = []
    
    longest_loss = {"steps": -1, "seed": None, "deck_a": None, "deck_b": None}
    shortest_loss = {"steps": float('inf'), "seed": None, "deck_a": None, "deck_b": None}
    
    for i in range(args.num_matches):
        seed = args.seed + i
        
        # Select decks
        if student_decks and student_weights:
            deck_a = random.choices(student_decks, weights=student_weights, k=1)[0]
        else:
            deck_a = args.deck_a
            
        if teacher_decks and teacher_weights:
            deck_b = random.choices(teacher_decks, weights=teacher_weights, k=1)[0]
        else:
            deck_b = args.deck_b

        deck_a_path = str(settings.DECK_DIR / deck_a)
        deck_b_path = str(settings.DECK_DIR / deck_b)
        
        # Check if decks exist in current repo (fallback to train_data if not in deckgym-core/example_decks)
        if not Path(deck_a_path).exists():
            deck_a_path = str(Path("train_data") / deck_a)
        if not Path(deck_b_path).exists():
            deck_b_path = str(Path("train_data") / deck_b)

        logging.info(f"Starting Match {i+1}/{args.num_matches} (Seed: {seed})")
        logging.info(f"Decks: P0: {deck_a} vs P1: {deck_b}")
        
        try:
            game = deckgym.PyGameState(deck_a_path, deck_b_path, seed)
            winner, history, steps = run_match(game, play_funcs, record_history=(i == args.num_matches - 1))
        except Exception as e:
            logging.error(f"Failed to start match: {e}")
            continue
        
        if winner != -1:
            wins[winner] += 1
            logging.info(f"Match {i+1} Winner: Player {winner} ({'Current' if winner == 0 else 'Past'}) in {steps} steps")
            
            # Track loss (Player 1 won)
            if winner == 1:
                if steps > longest_loss["steps"]:
                    longest_loss = {"steps": steps, "seed": seed, "deck_a": deck_a, "deck_b": deck_b}
                if steps < shortest_loss["steps"]:
                    shortest_loss = {"steps": steps, "seed": seed, "deck_a": deck_a, "deck_b": deck_b}
        else:
            logging.info(f"Match {i+1} ended in a draw/limit after {steps} steps.")
            
        if i == args.num_matches - 1:
            last_history = history

    print("\n--- Battle Results ---")
    print(f"Current (P0) Wins: {wins[0]}")
    print(f"Past (P1) Wins: {wins[1]}")
    if sum(wins) > 0:
        print(f"Current Win Rate: {wins[0] / sum(wins):.2%}")

    if wins[1] > 0:
        print("\n--- Loss Analysis (P1 Victory) ---")
        print(f"Longest Loss:  {longest_loss['steps']} steps (Seed: {longest_loss['seed']})")
        print(f"  Decks: P0: {longest_loss['deck_a']} vs P1: {longest_loss['deck_b']}")
        print(f"Shortest Loss: {shortest_loss['steps']} steps (Seed: {shortest_loss['seed']})")
        print(f"  Decks: P0: {shortest_loss['deck_a']} vs P1: {shortest_loss['deck_b']}")

    # Generate HTML for the last match
    generate_html(last_history, args.output)
    print(f"\nLast match visualization saved to: {args.output}")

if __name__ == "__main__":
    main()
