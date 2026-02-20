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
        # Returns string representation of energy type
        if card and hasattr(card, "energy_type"):
            return str(card.energy_type)
        return "Colorless"

    def get_attack_damage(card, attack_idx, my_bench=None):
        if not card or not hasattr(card, "attacks") or attack_idx >= len(card.attacks):
            return 0
        atk = card.attacks[attack_idx]
        dmg = getattr(atk, "fixed_damage", 0)

        # Handle Pikachu ex "Circle Circuit"
        if "Pikachu ex" in getattr(card, "name", "") and "Circle Circuit" in getattr(atk, "name", ""):
            # Count lightning types on bench
            lightning_count = 0
            if my_bench:
                for b in my_bench:
                    if b and "Lightning" in get_energy_type(b):
                        lightning_count += 1
            return 30 * lightning_count

        return dmg

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
            return []

        # Strategy: Aim for the attack with the HIGHEST Energy Cost (assuming it's the strongest/ultimate)
        # This avoids skipping "Circle Circuit" if it reports 0 damage currently.

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

    # --- 2. State Analysis (Moved to top) ---
    current_player = state.current_player
    my_active = state.get_active_pokemon(current_player)
    my_bench = state.get_bench_pokemon(current_player)

    opponent = 1 - current_player
    opp_active = state.get_active_pokemon(opponent)
    opp_bench = state.get_bench_pokemon(opponent)

    opp_hp = get_hp(opp_active)
    opp_max_hp = get_max_hp(opp_active)
    my_hp = get_hp(my_active)
    my_max_hp = get_max_hp(my_active)

    try:
        opp_hand_size = len(state.get_hand(opponent))
    except:
        opp_hand_size = 0

    my_hand_size = len(state.get_hand(current_player))

    # --- 3. Parse Actions ---
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

    for aid in legal_actions:
        name = game.action_name(aid)

        if name.startswith("Attack("):
            match = re.search(r"Attack\((\d+)\)", name)
            if match:
                idx = int(match.group(1))
                dmg = get_attack_damage(my_active, idx, my_bench) # DYNAMIC DAMAGE
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

    # --- 4. Decision Logic ---

    # A. Lethal Check (Priority 1)
    # Check if we can win or KO active without Supporters
    if parsed_actions["attack"]:
        # Sort by damage descending, then by energy cost (heuristic: assume idx 0 is cheaper/weaker)
        # Actually, if both lethal, pick the one with lower index (usually cheaper)
        lethal_attacks = []
        for aid, idx, dmg in parsed_actions["attack"]:
            if can_kill(dmg, opp_hp):
                lethal_attacks.append((aid, idx, dmg))

        if lethal_attacks:
            # Sort by index ascending (cheaper first)
            lethal_attacks.sort(key=lambda x: x[1])
            return lethal_attacks[0][0]

    # B. Activate (Switching/Targeting)
    if parsed_actions["activate"]:
        # Context 1: We need to switch in a new Active (our active is None)
        if not my_active:
            # Pick best bench to be active
            best_aid = parsed_actions["activate"][0][0]
            max_score = -1
            for aid, idx in parsed_actions["activate"]:
                score = 0
                if idx < len(my_bench):
                    card = my_bench[idx]
                    if card:
                         # Prioritize card with energy and high HP
                         score = count_energy(card) * 100 + get_hp(card)
                if score > max_score:
                    max_score = score
                    best_aid = aid
            return best_aid
        else:
            # Context 2: We are targeting opponent (e.g. Sabrina, Boss, or Attack effect)
            best_aid = parsed_actions["activate"][0][0]
            # Check if any bench can be KO'd by our current max attack
            max_dmg = 0
            if parsed_actions["attack"]:
                max_dmg = max(a[2] for a in parsed_actions["attack"])

            # Find vulnerable targets
            vulnerable = []
            for aid, idx in parsed_actions["activate"]:
                if idx < len(opp_bench):
                    card = opp_bench[idx]
                    if card:
                        hp = get_hp(card)
                        if hp <= max_dmg:
                            vulnerable.append((aid, hp))

            if vulnerable:
                # Pick the one with lowest HP to be safe.
                vulnerable.sort(key=lambda x: x[1])
                return vulnerable[0][0]

            # If no lethal on bench, pick the one with lowest HP
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

    # C. Setup (Place Active)
    if parsed_actions["place_active"]:
        def score_card(name):
            s = 0
            if "ex" in name.lower() or "EX" in name: s += 100
            if "mewtwo" in name.lower(): s += 50
            if "pikachu" in name.lower(): s += 60 # Pikachu is fast
            return s
        best = max(parsed_actions["place_active"], key=lambda x: score_card(x[1]))
        return best[0]

    # D. Evolution
    if parsed_actions["evolve"]:
        # Always evolve if possible
        return parsed_actions["evolve"][0][0]

    # E. Bench Placement
    if parsed_actions["place_bench"]:
        # Prioritize EX > High HP
        def score_bench(name):
            s = 0
            if "ex" in name.lower() or "EX" in name: s += 100
            if "mewtwo" in name.lower(): s += 50
            if "pikachu" in name.lower(): s += 50
            if "articuno" in name.lower(): s += 50
            if "starmie" in name.lower(): s += 50
            return s

        best = max(parsed_actions["place_bench"], key=lambda x: score_bench(x[1]))
        return best[0]

    # F. Play Supporters (Priority Handling)
    # 1. Misty (RNG energy) - Play first to see what we get
    misty = [a for a in parsed_actions["play_supporter"] if "Misty" in a[1]]
    if misty:
        return misty[0][0]

    # 2. Professor's Research (Draw 2) - Play if we need cards (hand <= 5 usually safe)
    research = [a for a in parsed_actions["play_supporter"] if "Research" in a[1]]
    if research:
        # Check deck size if possible to avoid deck out?
        # But usually drawing is good.
        if my_hand_size < 8: # Arbitrary high limit
             return research[0][0]

    # 3. Giovanni (Damage Boost) - Only if it enables lethal
    giovanni = [a for a in parsed_actions["play_supporter"] if "Giovanni" in a[1]]
    if giovanni and parsed_actions["attack"]:
        can_lethal_with_gio = False
        for aid, idx, dmg in parsed_actions["attack"]:
            if dmg + 10 >= opp_hp:
                can_lethal_with_gio = True
                break
        if can_lethal_with_gio:
            return giovanni[0][0]

    # 4. Sabrina (Force Switch)
    sabrina = [a for a in parsed_actions["play_supporter"] if "Sabrina" in a[1]]
    if sabrina:
        # Use if we CANNOT kill active, but maybe can kill something else?
        # Or if Active is very strong (high HP) and we want to avoid it.

        # Check max damage we can do
        my_max_dmg = 0
        if parsed_actions["attack"]:
            my_max_dmg = max(a[2] for a in parsed_actions["attack"])

        # If we can kill active, don't use Sabrina (unless active is worth less points? ex gives 2)
        # Assuming lethal on active is preferred unless we can't kill it.
        can_kill_active = any(d >= opp_hp for _, _, d in parsed_actions["attack"])

        if not can_kill_active:
            # 1. Check if we can kill any benched
            can_kill_bench = False
            for b in opp_bench:
                if b and get_hp(b) <= my_max_dmg:
                    can_kill_bench = True
                    break

            if can_kill_bench:
                return sabrina[0][0]

            # 2. Check if opponent active is fully powered and we want to stall
            opp_active_energy = count_energy(opp_active)
            if opp_active_energy >= 3:
                # If bench has a pokemon with 0 energy (and high retreat cost ideally, but simple check first)
                can_stall = False
                for b in opp_bench:
                    if b and count_energy(b) == 0:
                        can_stall = True
                        break
                if can_stall:
                    return sabrina[0][0]

            # 3. Also use if active is full HP ex (>120) and we can chip at bench
            if opp_hp >= 120:
                return sabrina[0][0]

    # G. Abilities
    if parsed_actions["ability"]:
        # Generally use abilities
        return parsed_actions["ability"][0][0]

    # H. Items
    if parsed_actions["play_item"]:
        # Potion
        potion = [a for a in parsed_actions["play_item"] if "Potion" in a[1]]
        if potion and my_active and my_hp < my_max_hp:
            # Use if healing 20 saves us from being KO'd?
            # Rough check: if HP <= 40, healing to 60 might save from 50 dmg attack.
            if my_hp <= 50:
                return potion[0][0]

        # Red Card
        red_card = [a for a in parsed_actions["play_item"] if "RedCard" in a[1]]
        if red_card and opp_hand_size >= 4:
            return red_card[0][0]

        # Poke Ball / etc
        balls = [a for a in parsed_actions["play_item"] if "Ball" in a[1]]
        if balls: return balls[0][0]

        candy = [a for a in parsed_actions["play_item"] if "RareCandy" in a[1]]
        if candy: return candy[0][0]

        helmet = [a for a in parsed_actions["play_item"] if "RockyHelmet" in a[1]]
        if helmet: return helmet[0][0]

        hand_scope = [a for a in parsed_actions["play_item"] if "HandScope" in a[1]]
        if hand_scope: return hand_scope[0][0]

        # X Speed / Switch (not explicitly named in parser but might be there)

    # I. Other Supporters (Low Priority)
    if parsed_actions["play_supporter"]:
        # Play any remaining supporter if we haven't played one
        # Copycat
        copycat = [a for a in parsed_actions["play_supporter"] if "Copycat" in a[1]]
        if copycat and opp_hand_size > my_hand_size:
            return copycat[0][0]

        # Others
        return parsed_actions["play_supporter"][0][0]

    # J. Energy Attachment
    if parsed_actions["attach"]:
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

        # 2. Try to satisfy Bench deficit (prioritize EX or high HP)
        # Sort bench by priority
        bench_indices = []
        for i, card in enumerate(my_bench):
            if card:
                score = 0
                if "ex" in getattr(card, "name", ""): score += 10
                if get_max_hp(card) > 100: score += 5
                # Don't attach to dying pokemon
                if get_hp(card) < 40: score -= 10
                bench_indices.append((i, score))

        bench_indices.sort(key=lambda x: x[1], reverse=True)

        for i, score in bench_indices:
             card = my_bench[i]
             cost = get_best_attack_cost(card)
             attached = getattr(card, "attached_energy", [])
             specific_needed, colorless_needed = get_energy_deficit(attached, cost)

             if specific_needed or colorless_needed > 0:
                 pos_idx = i + 1
                 for aid, etype, pos in parsed_actions["attach"]:
                     if pos == pos_idx:
                         if is_useful_energy(etype, attached, cost):
                             return aid

        # 3. Fallback: Attach to active if not full, else random bench
        target_pos = 0
        if count_energy(my_active) < 4:
            target_pos = 0
        else:
            target_pos = 1

        for aid, etype, pos in parsed_actions["attach"]:
            if pos == target_pos:
                return aid
        return parsed_actions["attach"][0][0]

    # K. Retreat
    if parsed_actions["retreat"]:
        # Retreat if Active is heavily damaged and we have a ready bench
        if my_active and my_hp <= 40:
             has_backup = False
             for card in my_bench:
                 if card and count_energy(card) >= 2: # heuristic: backup has energy
                     has_backup = True
                     break
             if has_backup:
                 for aid, idx in parsed_actions["retreat"]:
                     # Try to switch to the backup
                     if idx < len(my_bench):
                         card = my_bench[idx]
                         if card and count_energy(card) >= 2:
                             return aid
                 return parsed_actions["retreat"][0][0]

        # Also retreat if Active has NO energy and Bench has full energy (Setup complete)
        if my_active and count_energy(my_active) == 0:
            for card in my_bench:
                 if card and count_energy(card) >= 3:
                     return parsed_actions["retreat"][0][0]

    # L. Attack (Best non-lethal)
    if parsed_actions["attack"]:
        best_attack = max(parsed_actions["attack"], key=lambda x: x[2])
        return best_attack[0]

    # M. End Turn
    if parsed_actions["end_turn"]:
        return parsed_actions["end_turn"][0][0]

    return legal_actions[0]
