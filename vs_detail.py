import argparse
import sys
import os
import json
import deckgym
from pathlib import Path
from typing import Dict, Any, List, Optional

# Set up paths for imports
sys.path.append(os.getcwd())

from autoexpert.skill_library import SkillLibrary
from autoexpert.config import settings

def parse_args():
    parser = argparse.ArgumentParser(description="Detailed battle analysis for LLM.")
    parser.add_argument("--deck_a", type=str, required=True, help="Deck file for Player 0.")
    parser.add_argument("--deck_b", type=str, required=True, help="Deck file for Player 1.")
    parser.add_argument("--seed", type=int, required=True, help="Random seed.")
    return parser.parse_args()

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
    # obs is a list/array of floats
    ptr = 0
    # 1. Turn Info
    turn_count = int(obs[ptr]); ptr += 1
    my_points = int(obs[ptr]); ptr += 1
    opp_points = int(obs[ptr]); ptr += 1
    is_my_turn = obs[ptr] > 0.5; ptr += 1
    
    # 1.1 Turn Flags
    has_played_support = obs[ptr] > 0.5; ptr += 1
    has_retreated = obs[ptr] > 0.5; ptr += 1
    ko_last_turn = obs[ptr] > 0.5; ptr += 1
    
    # 1.2 Energy Info
    current_energy = {ENERGY_TYPES[i]: 1 for i in range(10) if obs[ptr+i] > 0.5}; ptr += 10
    my_next_energy = {ENERGY_TYPES[i]: 1 for i in range(10) if obs[ptr+i] > 0.5}; ptr += 10
    opp_next_energy = {ENERGY_TYPES[i]: 1 for i in range(10) if obs[ptr+i] > 0.5}; ptr += 10
    
    # 2. Hand Counts
    my_hand_count = int(obs[ptr]); ptr += 1
    opp_hand_count = int(obs[ptr]); ptr += 1
    
    # 3. My Active
    my_active = decode_pokemon(obs, ptr, card_mapping); ptr += 24
    
    # 4. My Bench
    my_bench = []
    for _ in range(3):
        my_bench.append(decode_pokemon(obs, ptr, card_mapping)); ptr += 24
        
    # 5. Opponent Active
    opp_active = decode_pokemon(obs, ptr, card_mapping); ptr += 24
    
    # 6. Opponent Bench
    opp_bench = []
    for _ in range(3):
        opp_bench.append(decode_pokemon(obs, ptr, card_mapping)); ptr += 24
        
    # 7. My Hand Slots (10)
    my_hand = []
    for _ in range(10):
        idx = int(obs[ptr])
        if idx >= 0: my_hand.append(card_mapping.get(idx, f"Unknown({idx})"))
        ptr += 1
        
    # 8. Opponent Hand Slots (10) - Known cards
    opp_hand_known = []
    for _ in range(10):
        idx = int(obs[ptr])
        if idx >= 0: opp_hand_known.append(card_mapping.get(idx, f"Unknown({idx})"))
        ptr += 1
        
    # 9. My Deck IDs (20)
    my_deck = []
    for _ in range(20):
        idx = int(obs[ptr])
        if idx >= 0: my_deck.append(card_mapping.get(idx, f"Unknown({idx})"))
        ptr += 1
        
    # 10. Opponent Deck Count
    opp_deck_count = int(obs[ptr]); ptr += 1
    
    # 10.1 Opponent Known Deck (20)
    opp_deck_known = []
    for _ in range(20):
        idx = int(obs[ptr])
        if idx >= 0: opp_deck_known.append(card_mapping.get(idx, f"Unknown({idx})"))
        ptr += 1
        
    # 11. My Discard
    my_discard = []
    for _ in range(10):
        idx = int(obs[ptr])
        if idx >= 0: my_discard.append(card_mapping.get(idx, f"Unknown({idx})"))
        ptr += 1
        
    # 12. Opponent Discard
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
    import random
    random.seed(args.seed)
    card_mapping = get_cards_mapping()
    
    # Find active expert skill
    library = SkillLibrary()
    best_skill = library.get_best_skill()
    if best_skill:
        print(f"Using expert skill: {best_skill['name']}")
        code = best_skill["code"]
        local_vars = {}
        exec(code, {"deckgym": deckgym}, local_vars)
        play_func = local_vars.get("play")
    else:
        print("No expert skill found. Using random choice.")
        play_func = None

    deck_a_path = str(settings.DECK_DIR / args.deck_a)
    if not Path(deck_a_path).exists(): deck_a_path = str(Path("train_data") / args.deck_a)
    
    deck_b_path = str(settings.DECK_DIR / args.deck_b)
    if not Path(deck_b_path).exists(): deck_b_path = str(Path("train_data") / args.deck_b)

    game = deckgym.PyGameState(deck_a_path, deck_b_path, args.seed)
    
    step = 0
    while not game.get_state().is_game_over() and step < 500:
        state = game.get_state()
        curr_player = state.current_player
        
        # Get encoded observation for the current player
        obs_vec = game.encode_observation(player_id=curr_player)
        decoded = decode_observation(obs_vec, card_mapping)
        
        print(f"\n--- STEP {step} (Player {curr_player} Turn) ---")
        print(json.dumps(decoded, indent=2))
        
        legal = game.legal_actions()
        legal_names = {aid: game.action_name(aid) for aid in legal}
        print(f"Legal Actions: {legal_names}")
        
        # Determine action
        if play_func:
            # Note: AutoExpert play functions typically take (state, game)
            # We must be careful if the expert was trained on raw state or encoded.
            # Most current skills use 'game.legal_actions()' and logic based on 'state'.
            try:
                action_id = play_func(state, game)
            except Exception as e:
                print(f"Error in play_func: {e}")
                import random
                action_id = random.choice(legal)
        else:
            import random
            action_id = random.choice(legal)
            
        action_name = game.action_name(action_id)
        print(f"Selected Action: {action_id} - {action_name}")
        
        game.step_with_id(action_id)
        step += 1
        
    if game.get_state().is_game_over():
        print("\n--- GAME OVER ---")
        print(f"Winner: {game.get_state().winner}")

if __name__ == "__main__":
    main()
