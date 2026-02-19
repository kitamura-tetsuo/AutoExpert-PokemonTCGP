import re
import random

def play(state, game):
    """
    Decides the best action for the current player.
    """
    legal_actions = game.legal_actions()
    if not legal_actions:
        return 0

    # Parse all actions once
    actions = []
    for aid in legal_actions:
        name = game.action_name(aid)
        actions.append((aid, name))

    # Group actions by type
    attacks = []
    attach_energy = []
    evolutions = []
    place_active = []
    place_bench = []
    play_card = [] # Items/Supporters/PlayPokemon
    abilities = []
    end_turn = []
    retreat = []

    for aid, name in actions:
        if name.startswith("Attack("):
            attacks.append((aid, name))
        elif name.startswith("Attach("):
            attach_energy.append((aid, name))
        elif name.startswith("Evolve("):
            evolutions.append((aid, name))
        elif name.startswith("Place("):
            if ", 0)" in name:
                place_active.append((aid, name))
            else:
                place_bench.append((aid, name))
        elif name.startswith("PlayPokemon("):
            place_bench.append((aid, name))
        elif name.startswith("Play(") or name.startswith("Use"):
            play_card.append((aid, name))
        elif name.startswith("UseAbility("):
            abilities.append((aid, name))
        elif name == "EndTurn":
            end_turn.append((aid, name))
        elif name.startswith("Retreat("):
            retreat.append((aid, name))

    # 1. Setup Phase: Must place active
    if place_active:
        return place_active[0][0]

    current_player = state.current_player
    try:
        active = state.get_active_pokemon(current_player)
    except:
        active = None

    try:
        bench = state.get_bench_pokemon(current_player)
    except:
        bench = []

    opponent = 1 - current_player
    try:
        opp_active = state.get_active_pokemon(opponent)
        opp_hp = opp_active.remaining_hp if opp_active else 0
    except:
        opp_active = None
        opp_hp = 0

    # Helper to check damage
    def get_attack_damage(attack_idx, extra_damage=0):
        if not active or not hasattr(active, 'attacks') or attack_idx >= len(active.attacks):
            return 0
        atk = active.attacks[attack_idx]
        dmg = getattr(atk, 'fixed_damage', 0)
        if dmg == 0:
            dmg = getattr(atk, 'damage', 0)
        return dmg + extra_damage

    # Helper: Check if card needs energy
    def get_missing_energy(card):
        if not hasattr(card, 'attacks') or not card.attacks:
            return []

        attached = [str(e) for e in card.attached_energy]

        # Find best attack (max damage)
        target_attack = None
        max_dmg = -1
        for atk in card.attacks:
            d = getattr(atk, 'fixed_damage', 0)
            if d >= max_dmg:
                max_dmg = d
                target_attack = atk

        if not target_attack:
            return []

        cost = getattr(target_attack, 'cost', [])
        # Sort cost: put "Colorless" at the end to ensure specific types match first
        # Because we iterate cost and remove from attached.
        # But wait, we want to match specific cost with specific energy.
        # So we should iterate SPECIFIC costs first.

        sorted_cost = sorted([str(c) for c in cost], key=lambda x: 1 if x == "Colorless" else 0)

        temp_attached = list(attached)
        missing = []

        for c_str in sorted_cost:
            found = False
            if c_str in temp_attached:
                temp_attached.remove(c_str)
                found = True
            elif c_str == "Colorless":
                 if temp_attached:
                     # Prefer removing Colorless or non-matching types if possible?
                     # Actually any energy pays for Colorless.
                     # Just pop first?
                     temp_attached.pop(0)
                     found = True

            if not found:
                missing.append(c_str)

        return missing

    # 2. Check for Lethal (Win Game)
    giovanni = [a for a in play_card if "Giovanni" in a[1]]

    if attacks:
        max_dmg = -1
        best_lethal = None
        best_attack = attacks[0][0]

        for aid, name in attacks:
            match = re.search(r"Attack\((\d+)\)", name)
            if match:
                idx = int(match.group(1))
                dmg = get_attack_damage(idx)

                # Check lethal without Giovanni
                if dmg >= opp_hp and opp_hp > 0:
                    return aid

                # Check lethal WITH Giovanni
                if giovanni and (dmg + 10) >= opp_hp and opp_hp > 0:
                    return giovanni[0][0]

                if dmg > max_dmg:
                    max_dmg = dmg
                    best_attack = aid

        # If lethal found (handled above), return it.
        # Otherwise, we will use best_attack later.

    # 3. Evolution (High Priority)
    if evolutions:
        return evolutions[0][0]

    # 4. Attach Energy
    if attach_energy:
        # Check Active Needs
        if active:
            missing = get_missing_energy(active)
            if missing:
                attach_active = [a for a in attach_energy if ", 0)" in a[1]]
                for action_tuple in attach_active:
                    aid, name = action_tuple
                    match = re.search(r"Attach\((.+?), 0\)", name)
                    if match:
                        etype = match.group(1)
                        if etype.startswith("Some("): etype = etype[5:-1]

                        if etype in missing or "Colorless" in missing:
                            return aid

        # Check Bench Needs
        # Position 1, 2, 3...
        # attach_bench = [a for a in attach_energy if ", 0)" not in a[1]]
        # We need to map position to card
        # bench is a list [PlayedCard, PlayedCard, ...]
        # bench indices correspond to position 1, 2, 3

        for i, b_card in enumerate(bench):
            if b_card is not None:
                missing = get_missing_energy(b_card)
                if missing:
                    pos = i + 1
                    # Find actions for this pos
                    # Action format: Attach(Type, Pos) -> Pos matches integer
                    # Regex: Attach(..., pos)

                    target_actions = [a for a in attach_energy if f", {pos})" in a[1]]
                    for action_tuple in target_actions:
                        aid, name = action_tuple
                        match = re.search(r"Attach\((.+?), " + str(pos) + r"\)", name)
                        if match:
                            etype = match.group(1)
                            if etype.startswith("Some("): etype = etype[5:-1]

                            if etype in missing or "Colorless" in missing:
                                return aid

        # Fallback: Attach to Bench (if available) then Active
        attach_bench = [a for a in attach_energy if ", 0)" not in a[1]]
        if attach_bench:
            return attach_bench[0][0]

        attach_active = [a for a in attach_energy if ", 0)" in a[1]]
        if attach_active:
             return attach_active[0][0]

    # 5. Play Basics to Bench
    if place_bench:
        return place_bench[0][0]

    # 6. Supporters/Items
    if play_card:
        # Professor's Research
        research = [a for a in play_card if "Research" in a[1]]
        hand = state.get_hand(current_player)
        if research and len(hand) < 5:
             return research[0][0]

        # Potions
        potions = [a for a in play_card if "Potion" in a[1]]
        if potions and active and active.remaining_hp < active.total_hp:
            return potions[0][0]

        # PokeBall / Computer Search
        search_items = [a for a in play_card if "Ball" in a[1] or "Computer" in a[1]]
        if search_items:
            return search_items[0][0]

        # Sabrina (Use if we can't kill active)
        sabrina = [a for a in play_card if "Sabrina" in a[1]]
        if sabrina:
            can_kill = False
            # Check if we can kill current active
            if attacks:
                for aid, name in attacks:
                    match = re.search(r"Attack\((\d+)\)", name)
                    if match:
                        idx = int(match.group(1))
                        if get_attack_damage(idx) >= opp_hp:
                            can_kill = True

            if not can_kill:
                 return sabrina[0][0]

        # Red Card
        red_card = [a for a in play_card if "RedCard" in a[1]]
        try:
            opp_hand = state.get_hand(opponent)
            if red_card and len(opp_hand) >= 4:
                return red_card[0][0]
        except:
            pass

        # X Speed
        x_speed = [a for a in play_card if "XSpeed" in a[1]]
        if x_speed and active and active.remaining_hp <= 40:
             return x_speed[0][0]

    # 7. Abilities
    if abilities:
        return abilities[0][0]

    # 8. Attack (Best Damage)
    if attacks:
        # Re-calculate best attack
        max_dmg = -1
        best_attack = attacks[0][0]

        for aid, name in attacks:
            match = re.search(r"Attack\((\d+)\)", name)
            if match:
                idx = int(match.group(1))
                dmg = get_attack_damage(idx)
                if dmg > max_dmg:
                    max_dmg = dmg
                    best_attack = aid
        return best_attack

    # 9. Retreat
    if retreat and active and active.remaining_hp <= 40:
        bench_count = 0
        for p in bench:
            if p is not None:
                bench_count += 1
        if bench_count > 0:
            return retreat[0][0]

    # 10. End Turn
    if end_turn:
        return end_turn[0][0]

    # Fallback
    return legal_actions[0]
