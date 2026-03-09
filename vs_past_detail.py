import argparse
import sys
import os
import json
import random
import deckgym
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

# Set up paths for imports
sys.path.append(os.getcwd())

from autoexpert.skill_library import SkillLibrary
from autoexpert.config import settings

# Configure logging to stderr to keep stdout clean for JSON
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', stream=sys.stderr)

def parse_args():
    parser = argparse.ArgumentParser(description="Detailed battle analysis between current and past expert.")
    parser.add_argument("--deck_a", type=str, required=True, help="Deck file for Player 0.")
    parser.add_argument("--deck_b", type=str, required=True, help="Deck file for Player 1.")
    parser.add_argument("--seed", type=int, required=True, help="Random seed.")
    parser.add_argument("--past_dir", type=str, default="past_repo", help="Path to the past repository.")
    parser.add_argument("--repo_url", type=str, default="https://github.com/kitamura-tetsuo/AutoExpert-PokemonTCGP", help="URL of the past repository to clone.")
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
    try:
        zip_url = f"{repo_url.rstrip('/')}/archive/refs/heads/{branch}.zip"
        zip_path = Path(f"repo_temp_{branch.replace('/', '_')}.zip")
        res = subprocess.run(["curl", "-s", "-L", "-w", "%{http_code}", "-o", str(zip_path), zip_url], capture_output=True, text=True, check=True)
        if res.stdout.strip() == "404":
            if zip_path.exists():
                zip_path.unlink()
            raise Exception(f"Branch {branch} not found (404)")
        subprocess.run(["unzip", "-q", str(zip_path)], check=True)
        repo_name = repo_url.rstrip("/").split("/")[-1]
        unzipped_dirs = list(Path(".").glob(f"{repo_name}-{branch.replace('/', '-')}*"))
        if not unzipped_dirs:
            unzipped_dirs = list(Path(".").glob(f"*-{branch.replace('/', '-')}*"))
        if unzipped_dirs:
            unzipped_dir = unzipped_dirs[0]
            unzipped_dir.rename(past_dir)
        if zip_path.exists():
            zip_path.unlink()
        return past_dir
    except Exception as e:
        logging.error(f"Failed to download repository: {e}")
        if branch != "main":
            logging.info("Falling back to main branch...")
            return ensure_past_repo(base_dir, repo_url, "main")
        else:
            logging.info("Falling back to shallow clone...")
            subprocess.run(["git", "clone", "--depth", "1", "-b", branch, repo_url, str(past_dir)], check=True)
            return past_dir

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

def get_cards_mapping():
    cards = deckgym.get_all_cards()
    return {i: card.name for i, card in enumerate(cards)}

ENERGY_TYPES = ["Grass", "Fire", "Water", "Lightning", "Psychic", "Fighting", "Darkness", "Metal", "Dragon", "Colorless"]

def decode_pokemon(obs, start_idx, card_mapping):
    hp = obs[start_idx] * 300.0
    energies = obs[start_idx+1 : start_idx+11]
    card_id_idx = int(obs[start_idx+11])
    card_name = card_mapping.get(card_id_idx, "Empty") if card_id_idx >= 0 else "Empty"
    
    status = []
    if obs[start_idx+12] > 0.5: status.append("Poisoned")
    if obs[start_idx+13] > 0.5: status.append("Asleep")
    if obs[start_idx+14] > 0.5: status.append("Paralyzed")
    if obs[start_idx+15] > 0.5: status.append("Confused")
    if obs[start_idx+16] > 0.5: status.append("Burned")
    
    played_this_turn = obs[start_idx+17] > 0.5
    ability_used = obs[start_idx+18] > 0.5
    
    tool_idx = int(obs[start_idx+19])
    tool_name = card_mapping.get(tool_idx, "None") if tool_idx >= 0 else "None"
    
    effects = []
    if obs[start_idx+20] > 0.5: effects.append("NoRetreat")
    if obs[start_idx+21] > 0.5: effects.append("CannotAttack")
    if obs[start_idx+22] > 0.5: effects.append("ReducedDamage")
    if obs[start_idx+23] > 0.5: effects.append("PreventDamage")
    
    res = {
        "name": card_name,
        "hp": int(hp),
        "energy": {ENERGY_TYPES[i]: int(energies[i]) for i in range(10) if energies[i] > 0},
        "status": status,
        "played_this_turn": played_this_turn,
        "ability_used": ability_used,
        "tool": tool_name,
        "effects": effects
    }
    return res

