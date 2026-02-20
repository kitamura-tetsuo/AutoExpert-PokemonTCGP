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

    def get_energy_type(card):
        if card and hasattr(card, "energy_type"):
            return str(card.energy_type)
        return "Colorless"

    def get_attack_damage(card, attack_idx, my_bench=None):
        if not card or not hasattr(card, "attacks") or attack_idx >= len(card.attacks):
            return 0
        atk = card.attacks[attack_idx]
        base_dmg = getattr(atk, "fixed_damage", 0)

        # Handle Pikachu ex "Circle Circuit"
        if "Pikachu ex" in getattr(card, "name", "") and "Circle Circuit" in getattr(atk, "name", ""):
            lightning_count = 0
            if my_bench:
                for b in my_bench:
                    if b and "Lightning" in get_energy_type(b):
                        lightning_count += 1
            return 30 * lightning_count

        # Handle Mewtwo ex "Psydrive" (150 dmg, discard 2 energy)
        return base_dmg

    def get_energy_deficit(current_energy, cost):
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
            return []

        max_cost_len = -1
        best_cost = []
        for atk in card.attacks:
            cost = getattr(atk, "cost", [])
            if len(cost) > max_cost_len:
                max_cost_len = len(cost)
                best_cost = cost
        return best_cost

    def can_kill(damage, target_hp):
        return damage >= target_hp

    # --- 2. State Analysis ---
    current_player = state.current_player
    my_active = state.get_active_pokemon(current_player)
    my_bench = state.get_bench_pokemon(current_player)

    opponent = 1 - current_player
    opp_active = state.get_active_pokemon(opponent)
    opp_bench = state.get_bench_pokemon(opponent)

    opp_hp = get_hp(opp_active)
    my_hp = get_hp(my_active)
    my_max_hp = get_max_hp(my_active)

    try:
        opp_hand_size = len(state.get_hand(opponent))
    except:
        opp_hand_size = 0

    my_hand_size = len(state.get_hand(current_player))

    # --- 3. Parse Actions ---
    parsed_actions = {
        "attack": [], "attach": [], "evolve": [], "place_active": [], "place_bench": [],
        "play_item": [], "play_supporter": [], "ability": [], "retreat": [], "activate": [], "end_turn": []
    }

    for aid in legal_actions:
        name = game.action_name(aid)

        if name.startswith("Attack("):
            match = re.search(r"Attack\((\d+)\)", name)
            if match:
                idx = int(match.group(1))
                dmg = get_attack_damage(my_active, idx, my_bench)
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
        elif name == "Retreat":
            parsed_actions["retreat"].append((aid, -1))

        elif name.startswith("Activate("):
            match = re.search(r"Activate\((\d+)\)", name)
            idx = int(match.group(1)) if match else 0
            parsed_actions["activate"].append((aid, idx))

        elif name == "EndTurn":
            parsed_actions["end_turn"].append((aid,))

    # --- 4. Decision Logic ---

    # A. Lethal Check
    if parsed_actions["attack"]:
        lethal_attacks = []
        for aid, idx, dmg in parsed_actions["attack"]:
            if can_kill(dmg, opp_hp):
                lethal_attacks.append((aid, idx, dmg))
        if lethal_attacks:
            lethal_attacks.sort(key=lambda x: x[1])
            return lethal_attacks[0][0]

    # B. Activate
    if parsed_actions["activate"]:
        if not my_active or get_hp(my_active) == 0:
            best_aid = parsed_actions["activate"][0][0]
            max_score = -1
            for aid, idx in parsed_actions["activate"]:
                score = 0
                if idx < len(my_bench):
                    card = my_bench[idx]
                    if card:
                        score += count_energy(card) * 50
                        score += get_hp(card)
                        if "ex" in getattr(card, "name", ""): score += 20
                if score > max_score:
                    max_score = score
                    best_aid = aid
            return best_aid
        else:
            max_dmg = 0
            if parsed_actions["attack"]:
                max_dmg = max(a[2] for a in parsed_actions["attack"])

            for aid, idx in parsed_actions["activate"]:
                if idx < len(opp_bench):
                    card = opp_bench[idx]
                    if card:
                        hp = get_hp(card)
                        if hp <= max_dmg:
                            return aid

            best_stall_aid = None
            max_stall_score = -1
            for aid, idx in parsed_actions["activate"]:
                if idx < len(opp_bench):
                    card = opp_bench[idx]
                    if card:
                        if count_energy(card) == 0:
                            score = 1000 - get_hp(card)
                            if score > max_stall_score:
                                max_stall_score = score
                                best_stall_aid = aid

            if best_stall_aid: return best_stall_aid
            return parsed_actions["activate"][0][0]

    # C. Setup Active (Start of Game)
    if parsed_actions["place_active"]:
        def score_active(name):
            s = 0
            name_lower = name.lower()
            if "ex" in name_lower: s += 100
            if "mewtwo" in name_lower: s += 50
            if "pikachu" in name_lower: s += 60
            if "starmie" in name_lower: s += 60 # Added Starmie as Fast EX
            if "articuno" in name_lower: s += 50
            return s
        best = max(parsed_actions["place_active"], key=lambda x: score_active(x[1]))
        return best[0]

    # D. Evolution
    if parsed_actions["evolve"]:
        return parsed_actions["evolve"][0][0]

    # E. Bench Placement
    if parsed_actions["place_bench"]:
        def score_bench(name):
            s = 0
            name_lower = name.lower()
            if "ex" in name_lower: s += 100
            if "mewtwo" in name_lower: s += 50
            if "pikachu" in name_lower: s += 50
            if "articuno" in name_lower: s += 50
            if "starmie" in name_lower: s += 50
            if "moltres" in name_lower: s += 50
            if "zapdos" in name_lower: s += 50
            return s
        best = max(parsed_actions["place_bench"], key=lambda x: score_bench(x[1]))
        return best[0]

    # F. Supporters
    misty = [a for a in parsed_actions["play_supporter"] if "Misty" in a[1]]
    if misty:
        return misty[0][0]

    giovanni = [a for a in parsed_actions["play_supporter"] if "Giovanni" in a[1]]
    if giovanni and parsed_actions["attack"]:
        for aid, idx, dmg in parsed_actions["attack"]:
            if not can_kill(dmg, opp_hp) and can_kill(dmg + 10, opp_hp):
                return giovanni[0][0]

    research = [a for a in parsed_actions["play_supporter"] if "Research" in a[1]]
    if research:
        if my_hand_size <= 5:
            return research[0][0]

    sabrina = [a for a in parsed_actions["play_supporter"] if "Sabrina" in a[1]]
    if sabrina:
        can_kill_active = any(can_kill(a[2], opp_hp) for a in parsed_actions["attack"])
        if not can_kill_active:
            my_max_dmg = max([a[2] for a in parsed_actions["attack"]]) if parsed_actions["attack"] else 0
            can_kill_bench = False
            for b in opp_bench:
                if b and get_hp(b) <= my_max_dmg:
                    can_kill_bench = True
                    break
            if can_kill_bench:
                return sabrina[0][0]

            if count_energy(opp_active) >= 3 and opp_hp > 60:
                 if any(b and count_energy(b) == 0 for b in opp_bench):
                     return sabrina[0][0]

            if opp_hp >= 120:
                return sabrina[0][0]

    # G. Abilities
    if parsed_actions["ability"]:
        return parsed_actions["ability"][0][0]

    # H. Items
    if parsed_actions["play_item"]:
        potion = [a for a in parsed_actions["play_item"] if "Potion" in a[1]]
        if potion and my_active and my_hp < my_max_hp:
             if my_hp <= 60:
                 return potion[0][0]

        red_card = [a for a in parsed_actions["play_item"] if "RedCard" in a[1]]
        if red_card and opp_hand_size >= 4:
            return red_card[0][0]

        balls = [a for a in parsed_actions["play_item"] if "Ball" in a[1]]
        if balls: return balls[0][0]

        candy = [a for a in parsed_actions["play_item"] if "RareCandy" in a[1]]
        if candy: return candy[0][0]

    # I. Energy Attachment
    if parsed_actions["attach"]:
        if my_active:
             cost = get_best_attack_cost(my_active)
             attached = getattr(my_active, "attached_energy", [])
             specific_needed, colorless_needed = get_energy_deficit(attached, cost)

             if specific_needed or colorless_needed > 0:
                 for aid, etype, pos in parsed_actions["attach"]:
                     if pos == 0:
                         if is_useful_energy(etype, attached, cost):
                             return aid

        bench_candidates = []
        for i, card in enumerate(my_bench):
            if card:
                score = 0
                name = getattr(card, "name", "").lower()
                hp = get_hp(card)
                max_hp = get_max_hp(card)
                if "ex" in name: score += 20
                if "mewtwo" in name: score += 10
                if "pikachu" in name: score += 10
                if max_hp >= 100: score += 5
                if hp < 40: score -= 50
                cost = get_best_attack_cost(card)
                attached = getattr(card, "attached_energy", [])
                spec, col = get_energy_deficit(attached, cost)
                if not spec and col == 0:
                    score -= 100
                bench_candidates.append((i, score))

        bench_candidates.sort(key=lambda x: x[1], reverse=True)

        for i, score in bench_candidates:
            if score < -20: continue
            card = my_bench[i]
            cost = get_best_attack_cost(card)
            attached = getattr(card, "attached_energy", [])
            target_pos = i + 1
            for aid, etype, pos in parsed_actions["attach"]:
                if pos == target_pos:
                    if is_useful_energy(etype, attached, cost):
                        return aid

        # Fallback: Prefer Active if low energy (need retreat/future attack)
        if my_active and count_energy(my_active) < 2:
             for aid, etype, pos in parsed_actions["attach"]:
                 if pos == 0: return aid

        # Else, prefer Bench over Active (spread risk)
        for aid, etype, pos in parsed_actions["attach"]:
            if pos > 0: return aid

        return parsed_actions["attach"][0][0]

    # J. Retreat Logic
    if parsed_actions["retreat"]:
        should_retreat = False
        # 1. Survival
        if my_active and my_hp <= 50:
             has_backup = False
             for card in my_bench:
                 if card and count_energy(card) >= 2 and get_hp(card) > 50:
                     has_backup = True
                     break
             if has_backup:
                 should_retreat = True

        # 2. Tempo/Damage (Restored)
        best_bench_idx = -1
        if not should_retreat and my_active and parsed_actions["attack"]:
             current_dmg = max([x[2] for x in parsed_actions["attack"]])
             if current_dmg < 40:
                 max_bench_dmg = 0
                 for i, card in enumerate(my_bench):
                     if card and count_energy(card) >= 2:
                         card_dmg = 0
                         for idx in range(len(getattr(card, "attacks", []))):
                             d = get_attack_damage(card, idx, my_bench)
                             if d > card_dmg: card_dmg = d

                         if card_dmg > max_bench_dmg:
                             max_bench_dmg = card_dmg
                             best_bench_idx = i

                 if max_bench_dmg > current_dmg + 20:
                     should_retreat = True

        if should_retreat:
            if best_bench_idx != -1:
                for aid, idx in parsed_actions["retreat"]:
                    if idx == best_bench_idx: return aid

            for aid, idx in parsed_actions["retreat"]:
                if idx == -1: return aid

            return parsed_actions["retreat"][0][0]

    # K. Attack (Non-Lethal)
    if parsed_actions["attack"]:
        best_attack = max(parsed_actions["attack"], key=lambda x: x[2])
        return best_attack[0]

    # L. Play remaining Supporters
    if parsed_actions["play_supporter"]:
        return parsed_actions["play_supporter"][0][0]

    # M. End Turn
    if parsed_actions["end_turn"]:
        return parsed_actions["end_turn"][0][0]

    return legal_actions[0]
