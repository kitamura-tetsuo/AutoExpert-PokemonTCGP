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

    for aid in legal_actions:
        name = game.action_name(aid)

        # Attack(Index)
        if name.startswith("Attack("):
            match = re.search(r"Attack\((\d+)\)", name)
            if match:
                idx = int(match.group(1))
                dmg = get_attack_damage(my_active, idx)
                parsed_actions["attack"].append((aid, idx, dmg))

        # Attach(Type, Pos) or Attach(Some(Type), Pos)
        # OR AttachEnergy(Pos, Type)
        elif name.startswith("Attach"):
            # Try specific type (observed format)
            match = re.search(r"Attach\((?:Some\()?(.*?)\)?, (\d+)\)", name)
            if match:
                etype = match.group(1).replace(")", "")
                pos = int(match.group(2))
                parsed_actions["attach"].append((aid, etype, pos))
            else:
                 # Try AttachEnergy(Pos, Type) format (prompt description)
                match = re.search(r"AttachEnergy\((\d+), (.*?)\)", name)
                if match:
                    pos = int(match.group(1))
                    etype = match.group(2)
                    parsed_actions["attach"].append((aid, etype, pos))
                else:
                    # Fallback
                    parsed_actions["attach"].append((aid, name, -1))

        # Evolve(HandIdx, Pos) -> Evolve(...)
        elif name.startswith("Evolve("):
            parsed_actions["evolve"].append((aid, name))

        # Place(Some(Name), 0) -> Active
        elif name.startswith("Place("):
            if ", 0)" in name:
                parsed_actions["place_active"].append((aid, name))
            else:
                parsed_actions["place_bench"].append((aid, name))

        # PlayPokemon(HandIdx, Pos) -> Bench
        elif name.startswith("PlayPokemon("):
            parsed_actions["place_bench"].append((aid, name))

        # Play(Some(Name)) -> Item/Supporter/Tool
        # OR UseItem(HandIdx), UseSupporter(HandIdx)
        elif name.startswith("Play(") or name.startswith("UseItem") or name.startswith("UseSupporter"):
            # Normalize name
            card_name = name
            match = re.search(r"Play\((?:Some\()?(.*?)\)?\)", name)
            if match:
                card_name = match.group(1)

            # Check for known Supporters (if not clearly UseItem)
            if name.startswith("UseSupporter"):
                parsed_actions["play_supporter"].append((aid, card_name))
            elif name.startswith("UseItem"):
                parsed_actions["play_item"].append((aid, card_name))
            else:
                # Play(...) case
                supporters = ["Research", "Sabrina", "Giovanni", "Erika", "Misty", "Blaine", "Koga", "Lt. Surge", "Brock", "Copycat", "Lisia", "Cyrus"]
                if any(s in card_name for s in supporters):
                    parsed_actions["play_supporter"].append((aid, card_name))
                else:
                    # Assume Item/Tool
                    parsed_actions["play_item"].append((aid, card_name))

        # UseAbility(Idx)
        elif name.startswith("UseAbility("):
            match = re.search(r"UseAbility\((\d+)\)", name)
            idx = int(match.group(1)) if match else 0
            parsed_actions["ability"].append((aid, idx))

        # Retreat(Pos) - Pos is likely the bench slot to switch to
        elif name.startswith("Retreat("):
            match = re.search(r"Retreat\((\d+)\)", name)
            idx = int(match.group(1)) if match else 0
            parsed_actions["retreat"].append((aid, idx))

        # Activate(Pos)
        elif name.startswith("Activate("):
            match = re.search(r"Activate\((\d+)\)", name)
            idx = int(match.group(1)) if match else 0
            parsed_actions["activate"].append((aid, idx))

        # EndTurn
        elif name == "EndTurn":
            parsed_actions["end_turn"].append((aid,))

    # --- 3. State Analysis ---
    opponent = 1 - current_player
    my_bench = state.get_bench_pokemon(current_player)
    my_hand = state.get_hand(current_player)
    opp_active = state.get_active_pokemon(opponent)
    opp_bench = state.get_bench_pokemon(opponent)

    opp_hp = get_hp(opp_active)
    my_hp = get_hp(my_active)

    try:
        opp_hand_size = len(state.get_hand(opponent))
    except:
        opp_hand_size = 0

    my_hand_size = len(my_hand)

    # --- 4. Decision Logic ---

    # A. Lethal Check (Priority 1)
    if parsed_actions["attack"]:
        # Check direct lethal
        for aid, idx, dmg in parsed_actions["attack"]:
            if dmg >= opp_hp:
                return aid

        # Check Giovanni lethal
        giovanni = [a for a in parsed_actions["play_supporter"] if "Giovanni" in a[1]]
        if giovanni:
            # Assuming +10 damage
            for aid, idx, dmg in parsed_actions["attack"]:
                if dmg + 10 >= opp_hp:
                    return giovanni[0][0]

    # B. Activate (Forced Switch / KO Replacement)
    if parsed_actions["activate"]:
        # If I have no active, I must choose one from bench
        if not my_active:
            # Best bench: Most energy -> Highest HP
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
            # Opponent forced switch (Sabrina)
            # Target opponent bench with lowest HP (to snipe)
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

    # C. Setup (Place Active)
    if parsed_actions["place_active"]:
        # Prefer High HP/EX
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

    # E. Bench Placement
    if parsed_actions["place_bench"]:
        # Always place basics to have backup
        return parsed_actions["place_bench"][0][0]

    # F. Abilities
    if parsed_actions["ability"]:
        # Generally beneficial
        return parsed_actions["ability"][0][0]

    # G. Items
    if parsed_actions["play_item"]:
        # Poke Ball / Great Ball -> Always
        balls = [a for a in parsed_actions["play_item"] if "Ball" in a[1]]
        if balls: return balls[0][0]

        # Rare Candy -> Always (if valid, means we can use it)
        candy = [a for a in parsed_actions["play_item"] if "RareCandy" in a[1]]
        if candy: return candy[0][0]

        # Potion
        potion = [a for a in parsed_actions["play_item"] if "Potion" in a[1]]
        if potion and my_active and my_hp < get_max_hp(my_active):
            return potion[0][0]

        # Red Card
        red_card = [a for a in parsed_actions["play_item"] if "RedCard" in a[1]]
        if red_card and opp_hand_size >= 4:
            return red_card[0][0]

        # Rocky Helmet
        helmet = [a for a in parsed_actions["play_item"] if "RockyHelmet" in a[1]]
        if helmet: return helmet[0][0]

    # H. Supporters
    if parsed_actions["play_supporter"]:
        # Research: Draw 2. Use if hand isn't too full.
        research = [a for a in parsed_actions["play_supporter"] if "Research" in a[1]]
        if research and my_hand_size <= 6:
            return research[0][0]

        # Copycat: Use if I have few cards and opponent has many
        copycat = [a for a in parsed_actions["play_supporter"] if "Copycat" in a[1]]
        if copycat and my_hand_size <= 4 and opp_hand_size >= 4:
            return copycat[0][0]

        # Sabrina: Disruption/Snipe
        sabrina = [a for a in parsed_actions["play_supporter"] if "Sabrina" in a[1]]
        if sabrina:
            # Use if we can't kill active but might kill bench, or just to disrupt setup
            if opp_hp > 60:
                 return sabrina[0][0]

        # Misty
        misty = [a for a in parsed_actions["play_supporter"] if "Misty" in a[1]]
        if misty: return misty[0][0]

    # I. Energy Attachment
    if parsed_actions["attach"]:
        # Prioritize Active if it needs energy (approx < 3)
        active_energy = count_energy(my_active)

        target_pos = -1
        if my_active and active_energy < 3:
            target_pos = 0
        else:
            # Find best bench
            best_bench_idx = -1
            max_hp = -1
            for i, card in enumerate(my_bench):
                if card:
                    hp = get_hp(card)
                    if hp > max_hp:
                        max_hp = hp
                        best_bench_idx = i + 1 # Assuming bench starts at 1

            if best_bench_idx != -1:
                target_pos = best_bench_idx
            else:
                target_pos = 0 # Fallback to active

        # Find match
        for aid, etype, pos in parsed_actions["attach"]:
            if pos == target_pos:
                return aid

        # Fallback
        return parsed_actions["attach"][0][0]

    # J. Retreat
    if parsed_actions["retreat"]:
        # Retreat if active is almost dead and we have bench backup
        if my_active and my_hp <= 40:
             # Check if any bench has energy
             has_backup = False
             for card in my_bench:
                 if card and count_energy(card) > 0:
                     has_backup = True
                     break

             if has_backup:
                 # Which retreat option?
                 # Assuming Retreat(idx) switches to bench idx
                 # Pick one with energy
                 for aid, idx in parsed_actions["retreat"]:
                     if idx < len(my_bench):
                         card = my_bench[idx]
                         if card and count_energy(card) > 0:
                             return aid
                 return parsed_actions["retreat"][0][0]

    # K. Attack (Best Damage)
    if parsed_actions["attack"]:
        # Sort by damage descending
        best_attack = max(parsed_actions["attack"], key=lambda x: x[2])
        return best_attack[0]

    # L. End Turn
    if parsed_actions["end_turn"]:
        return parsed_actions["end_turn"][0][0]

    return legal_actions[0]