def decode_observation(obs, card_mapping):
    ptr = 0
    turn_count = int(obs[ptr]); ptr += 1
    my_points = int(obs[ptr]); ptr += 1
    opp_points = int(obs[ptr]); ptr += 1
    is_my_turn = obs[ptr] > 0.5; ptr += 1
    
    has_played_support = obs[ptr] > 0.5; ptr += 1
    has_retreated = obs[ptr] > 0.5; ptr += 1
    ko_last_turn = obs[ptr] > 0.5; ptr += 1
    
    current_energy = {ENERGY_TYPES[i]: 1 for i in range(10) if obs[ptr+i] > 0.5}; ptr += 10
    my_next_energy = {ENERGY_TYPES[i]: 1 for i in range(10) if obs[ptr+i] > 0.5}; ptr += 10
    opp_next_energy = {ENERGY_TYPES[i]: 1 for i in range(10) if obs[ptr+i] > 0.5}; ptr += 10
    
    my_hand_count = int(obs[ptr]); ptr += 1
    opp_hand_count = int(obs[ptr]); ptr += 1
    
    my_active = decode_pokemon(obs, ptr, card_mapping); ptr += 24
    my_bench = [decode_pokemon(obs, ptr + i*24, card_mapping) for i in range(3)]; ptr += 72
    opp_active = decode_pokemon(obs, ptr, card_mapping); ptr += 24
    opp_bench = [decode_pokemon(obs, ptr + i*24, card_mapping) for i in range(3)]; ptr += 72
    
    my_hand = []
    for _ in range(10):
        idx = int(obs[ptr])
        if idx >= 0: my_hand.append(card_mapping.get(idx, f"Unknown({idx})"))
        ptr += 1
        
    opp_hand_known = []
    for _ in range(10):
        idx = int(obs[ptr])
        if idx >= 0: opp_hand_known.append(card_mapping.get(idx, f"Unknown({idx})"))
        ptr += 1
        
    my_deck = []
    for _ in range(20):
        idx = int(obs[ptr])
        if idx >= 0: my_deck.append(card_mapping.get(idx, f"Unknown({idx})"))
        ptr += 1
        
    opp_deck_count = int(obs[ptr]); ptr += 1
    opp_deck_known = []
    for _ in range(20):
        idx = int(obs[ptr])
        if idx >= 0: opp_deck_known.append(card_mapping.get(idx, f"Unknown({idx})"))
        ptr += 1
        
    my_discard = []
    for _ in range(10):
        idx = int(obs[ptr])
        if idx >= 0: my_discard.append(card_mapping.get(idx, f"Unknown({idx})"))
        ptr += 1
        
    opp_discard = []
    for _ in range(10):
        idx = int(obs[ptr])
        if idx >= 0: opp_discard.append(card_mapping.get(idx, f"Unknown({idx})"))
        ptr += 1
        
    return {
        "turn": turn_count,
        "points": [my_points, opp_points],
        "is_my_turn": is_my_turn,
        "flags": {"support": has_played_support, "retreat": has_retreated, "ko_last_turn": ko_last_turn},
        "energy": {"current": current_energy, "my_next": my_next_energy, "opp_next": opp_next_energy},
        "hand_counts": [my_hand_count, opp_hand_count],
        "my_active": my_active,
        "my_bench": my_bench,
        "opp_active": opp_active,
        "opp_bench": opp_bench,
        "my_hand": my_hand,
        "opp_hand_known": opp_hand_known,
        "my_deck_contents": my_deck,
        "opp_deck_count": opp_deck_count,
        "opp_deck_known": opp_deck_known,
        "my_discard": my_discard,
        "opp_discard": opp_discard
    }

