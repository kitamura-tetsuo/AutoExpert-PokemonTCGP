import re
import random

def play(state, game):
    """
    Decides the best action for the current player using improved heuristics.
    """
    legal_actions = game.legal_actions()
    if not legal_actions:
        return 0 # Should not happen if game is not over

    # --- Helpers ---
    def get_hp(card):
        if not card: return 0
        return getattr(card, "remaining_hp", 0)

    def get_max_hp(card):
        if not card: return 0
        return getattr(card, "total_hp", 0)

    def count_energy(card):
        if not card or not hasattr(card, "attached_energy"): return 0
        return len(card.attached_energy)

    def get_attack_damage(card, attack_idx):
        if not card or not hasattr(card, "attacks") or attack_idx >= len(card.attacks):
            return 0
        atk = card.attacks[attack_idx]
        dmg = getattr(atk, "fixed_damage", 0)
        return dmg

    def get_max_attack_damage(card):
        if not card or not hasattr(card, "attacks"): return 0
        max_d = 0
        for atk in card.attacks:
            d = getattr(atk, "fixed_damage", 0)
            if d > max_d: max_d = d
        return max_d

    def is_lethal(damage, target_hp):
        return damage >= target_hp

    # --- Parse Actions ---
    parsed_actions = {
        "attack": [], # (aid, name, idx, damage)
        "attach": [], # (aid, name, pos, energy_type)
        "evolve": [], # (aid, name)
        "place_active": [], # (aid, name)
        "place_bench": [], # (aid, name)
        "play_item": [], # (aid, name)
        "play_supporter": [], # (aid, name)
        "ability": [], # (aid, idx)
        "retreat": [], # (aid, name)
        "activate": [], # (aid, idx)
        "end_turn": [] # (aid, name)
    }

    current_player = state.current_player
    my_active = state.get_active_pokemon(current_player)

    for aid in legal_actions:
        name = game.action_name(aid)

        if name.startswith("Attack("):
            match = re.search(r"Attack\((\d+)\)", name)
            idx = int(match.group(1)) if match else 0
            dmg = get_attack_damage(my_active, idx)
            parsed_actions["attack"].append((aid, name, idx, dmg))

        elif name.startswith("Attach"):
            # Try Attach(Type, Pos) or Attach(Some(Type), Pos)
            match = re.search(r"Attach\((?:Some\()?(.*?)\)?, (\d+)\)", name)
            if match:
                etype = match.group(1).replace(")", "")
                pos = int(match.group(2))
                parsed_actions["attach"].append((aid, name, pos, etype))
            else:
                match = re.search(r"AttachEnergy\((\d+), (.*?)\)", name)
                if match:
                    pos = int(match.group(1))
                    etype = match.group(2)
                    parsed_actions["attach"].append((aid, name, pos, etype))
                else:
                    parsed_actions["attach"].append((aid, name, -1, "Unknown"))

        elif name.startswith("Evolve("):
            parsed_actions["evolve"].append((aid, name))

        elif name.startswith("Place("):
            if ", 0)" in name:
                parsed_actions["place_active"].append((aid, name))
            else:
                parsed_actions["place_bench"].append((aid, name))

        elif name.startswith("PlayPokemon("):
            parsed_actions["place_bench"].append((aid, name))

        elif name.startswith("Play(") or name.startswith("UseItem") or name.startswith("UseSupporter"):
            if any(x in name for x in ["Research", "Sabrina", "Giovanni", "Erika", "Misty", "Blaine", "Koga", "Lt. Surge", "Brock"]):
                parsed_actions["play_supporter"].append((aid, name))
            else:
                parsed_actions["play_item"].append((aid, name))

        elif name.startswith("UseAbility("):
            match = re.search(r"UseAbility\((\d+)\)", name)
            idx = int(match.group(1)) if match else 0
            parsed_actions["ability"].append((aid, idx))

        elif name == "EndTurn":
            parsed_actions["end_turn"].append((aid, name))

        elif name.startswith("Retreat"):
            parsed_actions["retreat"].append((aid, name))

        elif name.startswith("Activate("):
            match = re.search(r"Activate\((\d+)\)", name)
            idx = int(match.group(1)) if match else 0
            parsed_actions["activate"].append((aid, idx))

    # --- State Analysis ---
    opponent = 1 - current_player

    # my_active already retrieved
    my_bench = state.get_bench_pokemon(current_player)
    my_hand = state.get_hand(current_player)

    opp_active = state.get_active_pokemon(opponent)
    opp_bench = state.get_bench_pokemon(opponent)

    try:
        opp_hand_size = len(state.get_hand(opponent))
    except:
        opp_hand_size = 0

    opp_hp = get_hp(opp_active)

    # --- Strategic Logic ---

    # 1. Activate (Forced Selection)
    if parsed_actions["activate"]:
        # Case A: We have NO active (e.g. KO replacement). Pick best bench.
        if not my_active:
             best_act_id = parsed_actions["activate"][0][0]
             max_score = -1
             for aid, idx in parsed_actions["activate"]:
                 if idx < len(my_bench):
                     b_card = my_bench[idx]
                     if b_card:
                         # Prioritize: Energy (ready to attack) > HP (survival)
                         # Reverted to 100 weight (Baseline)
                         score = count_energy(b_card) * 100 + get_hp(b_card)
                         if score > max_score:
                             max_score = score
                             best_act_id = aid
             return best_act_id
        else:
             # Case B: Target selection (e.g. Sabrina). Pick weakest target.
             best_act_id = parsed_actions["activate"][0][0]
             min_hp = 9999
             for aid, idx in parsed_actions["activate"]:
                 if opp_bench and idx < len(opp_bench):
                     b_card = opp_bench[idx]
                     if b_card:
                         hp = get_hp(b_card)
                         if hp < min_hp:
                             min_hp = hp
                             best_act_id = aid
             return best_act_id

    # 2. Setup Phase (Place Active)
    if parsed_actions["place_active"]:
        def score_start_card(aname):
            score = 0
            if "ex" in aname or "EX" in aname: score += 50
            if "Mewtwo" in aname: score += 20
            if "Basic" in aname: score += 10
            return score

        random.shuffle(parsed_actions["place_active"])
        best_active = max(parsed_actions["place_active"], key=lambda x: score_start_card(x[1]))
        return best_active[0]

    # 3. Lethal Check (Priority 1)

    # Direct Attack Lethal
    lethal_attacks = []
    for aid, name, idx, dmg in parsed_actions["attack"]:
        if is_lethal(dmg, opp_hp):
            lethal_attacks.append((aid, dmg))

    if lethal_attacks:
        return lethal_attacks[0][0]

    # Giovanni Lethal
    giovanni_actions = [a for a in parsed_actions["play_supporter"] if "Giovanni" in a[1]]
    if giovanni_actions and parsed_actions["attack"]:
        # Check if Giovanni + Attack is lethal
        for aid, name, idx, dmg in parsed_actions["attack"]:
            if is_lethal(dmg + 10, opp_hp):
                return giovanni_actions[0][0]

    # 4. Evolution (Always good)
    if parsed_actions["evolve"]:
        return parsed_actions["evolve"][0][0]

    # 5. Abilities (Generally good to use)
    if parsed_actions["ability"]:
        return parsed_actions["ability"][0][0]

    # 6. Supporters (Strategic)
    if parsed_actions["play_supporter"]:
        # Professor's Research
        research = [a for a in parsed_actions["play_supporter"] if "Research" in a[1]]
        if research:
            if len(my_hand) <= 5:
                return research[0][0]

        # Sabrina
        sabrina = [a for a in parsed_actions["play_supporter"] if "Sabrina" in a[1]]
        if sabrina:
            # Kill bench or stall
            if parsed_actions["attack"]:
                max_dmg = max([d for _, _, _, d in parsed_actions["attack"]])
                weakest_bench_hp = 999
                if opp_bench:
                    for b in opp_bench:
                        if b:
                            weakest_bench_hp = min(weakest_bench_hp, get_hp(b))

                if weakest_bench_hp <= max_dmg and weakest_bench_hp < 999:
                    return sabrina[0][0]

            # Reverted to > 70 (Baseline)
            if opp_hp > 70:
                return sabrina[0][0]

        # Misty
        misty = [a for a in parsed_actions["play_supporter"] if "Misty" in a[1]]
        if misty:
             return misty[0][0]

    # 7. Energy Attachment
    if parsed_actions["attach"]:
        active_energy = count_energy(my_active)

        target_pos = -1

        # Simple heuristic from baseline:
        # If active has < 3 energy, attach to it.
        if active_energy < 3:
            target_pos = 0
        else:
             # Attach to best bench
             best_bench_idx = -1
             best_bench_score = -1
             for i, b_card in enumerate(my_bench):
                 if b_card:
                     score = get_max_attack_damage(b_card) + get_hp(b_card)
                     if score > best_bench_score:
                         best_bench_score = score
                         best_bench_idx = i + 1
             if best_bench_idx != -1:
                 target_pos = best_bench_idx
             else:
                 target_pos = 0 # Fallback

        for aid, name, pos, etype in parsed_actions["attach"]:
            if pos == target_pos:
                return aid

        return parsed_actions["attach"][0][0]

    # 8. Bench Placement
    if parsed_actions["place_bench"]:
        return parsed_actions["place_bench"][0][0]

    # 9. Items
    if parsed_actions["play_item"]:
        potion = [a for a in parsed_actions["play_item"] if "Potion" in a[1]]
        if potion and my_active and get_hp(my_active) < get_max_hp(my_active):
             return potion[0][0]

        red_card = [a for a in parsed_actions["play_item"] if "RedCard" in a[1]]
        if red_card and opp_hand_size >= 4:
            return red_card[0][0]

        poke_ball = [a for a in parsed_actions["play_item"] if "Ball" in a[1]]
        if poke_ball: return poke_ball[0][0]

        x_speed = [a for a in parsed_actions["play_item"] if "XSpeed" in a[1]]
        if x_speed and my_active and get_hp(my_active) < 40: # Reverted to < 40
             return x_speed[0][0]

    # 10. Retreat
    if parsed_actions["retreat"]:
        # Survival Retreat
        if my_active and get_hp(my_active) <= 30:
             return parsed_actions["retreat"][0][0]

    # 11. Attack (Non-lethal)
    if parsed_actions["attack"]:
        # Pick max damage
        parsed_actions["attack"].sort(key=lambda x: x[3], reverse=True)
        return parsed_actions["attack"][0][0]

    # 12. End Turn
    if parsed_actions["end_turn"]:
        return parsed_actions["end_turn"][0][0]

    return legal_actions[0]
