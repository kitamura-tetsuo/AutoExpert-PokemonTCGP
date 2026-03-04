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
    parser.add_argument("--deck_a", type=str, help="Path to deck 1 file.")
    parser.add_argument("--deck_b", type=str, help="Path to deck 2 file.")
    parser.add_argument("--output", type=str, default="vs_past_battle.html", help="Path to output HTML file.")
    parser.add_argument("--seed", type=int, default=int(datetime.datetime.now().timestamp()), help="Random seed.")
    parser.add_argument("--num_matches", type=int, default=1, help="Number of matches to run (only last one visualized).")
    parser.add_argument("--threshold", type=float, default=0.51, help="Win rate threshold to pass.")
    parser.add_argument("--league_decks_student", type=str, default="train_data/teacher.csv", help="CSV file for student league decks")
    parser.add_argument("--league_decks_teacher", type=str, default="train_data/teacher.csv", help="CSV file for teacher league decks")
    return parser.parse_args()

def get_past_repo_path(base_dir: str, branch: str) -> Path:
    return Path(f"{base_dir}_{branch.replace('/', '_')}")

def ensure_past_repo(base_dir: str, repo_url: str, branch: str = "main") -> Path:
    past_dir = get_past_repo_path(base_dir, branch)
    if past_dir.exists():
        logging.info(f"Using existing past repository at {past_dir}")
        return past_dir
        
    logging.info(f"Past repository for branch '{branch}' not found at {past_dir}. Downloading from {repo_url}...")
    import subprocess
    import shutil
    try:
        zip_url = f"{repo_url.rstrip('/')}/archive/refs/heads/{branch}.zip"
        zip_path = Path(f"repo_temp_{branch.replace('/', '_')}.zip")
        
        logging.info(f"Downloading ZIP from {zip_url}...")
        res = subprocess.run(["curl", "-s", "-L", "-w", "%{http_code}", "-o", str(zip_path), zip_url], capture_output=True, text=True, check=True)
        if res.stdout.strip() == "404":
            if zip_path.exists():
                zip_path.unlink()
            raise Exception(f"Branch {branch} not found (404)")
            
        logging.info("Extracting ZIP...")
        subprocess.run(["unzip", "-q", str(zip_path)], check=True)
        
        repo_name = repo_url.rstrip("/").split("/")[-1]
        unzipped_dirs = list(Path(".").glob(f"{repo_name}-{branch.replace('/', '-')}*"))
        if not unzipped_dirs:
            unzipped_dirs = list(Path(".").glob(f"*-{branch.replace('/', '-')}*"))
            if not unzipped_dirs:
                raise Exception(f"Could not find unzipped directory for branch {branch}")
        
        unzipped_dir = unzipped_dirs[0]
        unzipped_dir.rename(past_dir)
        if zip_path.exists():
            zip_path.unlink()
        logging.info(f"Download and extraction successful for branch {branch}.")
        return past_dir
    except Exception as e:
        logging.error(f"Failed to download repository for branch {branch}: {e}")
        if branch != "main":
            logging.info("Falling back to main branch...")
            return ensure_past_repo(base_dir, repo_url, "main")
        else:
            logging.info("Falling back to shallow clone...")
            try:
                subprocess.run(["git", "clone", "--depth", "1", "-b", branch, repo_url, str(past_dir)], check=True)
                logging.info("Shallow clone successful.")
                return past_dir
            except subprocess.CalledProcessError as e2:
                logging.error(f"Failed to clone repository: {e2}")
                sys.exit(1)

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

past_funcs_cache = {}