def main():
    args = parse_args()
    random.seed(args.seed)
    card_mapping = get_cards_mapping()
    
    # 1. Load Current Best (P0)
    current_best_func = None
    try:
        import candidate_player
        import importlib
        importlib.reload(candidate_player)
        current_best_func = candidate_player.play
        logging.info("Using candidate_player.play for Player 0.")
    except ImportError:
        library = SkillLibrary()
        best_skill = library.get_best_skill()
        if best_skill:
            logging.info(f"Using expert skill from library for Player 0: {best_skill['name']}")
            current_best_func = get_play_func(best_skill)
        else:
            logging.warning("No current expert found. Using random.")
            current_best_func = get_play_func(None)

    # 2. Load Past Best (P1)
    branch_name = Path(args.deck_b).stem
    past_dir = ensure_past_repo(args.past_dir, args.repo_url, branch_name)

    past_best_func = None
    past_candidate_path = past_dir / "candidate_player.py"
    if past_candidate_path.exists():
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(f"past_candidate_player_{branch_name.replace('/', '_')}", str(past_candidate_path))
            past_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(past_module)
            past_best_func = past_module.play
            logging.info(f"Using candidate_player.play from branch {branch_name} for Player 1.")
        except Exception as e:
             logging.error(f"Error loading past candidate: {e}")

    if not past_best_func:
        past_skill_dir = past_dir / "skill_library"
        if past_skill_dir.exists():
            past_library = SkillLibrary(directory=past_skill_dir)
            past_best = past_library.get_best_skill()
            if past_best:
                 logging.info(f"Using past library skill: {past_best['name']}")
                 past_best_func = get_play_func(past_best)
        
    if not past_best_func:
        logging.warning("No past expert found. Using random for Player 1.")
        past_best_func = get_play_func(None)

    play_funcs = [current_best_func, past_best_func]

    deck_a_path = Path(args.deck_a)
    if not deck_a_path.exists():
        deck_a_path = settings.DECK_DIR / args.deck_a
    if not deck_a_path.exists():
        deck_a_path = Path("train_data") / args.deck_a
        
    deck_b_path = Path(args.deck_b)
    if not deck_b_path.exists():
        deck_b_path = settings.DECK_DIR / args.deck_b
    if not deck_b_path.exists():
        deck_b_path = Path("train_data") / args.deck_b
        
    deck_a_path = str(deck_a_path)
    deck_b_path = str(deck_b_path)

    game = deckgym.PyGameState(deck_a_path, deck_b_path, args.seed)
    
    step = 0
    while not game.get_state().is_game_over() and step < 500:
        state = game.get_state()
        curr_p = state.current_player
        
        obs_vec = game.encode_observation(player_id=0)
        decoded = decode_observation(obs_vec, card_mapping)
        
        # Use stderr for "STEP" labels if you want clean JSON output, 
        # but the user likely wants to see them in the log.
        print(f"\n--- STEP {step} (Player {curr_p} Turn) ---")
        print(json.dumps(decoded, indent=2))
        
        legal = game.legal_actions()
        legal_names = {aid: game.action_name(aid) for aid in legal}
        print(f"Legal Actions: {legal_names}")
        
        if not legal:
            print("No legal actions available, breaking out of the loop...")
            break

        action_id = play_funcs[curr_p](state, game)
        action_name = game.action_name(action_id)
        print(f"Selected Action: {action_id} - {action_name}")
        
        game.step_with_id(action_id)
        step += 1
        
    if game.get_state().is_game_over():
        print("\n--- GAME OVER ---")
        print(f"Winner: {game.get_state().winner}")

if __name__ == "__main__":
    main()
