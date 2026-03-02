"""
vs_past_deck.py - Deck-specialized AI evaluation against teacher league.

Evaluation method:
  Both the new AI (current candidate_player.py) and the old AI (1 commit before,
  placed in past_repo_main/) independently play 1000 matches against the teacher
  league using identical seeds (same opponent decks, same RNG state per match).

  Pass condition: new AI win rate - old AI win rate >= threshold (default: 1%).
"""

import argparse
import sys
import os
import random
import datetime
import logging
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
    parser = argparse.ArgumentParser(
        description="Deck-specialized AI evaluation: new vs old AI against teacher league."
    )
    parser.add_argument("--past_dir", type=str, default="past_repo",
                        help="Base path for past repository (branch suffix appended automatically).")
    parser.add_argument("--repo_url", type=str,
                        default="https://github.com/kitamura-tetsuo/AutoExpert-PokemonTCGP",
                        help="URL of the past repository to clone if not found locally.")
    parser.add_argument("--deck_a", type=str, required=True,
                        help="Path to student deck file (fixed for all matches).")
    parser.add_argument("--output", type=str, default="vs_past_deck_battle.html",
                        help="Path to output HTML file (last match of new AI).")
    parser.add_argument("--seed", type=int, default=int(datetime.datetime.now().timestamp()),
                        help="Base random seed. Match i uses seed+i for both AIs.")
    parser.add_argument("--num_matches", type=int, default=1000,
                        help="Number of matches per AI.")
    parser.add_argument("--threshold", type=float, default=0.01,
                        help="Minimum win rate improvement (new - old) to pass CI (default: 0.01 = 1%%).")
    parser.add_argument("--league_decks_teacher", type=str, default="train_data/teacher.csv",
                        help="CSV file for teacher league decks.")
    parser.add_argument("--deck_b", type=str, default=None,
                        help="Path to a specific teacher deck file (optional, overrides league).")
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Repository helpers (shared pattern with vs_past.py)
# ---------------------------------------------------------------------------

def get_past_repo_path(base_dir: str, branch: str) -> Path:
    return Path(f"{base_dir}_{branch.replace('/', '_')}")


def ensure_past_repo(base_dir: str, repo_url: str, branch: str = "main") -> Path:
    past_dir = get_past_repo_path(base_dir, branch)
    if past_dir.exists():
        logging.info(f"Using existing past repository at {past_dir}")
        return past_dir

    logging.info(f"Past repository for branch '{branch}' not found at {past_dir}. Downloading from {repo_url}...")
    import subprocess
    try:
        zip_url = f"{repo_url.rstrip('/')}/archive/refs/heads/{branch}.zip"
        zip_path = Path(f"repo_temp_{branch.replace('/', '_')}.zip")

        logging.info(f"Downloading ZIP from {zip_url}...")
        res = subprocess.run(
            ["curl", "-s", "-L", "-w", "%{http_code}", "-o", str(zip_path), zip_url],
            capture_output=True, text=True, check=True
        )
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

        unzipped_dirs[0].rename(past_dir)
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
                subprocess.run(
                    ["git", "clone", "--depth", "1", "-b", branch, repo_url, str(past_dir)],
                    check=True
                )
                logging.info("Shallow clone successful.")
                return past_dir
            except subprocess.CalledProcessError as e2:
                logging.error(f"Failed to clone repository: {e2}")
                sys.exit(1)


def get_play_func(skill_data: Optional[Dict[str, Any]]):
    if not skill_data:
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


def load_past_func(base_dir: str, repo_url: str, branch: str = "main"):
    """Load play function from a past repository (or worktree placed at past_repo_main)."""
    past_dir = ensure_past_repo(base_dir, repo_url, branch)

    past_candidate_path = past_dir / "candidate_player.py"
    if past_candidate_path.exists():
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                f"past_candidate_player_{branch.replace('/', '_')}", str(past_candidate_path)
            )
            past_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(past_module)
            logging.info(f"Using candidate_player.play from branch '{branch}' for old AI.")
            return past_module.play
        except Exception as e:
            logging.error(f"Error loading past candidate player for branch '{branch}': {e}")

    past_skill_dir = past_dir / "skill_library"
    if past_skill_dir.exists():
        past_library = SkillLibrary(directory=past_skill_dir)
        past_best = past_library.get_best_skill()
        if past_best:
            logging.info(
                f"Past Best Skill from library ('{branch}'): "
                f"{past_best['name']} (Win Rate: {past_best.get('win_rate', 0):.2%})"
            )
            return get_play_func(past_best)

    logging.warning(f"Using random strategy for old AI (branch '{branch}').")
    return get_play_func(None)


# ---------------------------------------------------------------------------
# Game helpers
# ---------------------------------------------------------------------------

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

    winner_val = -1
    outcome = final_state.winner
    import re
    if hasattr(outcome, "winner"):
        winner_val = outcome.winner
    else:
        m = re.search(r"Win\((\d+)\)", str(outcome))
        if m:
            winner_val = int(m.group(1))

    return winner_val, history, step_count


