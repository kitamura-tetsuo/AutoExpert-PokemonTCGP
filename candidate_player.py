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
    play_card = []
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
        elif name.startswith("Play("):
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
    active = state.get_active_pokemon(current_player)
    bench = state.get_bench_pokemon(current_player)
    opponent = 1 - current_player
    opp_active = state.get_active_pokemon(opponent)
    opp_hp = opp_active.remaining_hp if opp_active else 0

    # Helper to check damage
    def get_attack_damage(attack_obj):
        dmg = getattr(attack_obj, 'damage', 0)
        if dmg == 0:
            dmg = getattr(attack_obj, 'fixed_damage', 0)
        return dmg

    # 2. Check for Lethal (Win Game)
    if attacks and active and hasattr(active, 'attacks'):
        for aid, name in attacks:
            match = re.search(r"Attack\((\d+)\)", name)
            if match:
                idx = int(match.group(1))
                if idx < len(active.attacks):
                    atk = active.attacks[idx]
                    dmg = get_attack_damage(atk)
                    # Simple lethal check. Doesn't account for resistance/weakness if not computed in damage property.
                    # Assuming damage property is base damage.
                    # But verifying lethal is always good.
                    if dmg >= opp_hp and opp_hp > 0:
                        return aid

    # 3. Evolution (High Priority)
    if evolutions:
        # Prioritize evolving active
        for aid, name in evolutions:
            if ", 0)" in name:
                return aid
        return evolutions[0][0]

    # 4. Bench Setup (Place Basics)
    bench_count = len([p for p in bench if p is not None])
    if place_bench and bench_count < 3:
        # Just place whatever we can to build board
        return place_bench[0][0]

    # 5. Use Supporters (Draw)
    # Prioritize Professor's Research / other draw supporters
    hand = state.get_hand(current_player)
    hand_size = len(hand)

    draw_supporters = [a for a in play_card if "Professor" in a[1] or "Research" in a[1] or "Erika" in a[1] or "Bill" in a[1]]
    if draw_supporters:
        # Use if hand is small OR we haven't attached energy yet and have none in hand
        # We can't easily check hand content types without card objects, but low hand size is a good proxy.
        if hand_size < 4:
            return draw_supporters[0][0]

    # 6. Attach Energy
    if attach_energy:
        # Logic:
        # 1. If Active needs energy for max attack, attach to active.
        # 2. If Active full, attach to bench.

        needs_energy = False
        if active and hasattr(active, 'attacks'):
            attached = len(active.attached_energy)
            max_cost = 0
            for atk in active.attacks:
                cost_val = 0
                if hasattr(atk, 'cost'):
                    if isinstance(atk.cost, int): cost_val = atk.cost
                    elif isinstance(atk.cost, list): cost_val = len(atk.cost)
                if cost_val > max_cost: max_cost = cost_val

            if attached < max_cost:
                needs_energy = True

        attach_active = [a for a in attach_energy if ", 0)" in a[1]]
        attach_bench_acts = [a for a in attach_energy if ", 0)" not in a[1]]

        if needs_energy and attach_active:
            return attach_active[0][0]
        elif attach_bench_acts:
            # Attach to bench if available
            return attach_bench_acts[0][0]
        elif attach_active:
            # If no bench to attach to, attach to active even if full (overcharge/thin deck)
            return attach_active[0][0]

    # 7. Use Items (Potions, Balls, etc)
    potions = [a for a in play_card if "Potion" in a[1]]
    if potions and active and active.remaining_hp < active.total_hp:
        # Heal if damaged
        return potions[0][0]

    balls = [a for a in play_card if "Ball" in a[1]]
    if balls and bench_count < 3:
        # Search for pokemon
        return balls[0][0]

    others = [a for a in play_card if a not in potions and a not in balls and a not in draw_supporters]
    if others:
        # Use X Speed, Red Card, etc.
        return others[0][0]

    # 8. Abilities
    if abilities:
        return abilities[0][0]

    # 9. Attack (Best Damage)
    if attacks:
        best_attack = None
        max_dmg = -1
        for aid, name in attacks:
            match = re.search(r"Attack\((\d+)\)", name)
            if match and active and hasattr(active, 'attacks'):
                idx = int(match.group(1))
                if idx < len(active.attacks):
                    atk = active.attacks[idx]
                    dmg = get_attack_damage(atk)
                    if dmg > max_dmg:
                        max_dmg = dmg
                        best_attack = aid

        if best_attack:
            return best_attack
        return attacks[0][0]

    # 10. Retreat
    # If we are here, we can't attack, or we choose not to (but we usually choose to attack if possible).
    # If active is stuck (no energy to attack) and we have bench with energy, retreat?
    # For now, simple logic: if active is near death, try to retreat.
    if retreat and active and active.remaining_hp <= 40 and bench_count > 0:
        return retreat[0][0]

    # 11. End Turn
    if end_turn:
        return end_turn[0][0]

    return legal_actions[0]