def get_past_func_for_branch(base_dir: str, repo_url: str, branch: str):
    if branch in past_funcs_cache:
        return past_funcs_cache[branch]

    past_dir = ensure_past_repo(base_dir, repo_url, branch)
    
    past_candidate_path = past_dir / "candidate_player.py"
    past_best_func = None

    if past_candidate_path.exists():
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(f"past_candidate_player_{branch.replace('/', '_')}", str(past_candidate_path))
            past_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(past_module)
            past_best_func = past_module.play
            logging.info(f"Using candidate_player.play from branch {branch} for Player 1.")
        except Exception as e:
            logging.error(f"Error loading past candidate player for branch {branch}: {e}")

    if not past_best_func:
        past_skill_dir = past_dir / "skill_library"
        if past_skill_dir.exists():
            past_library = SkillLibrary(directory=past_skill_dir)
            past_best = past_library.get_best_skill()
            if past_best:
                logging.info(f"Past Best Skill from library ({branch}): {past_best['name']} (Win Rate: {past_best.get('win_rate', 0):.2%})")
                past_best_func = get_play_func(past_best)
            else:
                logging.info(f"Past Library ({past_skill_dir}) is empty.")
        else:
            logging.info(f"Past Library ({past_skill_dir}) not found.")

    if not past_best_func:
        logging.info(f"Using random strategy for Player 1 (branch {branch}).")
        past_best_func = get_play_func(None)

    past_funcs_cache[branch] = past_best_func
    return past_best_func

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
    
    # Check if deck_a exists
    deck_a_resolved = False
    if args.deck_a:
        for base in [Path("."), settings.DECK_DIR, Path("train_data")]:
            if (base / args.deck_a).exists():
                deck_a_resolved = True
                break

    if deck_a_resolved:
        logging.info(f"deck_a ({args.deck_a}) exists. Ignoring league_decks_student.")
        student_decks, student_weights = None, None
    else:
        logging.info(f"deck_a ({args.deck_a}) does not exist. Using league_decks_student.")
        student_decks, student_weights = load_league_decks(args.league_decks_student)

    teacher_decks, teacher_weights = load_league_decks(args.league_decks_teacher)
    
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

    # Past best func will be loaded dynamically per match based on deck


    # Silence player logs during bulk matches to prevent CI timeout/log overflow
    logging.getLogger("player").setLevel(logging.WARNING)
    logging.getLogger().setLevel(logging.WARNING)

    wins = [0, 0]
    last_history = []
    
    draws = 0
    longest_loss = {"steps": -1, "seed": None, "deck_a": None, "deck_b": None}
    shortest_loss = {"steps": float('inf'), "seed": None, "deck_a": None, "deck_b": None}
    longest_draw = {"steps": -1, "seed": None, "deck_a": None, "deck_b": None}
    
    for i in range(args.num_matches):
        seed = args.seed + i
        random.seed(seed)
        
        # Select decks
        if student_decks and student_weights:
            deck_a = random.choices(student_decks, weights=student_weights, k=1)[0]
        else:
            deck_a = args.deck_a
            
        if teacher_decks and teacher_weights:
            deck_b = random.choices(teacher_decks, weights=teacher_weights, k=1)[0]
        else:
            deck_b = args.deck_b

        deck_a_path = Path(deck_a)
        if not deck_a_path.exists():
            deck_a_path = settings.DECK_DIR / deck_a
        if not deck_a_path.exists():
            deck_a_path = Path("train_data") / deck_a
            
        deck_b_path = Path(deck_b)
        if not deck_b_path.exists():
            deck_b_path = settings.DECK_DIR / deck_b
        if not deck_b_path.exists():
            deck_b_path = Path("train_data") / deck_b

        deck_a_path = str(deck_a_path)
        deck_b_path = str(deck_b_path)

        # Get past func for deck_b branch
        branch_name = Path(deck_b).stem  # Removes .txt and gets filename only
        past_best_func = get_past_func_for_branch(args.past_dir, args.repo_url, branch_name)

        play_funcs = [
            current_best_func,
            past_best_func
        ]

        logging.info(f"Starting Match {i+1}/{args.num_matches} (Seed: {seed})")
        logging.info(f"Decks: P0: {deck_a} vs P1: {deck_b}")
        
        try:
            game = deckgym.PyGameState(deck_a_path, deck_b_path, seed)
            winner, history, steps = run_match(game, play_funcs, record_history=(i == args.num_matches - 1))
        except Exception as e:
            logging.error(f"Failed to start match: {e}")
            continue
        
        if winner is not None and winner != -1:
            wins[winner] += 1
            logging.info(f"Match {i+1} Winner: Player {winner} ({'Current' if winner == 0 else 'Past'}) in {steps} steps")
            
            # Track loss (Player 1 won)
            if winner == 1:
                if steps > longest_loss["steps"]:
                    longest_loss = {"steps": steps, "seed": seed, "deck_a": deck_a, "deck_b": deck_b}
                if steps < shortest_loss["steps"]:
                    shortest_loss = {"steps": steps, "seed": seed, "deck_a": deck_a, "deck_b": deck_b}
        else:
            draws += 1
            logging.info(f"Match {i+1} ended in a draw/limit after {steps} steps.")
            if steps > longest_draw["steps"]:
                longest_draw = {"steps": steps, "seed": seed, "deck_a": deck_a, "deck_b": deck_b}
            
        if i == args.num_matches - 1:
            last_history = history

    total_matches = sum(wins) + draws
    win_rate = wins[0] / total_matches if total_matches > 0 else 0

    print("\n--- Battle Results ---")
    print(f"Current (P0) Wins: {wins[0]}")
    print(f"Past (P1) Wins: {wins[1]}")
    print(f"Draws: {draws}")
    if total_matches > 0:
        print(f"Current Win Rate: {wins[0] / total_matches:.2%}")

    if wins[1] > 0:
        print("\n--- Loss Analysis (P1 Victory) ---")
        print(f"Longest Loss:  {longest_loss['steps']} steps (Seed: {longest_loss['seed']})")
        print(f"  Decks: P0: {longest_loss['deck_a']} vs P1: {longest_loss['deck_b']}")
        print(f"Shortest Loss: {shortest_loss['steps']} steps (Seed: {shortest_loss['seed']})")
        print(f"  Decks: P0: {shortest_loss['deck_a']} vs P1: {shortest_loss['deck_b']}")

    if longest_draw["steps"] != -1:
        print("\n--- Draw Analysis ---")
        print(f"Longest Draw: {longest_draw['steps']} steps (Seed: {longest_draw['seed']})")
        print(f"  Decks: P0: {longest_draw['deck_a']} vs P1: {longest_draw['deck_b']}")

    # Generate HTML for the last match
    generate_html(last_history, args.output, seed)
    print(f"\nLast match visualization saved to: {args.output}")

    # CI check logic
    if args.num_matches < 1000:
        logging.error(f"Number of matches ({args.num_matches}) is less than 1000. Failing CI.")
        sys.exit(1)
    
    if win_rate < args.threshold:
        logging.error(f"Win rate ({win_rate:.2%}) is below threshold ({args.threshold:.2%}). Failing CI.")
        sys.exit(1)
    
    logging.info("CI check passed.")

if __name__ == "__main__":
    main()