def load_league_decks(csv_path: str):
    if not csv_path:
        return None, None

    import csv
    decks, weights = [], []
    try:
        with open(csv_path, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sig = row['signature']
                weight = float(row['lower_ci'])
                decks.append(f"{sig}.txt")
                weights.append(weight)
    except Exception as e:
        logging.error(f"Error loading league decks from {csv_path}: {e}")
        return None, None

    return decks, weights


def resolve_deck_path(deck: str) -> str:
    deck_path = Path(deck)
    if not deck_path.exists():
        deck_path = settings.DECK_DIR / deck
    if not deck_path.exists():
        deck_path = Path("train_data") / deck
    return str(deck_path)


# ---------------------------------------------------------------------------
# League series runner
# ---------------------------------------------------------------------------

def run_league_series(play_func, deck_a: str, teacher_decks, teacher_weights,
                      num_matches: int, base_seed: int, label: str):
    """Run num_matches games: play_func (student, P0) vs teacher league (P1).

    For match i:
      - seed = base_seed + i
      - Teacher deck selected via Random(seed) (same RNG state for new and old AI)
      - Game initialized with the same seed

    Returns (wins, draws, completed, last_history).
    """
    wins = 0
    draws = 0
    completed = 0
    last_history = []

    for i in range(num_matches):
        seed = base_seed + i
        rng = random.Random(seed)

        # Select teacher deck deterministically
        deck_b = rng.choices(teacher_decks, weights=teacher_weights, k=1)[0]

        deck_a_path = resolve_deck_path(deck_a)
        deck_b_path = resolve_deck_path(deck_b)

        record = (i == num_matches - 1)

        try:
            game = deckgym.PyGameState(deck_a_path, deck_b_path, seed)

            # Teacher (P1) plays randomly with the same RNG so both series are identical
            def make_teacher_func(r):
                def teacher_func(state, g):
                    return r.choice(g.legal_actions())
                return teacher_func

            play_funcs = [play_func, make_teacher_func(rng)]
            winner, history, steps = run_match(game, play_funcs, record_history=record)
        except Exception as e:
            logging.error(f"[{label}] Match {i+1} failed: {e}")
            continue

        completed += 1
        if winner == 0:
            wins += 1
        elif winner == -1:
            draws += 1

        if record:
            last_history = history

        if (i + 1) % 100 == 0:
            logging.warning(f"[{label}] {i+1}/{num_matches} done, wins={wins}")

    return wins, draws, completed, last_history


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = parse_args()

    # Load teacher league decks or specific deck
    if args.deck_b:
        teacher_decks = [args.deck_b]
        teacher_weights = [1.0]
        logging.info(f"Using specific teacher deck: {args.deck_b}")
    else:
        teacher_decks, teacher_weights = load_league_decks(args.league_decks_teacher)
        if not teacher_decks:
            logging.error("Teacher league decks could not be loaded. Aborting.")
            sys.exit(1)

    # Load new AI
    try:
        import candidate_player
        import importlib
        importlib.reload(candidate_player)
        new_func = candidate_player.play
        logging.info("Using candidate_player.play for new AI.")
    except ImportError:
        logging.error("Could not import candidate_player. Using random strategy.")
        def new_func(state, game):
            return random.choice(game.legal_actions())

    # Load old AI (1 commit before = past_repo_main worktree prepared by CI)
    old_func = load_past_func(args.past_dir, args.repo_url, branch="main")

    # Silence per-step logs during bulk matches
    logging.getLogger("player").setLevel(logging.WARNING)
    logging.getLogger().setLevel(logging.WARNING)

    base_seed = args.seed

    # Run new AI series
    new_wins, new_draws, new_total, new_last = run_league_series(
        new_func, args.deck_a, teacher_decks, teacher_weights,
        args.num_matches, base_seed, "NEW"
    )

    # Run old AI series (same seeds = same opponents)
    old_wins, old_draws, old_total, old_last = run_league_series(
        old_func, args.deck_a, teacher_decks, teacher_weights,
        args.num_matches, base_seed, "OLD"
    )

    new_win_rate = new_wins / new_total if new_total > 0 else 0
    old_win_rate = old_wins / old_total if old_total > 0 else 0
    improvement = new_win_rate - old_win_rate

    # Re-enable logging for results
    logging.getLogger().setLevel(logging.INFO)

    print("\n--- Deck-Specialized AI Evaluation Results ---")
    print(f"Student deck : {args.deck_a}")
    print(f"Matches / AI : {args.num_matches}")
    print(f"\nNew AI  wins : {new_wins} / {new_total}  ({new_win_rate:.2%})")
    print(f"Old AI  wins : {old_wins} / {old_total}  ({old_win_rate:.2%})")
    print(f"Improvement  : {improvement:+.2%}  (threshold: {args.threshold:+.2%})")

    # Generate HTML for the last match of the new AI
    generate_html(new_last, args.output)
    print(f"\nLast match visualization saved to: {args.output}")

    # CI check
    if args.num_matches < 1000:
        logging.error(f"Number of matches ({args.num_matches}) is less than 1000. Failing CI.")
        sys.exit(1)

    if improvement < args.threshold:
        logging.error(
            f"New AI did not improve over old AI by the required {args.threshold:.2%}. "
            f"Actual improvement: {improvement:+.2%}. Failing CI."
        )
        sys.exit(1)

    logging.info(f"CI check passed. New AI improved by {improvement:+.2%}.")


if __name__ == "__main__":
    main()
