import re

def play(state, game):
    """
    Decides the best action for the current player using optimized heuristics.
    """
    legal_actions = game.legal_actions()
    if not legal_actions:
        return 0

    # --- 1. Parsing Actions ---
    parsed_actions = {
        "attack": [],       # (aid, name, idx, damage)
        "attach": [],       # (aid, energy_type, pos)
        "evolve": [],       # (aid, name)
        "place_active": [], # (aid, name)
        "place_bench": [],  # (aid, name)
        "play_item": [],    # (aid, name)
        "play_supporter": [], # (aid, name)
        "ability": [],      # (aid, idx)
        "retreat": [],      # (aid, name)
        "activate": [],     # (aid, idx)
        "end_turn": []      # (aid, name)
    }

    # Pre-scan for damage to avoid recalculating
    current_player = state.current_player
    my_active = state.get_active_pokemon(current_player)

    def get_attack_damage(card, attack_idx):
        if not card or not hasattr(card, "attacks") or attack_idx >= len(card.attacks):
            return 0
        atk = card.attacks[attack_idx]
        return getattr(atk, "fixed_damage", 0)

    for aid in legal_actions:
        name = game.action_name(aid)

        if name.startswith("Attack("):
            match = re.search(r"Attack\((\d+)\)", name)
            idx = int(match.group(1)) if match else 0
            dmg = get_attack_damage(my_active, idx)
            parsed_actions["attack"].append((aid, name, idx, dmg))

        elif name.startswith("Attach"):
            # Format: Attach(Some(Type), Pos) or Attach(Type, Pos)
            match = re.search(r"Attach\((?:Some\()?(.*?)\)?, (\d+)\)", name)
            if match:
                etype = match.group(1).replace(")", "")
                pos = int(match.group(2))
                parsed_actions["attach"].append((aid, etype, pos))
            else:
                 # Try AttachEnergy(Pos, Type) format
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

    # --- 2. State Analysis ---
    opponent = 1 - current_player
    my_bench = state.get_bench_pokemon(current_player)
    my_hand = state.get_hand(current_player)
    opp_active = state.get_active_pokemon(opponent)
    opp_bench = state.get_bench_pokemon(opponent)

    try:
        opp_hand_size = len(state.get_hand(opponent))
    except:
        opp_hand_size = 0

    def get_hp(card):
        return getattr(card, "remaining_hp", 0) if card else 0

    def get_max_hp(card):
        return getattr(card, "total_hp", 0) if card else 0

    def count_energy(card):
        return len(card.attached_energy) if (card and hasattr(card, "attached_energy")) else 0

    def get_max_damage_potential(card):
        if not card or not hasattr(card, "attacks"): return 0
        max_d = 0
        for atk in card.attacks:
            d = getattr(atk, "fixed_damage", 0)
            if d > max_d: max_d = d
        return max_d

    opp_hp = get_hp(opp_active)

    # --- 3. Decision Logic ---

    # A. Activate (Forced Switch / Target Selection)
    if parsed_actions["activate"]:
        # If no active, we must select one from bench
        if not my_active:
            # Pick the one with most energy, then highest HP
            best_act = parsed_actions["activate"][0]
            max_score = -1
            for aid, idx in parsed_actions["activate"]:
                if idx < len(my_bench):
                    card = my_bench[idx]
                    if card:
                        # Score: Energy * 100 + HP
                        score = count_energy(card) * 100 + get_hp(card)
                        if score > max_score:
                            max_score = score
                            best_act = (aid, idx)
            return best_act[0]
        else:
            # Sabrina target selection (opponent bench)
            # Pick the one we can kill easiest (lowest HP)
            best_act = parsed_actions["activate"][0]
            min_hp = 999
            for aid, idx in parsed_actions["activate"]:
                if opp_bench and idx < len(opp_bench):
                    card = opp_bench[idx]
                    if card:
                        hp = get_hp(card)
                        if hp < min_hp:
                            min_hp = hp
                            best_act = (aid, idx)
            return best_act[0]

    # B. Setup Phase (Place Active)
    if parsed_actions["place_active"]:
        def score_starter(name):
            s = 0
            if "ex" in name.lower() or "EX" in name: s += 100
            elif "mewtwo" in name.lower(): s += 80
            elif "basic" in name.lower(): s += 50
            # Tie breaker: Prefer not to place utility basics if possible?
            # Actually higher HP is generally better.
            return s

        # We can't see HP of cards in hand easily without parsing names or having a DB.
        # So rely on name heuristics.
        best = max(parsed_actions["place_active"], key=lambda x: score_starter(x[1]))
        return best[0]

    # C. Lethal Check (Attacks & Giovanni)
    if parsed_actions["attack"]:
        # Sort attacks by index (prefer 0 as it's usually cheaper)
        sorted_attacks = sorted(parsed_actions["attack"], key=lambda x: x[2])

        # Check standard lethal
        for aid, name, idx, dmg in sorted_attacks:
            if dmg >= opp_hp:
                return aid

        # Check Giovanni lethal
        giovanni = [a for a in parsed_actions["play_supporter"] if "Giovanni" in a[1]]
        if giovanni:
            # Assuming Giovanni adds +10 damage
            for aid, name, idx, dmg in sorted_attacks:
                if dmg + 10 >= opp_hp:
                    return giovanni[0][0] # Play Giovanni first

    # D. Evolution (Always good)
    if parsed_actions["evolve"]:
        # Prefer evolving active if possible, or highest potential bench
        return parsed_actions["evolve"][0][0]

    # E. Abilities
    if parsed_actions["ability"]:
        return parsed_actions["ability"][0][0]

    # F. Supporters
    if parsed_actions["play_supporter"]:
        # Misty: High priority if we need energy
        misty = [a for a in parsed_actions["play_supporter"] if "Misty" in a[1]]
        if misty:
            return misty[0][0]

        # Sabrina: Disruption or finding a kill
        sabrina = [a for a in parsed_actions["play_supporter"] if "Sabrina" in a[1]]
        if sabrina:
            # Use if opponent active is tanky (>100 HP) and we can't kill it
            # Or if we have a good attack ready that can kill a benched mon
            if opp_hp > 70:
                return sabrina[0][0]

        # Professor's Research: Draw
        research = [a for a in parsed_actions["play_supporter"] if "Research" in a[1]]
        if research:
            if len(my_hand) <= 5:
                return research[0][0]

    # G. Items
    if parsed_actions["play_item"]:
        poke_ball = [a for a in parsed_actions["play_item"] if "Ball" in a[1]]
        if poke_ball: return poke_ball[0][0] # Always good to search

        red_card = [a for a in parsed_actions["play_item"] if "RedCard" in a[1]]
        if red_card and opp_hand_size >= 4:
            return red_card[0][0]

        potion = [a for a in parsed_actions["play_item"] if "Potion" in a[1]]
        if potion and my_active:
            hp = get_hp(my_active)
            max_hp = get_max_hp(my_active)
            # Use if damaged but not effectively dead
            if hp < max_hp and hp > 0:
                 return potion[0][0]

        x_speed = [a for a in parsed_actions["play_item"] if "XSpeed" in a[1]]
        if x_speed and my_active:
            # Use if we want to retreat (handled in retreat logic? No, this is item usage)
            # If we are confused/asleep or just need to switch to a better attacker
            pass

    # H. Energy Attachment
    if parsed_actions["attach"]:
        # Where to attach?
        target_pos = -1

        # 1. Check Active
        active_energy = count_energy(my_active)
        active_needs = 3 # Approximation, most attacks need 1-4. 3 is a safe bet.

        # Check if active is main attacker
        if my_active and active_energy < active_needs:
             target_pos = 0
        else:
            # 2. Check Bench for best potential attacker
            best_bench_idx = -1
            max_potential = -1
            for i, card in enumerate(my_bench):
                if card:
                    # Prioritize high potential + high HP
                    pot = get_max_damage_potential(card) + get_hp(card)
                    if pot > max_potential:
                        max_potential = pot
                        best_bench_idx = i + 1

            if best_bench_idx != -1:
                target_pos = best_bench_idx
            else:
                # Fallback to active if no good bench
                target_pos = 0

        # Find the action that attaches to target_pos
        for aid, etype, pos in parsed_actions["attach"]:
            if pos == target_pos:
                return aid

        # Fallback: any attachment
        return parsed_actions["attach"][0][0]

    # I. Bench Placement
    if parsed_actions["place_bench"]:
        # Generally good to fill bench, but maybe not if we have too many liabilities?
        # For now, always place.
        return parsed_actions["place_bench"][0][0]

    # J. Retreat
    if parsed_actions["retreat"]:
        # Retreat if active is low HP and we have a better option
        if my_active and get_hp(my_active) <= 30:
             # Check if we have a bench pokemon with energy
             for aid, name in parsed_actions["retreat"]:
                 # Which bench slot is this? Retreat(idx)?
                 match = re.search(r"Retreat\((\d+)\)", name)
                 if match:
                     idx = int(match.group(1))
                     if idx < len(my_bench):
                         card = my_bench[idx]
                         if card and get_hp(card) > 50:
                             return aid
             return parsed_actions["retreat"][0][0]

    # K. Attack (Non-lethal)
    if parsed_actions["attack"]:
        # Pick highest damage
        best_aid = parsed_actions["attack"][0][0]
        max_dmg = -1
        for aid, name, idx, dmg in parsed_actions["attack"]:
            if dmg > max_dmg:
                max_dmg = dmg
                best_aid = aid
        return best_aid

    # L. End Turn
    if parsed_actions["end_turn"]:
        return parsed_actions["end_turn"][0][0]

    # Fallback
    return legal_actions[0]
