import re

def play(state, game):
    """
    Decides the best action for the current player using optimized heuristics.
    """
    legal_actions = game.legal_actions()
    if not legal_actions:
        return 0

    # --- 1. Helper Functions ---
    def get_hp(card):
        return getattr(card, "remaining_hp", 0) if card else 0

    def get_max_hp(card):
        return getattr(card, "total_hp", 0) if card else 0

    def count_energy(card):
        return len(card.attached_energy) if (card and hasattr(card, "attached_energy")) else 0

    def get_attack_damage(card, attack_idx):
        if not card or not hasattr(card, "attacks") or attack_idx >= len(card.attacks):
            return 0
        atk = card.attacks[attack_idx]
        return getattr(atk, "fixed_damage", 0)

    def get_energy_deficit(current_energy, cost):
        """
        Returns (specific_needed_map, colorless_needed_count).
        specific_needed_map: {type_str: count}
        """
        current_counts = {}
        for e in current_energy:
            s = str(e)
            current_counts[s] = current_counts.get(s, 0) + 1

        specific_needed = {}
        colorless_cost = 0

        # 1. Match specific types first
        temp_counts = current_counts.copy()

        for c in cost:
            s = str(c)
            if s == "Colorless":
                colorless_cost += 1
                continue

            if temp_counts.get(s, 0) > 0:
                temp_counts[s] -= 1
            else:
                specific_needed[s] = specific_needed.get(s, 0) + 1

        # 2. Check colorless
        remaining_energy = sum(temp_counts.values())
        colorless_needed = max(0, colorless_cost - remaining_energy)

        return specific_needed, colorless_needed

    def is_useful_energy(new_energy_type, current_energy, cost):
        specific_needed, colorless_needed = get_energy_deficit(current_energy, cost)

        s = str(new_energy_type)
        if specific_needed.get(s, 0) > 0:
            return True
        if colorless_needed > 0:
            return True
        return False

    def get_best_attack_cost(card):
        if not card or not hasattr(card, "attacks") or not card.attacks:
            return None

        best_dmg = -1
        best_cost = []
        found = False

        for atk in card.attacks:
            dmg = getattr(atk, "fixed_damage", 0)
            if dmg > best_dmg:
                best_dmg = dmg
                best_cost = getattr(atk, "cost", [])
                found = True

        return best_cost if found else []

    # --- 2. Parse Actions ---
    parsed_actions = {
        "attack": [],       # (aid, idx, damage)
        "attach": [],       # (aid, energy_type, pos)
        "evolve": [],       # (aid, name)
        "place_active": [], # (aid, name)
        "place_bench": [],  # (aid, name)
        "play_item": [],    # (aid, name)
        "play_supporter": [], # (aid, name)
        "ability": [],      # (aid, idx)
        "retreat": [],      # (aid, idx)
        "activate": [],     # (aid, idx)
        "end_turn": []      # (aid)
    }

    current_player = state.current_player
    my_active = state.get_active_pokemon(current_player)
    my_bench = state.get_bench_pokemon(current_player)

    for aid in legal_actions:
        name = game.action_name(aid)

        if name.startswith("Attack("):
            match = re.search(r"Attack\((\d+)\)", name)
            if match:
                idx = int(match.group(1))
                dmg = get_attack_damage(my_active, idx)
                parsed_actions["attack"].append((aid, idx, dmg))

        elif name.startswith("Attach"):
            match = re.search(r"Attach\((?:Some\()?(.*?)\)?, (\d+)\)", name)
            if match:
                etype = match.group(1).replace(")", "")
                pos = int(match.group(2))
                parsed_actions["attach"].append((aid, etype, pos))
            else:
                match = re.search(r"AttachEnergy\((\d+), (.*?)\)", name)
                if match:
                    pos = int(match.group(1))
                    etype = match.group(2)
                    parsed_actions["attach"].append((aid, etype, pos))
                else:
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
            card_name = name
            match = re.search(r"Play\((?:Some\()?(.*?)\)?\)", name)
            if match:
                card_name = match.group(1)

            if name.startswith("UseSupporter"):
                parsed_actions["play_supporter"].append((aid, card_name))
            elif name.startswith("UseItem"):
                parsed_actions["play_item"].append((aid, card_name))
            else:
                supporters = ["Research", "Sabrina", "Giovanni", "Erika", "Misty", "Blaine", "Koga", "Lt. Surge", "Brock", "Copycat", "Lisia", "Cyrus"]
                if any(s in card_name for s in supporters):
                    parsed_actions["play_supporter"].append((aid, card_name))
                else:
                    parsed_actions["play_item"].append((aid, card_name))

        elif name.startswith("UseAbility("):
            match = re.search(r"UseAbility\((\d+)\)", name)
            idx = int(match.group(1)) if match else 0
            parsed_actions["ability"].append((aid, idx))

        elif name.startswith("Retreat("):
            match = re.search(r"Retreat\((\d+)\)", name)
            idx = int(match.group(1)) if match else 0
            parsed_actions["retreat"].append((aid, idx))

        elif name.startswith("Activate("):
            match = re.search(r"Activate\((\d+)\)", name)
            idx = int(match.group(1)) if match else 0
            parsed_actions["activate"].append((aid, idx))

        elif name == "EndTurn":
            parsed_actions["end_turn"].append((aid,))

    # --- 3. State Analysis ---
    opponent = 1 - current_player
    opp_active = state.get_active_pokemon(opponent)
    opp_bench = state.get_bench_pokemon(opponent)

    opp_hp = get_hp(opp_active)
    my_hp = get_hp(my_active)

    try:
        opp_hand_size = len(state.get_hand(opponent))
    except:
        opp_hand_size = 0

    my_hand_size = len(state.get_hand(current_player))

    # --- 4. Decision Logic ---

    # A. Lethal Check
    if parsed_actions["attack"]:
        for aid, idx, dmg in parsed_actions["attack"]:
            if dmg >= opp_hp:
                return aid
        giovanni = [a for a in parsed_actions["play_supporter"] if "Giovanni" in a[1]]
        if giovanni:
            for aid, idx, dmg in parsed_actions["attack"]:
                if dmg + 10 >= opp_hp:
                    return giovanni[0][0]

    # B. Activate
    if parsed_actions["activate"]:
        if not my_active:
            best_aid = parsed_actions["activate"][0][0]
            max_score = -1
            for aid, idx in parsed_actions["activate"]:
                score = 0
                if idx < len(my_bench):
                    card = my_bench[idx]
                    if card:
                         score = count_energy(card) * 1000 + get_hp(card)
                if score > max_score:
                    max_score = score
                    best_aid = aid
            return best_aid
        else:
            best_aid = parsed_actions["activate"][0][0]
            min_hp = 9999
            for aid, idx in parsed_actions["activate"]:
                if idx < len(opp_bench):
                    card = opp_bench[idx]
                    if card:
                        hp = get_hp(card)
                        if hp < min_hp:
                            min_hp = hp
                            best_aid = aid
            return best_aid

    # C. Setup
    if parsed_actions["place_active"]:
        def score_card(name):
            s = 0
            if "ex" in name.lower() or "EX" in name: s += 100
            if "mewtwo" in name.lower(): s += 50
            return s
        best = max(parsed_actions["place_active"], key=lambda x: score_card(x[1]))
        return best[0]

    # D. Evolution
    if parsed_actions["evolve"]:
        return parsed_actions["evolve"][0][0]

    # E. Bench
    if parsed_actions["place_bench"]:
        return parsed_actions["place_bench"][0][0]

    # F. Abilities
    if parsed_actions["ability"]:
        return parsed_actions["ability"][0][0]

    # G. Items
    if parsed_actions["play_item"]:
        balls = [a for a in parsed_actions["play_item"] if "Ball" in a[1]]
        if balls: return balls[0][0]
        candy = [a for a in parsed_actions["play_item"] if "RareCandy" in a[1]]
        if candy: return candy[0][0]
        potion = [a for a in parsed_actions["play_item"] if "Potion" in a[1]]
        if potion and my_active and my_hp < get_max_hp(my_active):
            return potion[0][0]
        red_card = [a for a in parsed_actions["play_item"] if "RedCard" in a[1]]
        if red_card and opp_hand_size >= 4:
            return red_card[0][0]
        helmet = [a for a in parsed_actions["play_item"] if "RockyHelmet" in a[1]]
        if helmet: return helmet[0][0]
        hand_scope = [a for a in parsed_actions["play_item"] if "HandScope" in a[1]]
        if hand_scope: return hand_scope[0][0]

    # H. Supporters
    if parsed_actions["play_supporter"]:
        research = [a for a in parsed_actions["play_supporter"] if "Research" in a[1]]
        if research and my_hand_size <= 6:
            return research[0][0]
        copycat = [a for a in parsed_actions["play_supporter"] if "Copycat" in a[1]]
        if copycat and my_hand_size <= 4 and opp_hand_size >= 4:
            return copycat[0][0]
        sabrina = [a for a in parsed_actions["play_supporter"] if "Sabrina" in a[1]]
        if sabrina and opp_hp > 60:
             return sabrina[0][0]
        misty = [a for a in parsed_actions["play_supporter"] if "Misty" in a[1]]
        if misty: return misty[0][0]

    # I. Energy Attachment
    if parsed_actions["attach"]:
        # Find best attachment
        # 1. Try to satisfy Active deficit
        if my_active:
             cost = get_best_attack_cost(my_active)
             attached = getattr(my_active, "attached_energy", [])
             specific_needed, colorless_needed = get_energy_deficit(attached, cost)

             if specific_needed or colorless_needed > 0:
                 for aid, etype, pos in parsed_actions["attach"]:
                     if pos == 0:
                         if is_useful_energy(etype, attached, cost):
                             return aid

        # 2. Try to satisfy Bench deficit
        for i, card in enumerate(my_bench):
            if card:
                 cost = get_best_attack_cost(card)
                 attached = getattr(card, "attached_energy", [])
                 specific_needed, colorless_needed = get_energy_deficit(attached, cost)

                 if specific_needed or colorless_needed > 0:
                     pos_idx = i + 1
                     for aid, etype, pos in parsed_actions["attach"]:
                         if pos == pos_idx:
                             if is_useful_energy(etype, attached, cost):
                                 return aid

        # 3. Fallback: Standard heuristic
        target_pos = 0
        if count_energy(my_active) < 3:
            target_pos = 0
        else:
            target_pos = 1

        for aid, etype, pos in parsed_actions["attach"]:
            if pos == target_pos:
                return aid
        return parsed_actions["attach"][0][0]

    # J. Retreat
    if parsed_actions["retreat"]:
        if my_active and my_hp <= 40:
             has_backup = False
             for card in my_bench:
                 if card and count_energy(card) > 0:
                     has_backup = True
                     break
             if has_backup:
                 for aid, idx in parsed_actions["retreat"]:
                     if idx < len(my_bench):
                         card = my_bench[idx]
                         if card and count_energy(card) > 0:
                             return aid
                 return parsed_actions["retreat"][0][0]

    # K. Attack
    if parsed_actions["attack"]:
        best_attack = max(parsed_actions["attack"], key=lambda x: x[2])
        return best_attack[0]

    # L. End Turn
    if parsed_actions["end_turn"]:
        return parsed_actions["end_turn"][0][0]

    return legal_actions[0]
