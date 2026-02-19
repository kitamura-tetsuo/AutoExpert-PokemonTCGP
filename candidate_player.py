import re

def play(state, game):
    """
    Decides the best action for the current player using general heuristics.
    """
    legal_actions = game.legal_actions()
    if not legal_actions:
        return 0

    # 1. Parse Legal Actions
    parsed_actions = {
        "attack": [],
        "attach": [], # (aid, card_name/energy_type, pos)
        "evolve": [],
        "place_active": [],
        "place_bench": [],
        "play_item": [],
        "play_supporter": [],
        "ability": [], # (aid, ability_idx)
        "retreat": [],
        "activate": [], # (aid, target_idx)
        "end_turn": []
    }

    for aid in legal_actions:
        name = game.action_name(aid)

        if name.startswith("Attack("):
            match = re.search(r"Attack\((\d+)\)", name)
            idx = int(match.group(1)) if match else 0
            parsed_actions["attack"].append((aid, name, idx))

        elif name.startswith("Attach"):
            # Try Attach(Type, Pos) or Attach(Some(Type), Pos)
            match = re.search(r"Attach\((?:Some\()?(.*?)\)?, (\d+)\)", name)
            if match:
                etype = match.group(1).replace(")", "")
                pos = int(match.group(2))
                parsed_actions["attach"].append((aid, etype, pos))
            else:
                # Try AttachEnergy(Pos, Type) (Prompt format)
                match = re.search(r"AttachEnergy\((\d+), (.*?)\)", name)
                if match:
                    pos = int(match.group(1))
                    etype = match.group(2)
                    parsed_actions["attach"].append((aid, etype, pos))
                else:
                    # Fallback
                    parsed_actions["attach"].append((aid, name, -1))

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

        elif name.startswith("Retreat("):
            parsed_actions["retreat"].append((aid, name))

        elif name.startswith("Activate("):
            match = re.search(r"Activate\((\d+)\)", name)
            idx = int(match.group(1)) if match else 0
            parsed_actions["activate"].append((aid, idx))

    # 2. Analyze State
    current_player = state.current_player
    opponent = 1 - current_player

    my_active = state.get_active_pokemon(current_player)
    my_bench = state.get_bench_pokemon(current_player)
    my_hand = state.get_hand(current_player)

    opp_active = state.get_active_pokemon(opponent)
    opp_bench = state.get_bench_pokemon(opponent)
    # Use len(get_hand) instead of get_hand_size for safety per review
    try:
        opp_hand_size = len(state.get_hand(opponent))
    except:
        opp_hand_size = 0

    # --- Helpers ---
    def get_card_name(card):
        if hasattr(card, "name"): return card.name
        return ""

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

    # --- Logic ---

    # 0. Forced Selection (Activate)
    if parsed_actions["activate"]:
        # If we have no active pokemon, we are choosing a replacement from OUR bench.
        if not my_active:
             best_act_id = parsed_actions["activate"][0][0]
             max_score = -1
             for aid, idx in parsed_actions["activate"]:
                 if idx < len(my_bench):
                     b_card = my_bench[idx]
                     if b_card:
                         # Prioritize pokemon with energy and HP
                         score = count_energy(b_card) * 100 + get_hp(b_card)
                         if score > max_score:
                             max_score = score
                             best_act_id = aid
             return best_act_id
        else:
             # If we have active, assume it's a target selection (e.g. Sabrina).
             # Pick the weakest opponent bench pokemon.
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

    # 1. Setup Phase
    if parsed_actions["place_active"]:
        def score_start_card(aname):
            score = 0
            if "ex" in aname or "EX" in aname: score += 50
            if "Mewtwo" in aname: score += 20
            if "Basic" in aname: score += 10
            return score

        best_active = max(parsed_actions["place_active"], key=lambda x: score_start_card(x[1]))
        return best_active[0]

    # 2. Lethal Check
    if parsed_actions["attack"]:
        opp_hp = get_hp(opp_active)
        best_kill_aid = None
        max_dmg = -1
        best_dmg_aid = parsed_actions["attack"][0][0]

        for aid, name, idx in parsed_actions["attack"]:
            dmg = get_attack_damage(my_active, idx)

            giovanni = [a for a in parsed_actions["play_supporter"] if "Giovanni" in a[1]]
            if giovanni and is_lethal(dmg + 10, opp_hp):
                return giovanni[0][0]

            if is_lethal(dmg, opp_hp):
                if best_kill_aid is None or idx == 0:
                    best_kill_aid = aid

            if dmg > max_dmg:
                max_dmg = dmg
                best_dmg_aid = aid

        if best_kill_aid:
            return best_kill_aid

    # 3. Evolution
    if parsed_actions["evolve"]:
        return parsed_actions["evolve"][0][0]

    # 4. Abilities
    if parsed_actions["ability"]:
        return parsed_actions["ability"][0][0]

    # 5. Energy Attachment
    if parsed_actions["attach"]:
        target_pos = 0
        active_energy = count_energy(my_active)
        # If active needs energy (<3), attach. Else bench.
        if active_energy < 3:
            target_pos = 0
        else:
            best_bench_idx = -1
            max_potential = -1
            for i, b_card in enumerate(my_bench):
                if b_card:
                    pot = get_max_attack_damage(b_card) + get_hp(b_card)
                    if pot > max_potential:
                        max_potential = pot
                        best_bench_idx = i + 1
            if best_bench_idx != -1:
                target_pos = best_bench_idx

        for aid, etype, pos in parsed_actions["attach"]:
            if pos == target_pos:
                return aid
        return parsed_actions["attach"][0][0]

    # 6. Bench Basics
    if parsed_actions["place_bench"]:
        return parsed_actions["place_bench"][0][0]

    # 7. Supporters
    if parsed_actions["play_supporter"]:
        research = [a for a in parsed_actions["play_supporter"] if "Research" in a[1]]
        if research and len(my_hand) <= 5:
            return research[0][0]

        sabrina = [a for a in parsed_actions["play_supporter"] if "Sabrina" in a[1]]
        if sabrina and opp_active and get_hp(opp_active) > 70:
             return sabrina[0][0]

        misty = [a for a in parsed_actions["play_supporter"] if "Misty" in a[1]]
        if misty:
            return misty[0][0]

    # 8. Items
    if parsed_actions["play_item"]:
        poke_ball = [a for a in parsed_actions["play_item"] if "Ball" in a[1]]
        if poke_ball: return poke_ball[0][0]

        red_card = [a for a in parsed_actions["play_item"] if "RedCard" in a[1]]
        if red_card and opp_hand_size >= 4:
            return red_card[0][0]

        potion = [a for a in parsed_actions["play_item"] if "Potion" in a[1]]
        if potion and my_active and get_hp(my_active) < get_max_hp(my_active):
            return potion[0][0]

        x_speed = [a for a in parsed_actions["play_item"] if "XSpeed" in a[1]]
        if x_speed and my_active and get_hp(my_active) < 40:
             return x_speed[0][0]

    # 9. Attack
    if parsed_actions["attack"]:
        best_aid = parsed_actions["attack"][0][0]
        max_dmg = -1
        for aid, name, idx in parsed_actions["attack"]:
            d = get_attack_damage(my_active, idx)
            if d > max_dmg:
                max_dmg = d
                best_aid = aid
        return best_aid

    # 10. Retreat
    if parsed_actions["retreat"]:
        if my_active and get_hp(my_active) <= 30:
             for aid, name in parsed_actions["retreat"]:
                 match = re.search(r"Retreat\((\d+)\)", name)
                 if match:
                     idx = int(match.group(1))
                     if idx < len(my_bench):
                         b_card = my_bench[idx]
                         if b_card and get_hp(b_card) > 50:
                             return aid
             return parsed_actions["retreat"][0][0]

    # 11. End Turn
    if parsed_actions["end_turn"]:
        return parsed_actions["end_turn"][0][0]

    return legal_actions[0]
