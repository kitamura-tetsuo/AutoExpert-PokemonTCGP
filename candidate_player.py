import re

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

    # Categorize actions
    attacks = []
    attach_energy_active = []
    attach_energy_bench = []
    evolutions_active = []
    evolutions_bench = []
    place_active = []
    place_bench = []

    supporters = [] # Draw supporters mostly
    items = [] # Items, Stadiums, other trainers
    abilities = []
    retreat = []
    end_turn = []

    # Helper for categorizing Play actions (Trainers)
    def is_supporter(name):
        return any(x in name for x in ["Professor", "Research", "Erika", "Bill", "Misty", "Giovanni", "Sabrina", "Koga", "Lt. Surge", "Blaine", "Brock"])

    for aid, name in actions:
        if name.startswith("Attack("):
            attacks.append((aid, name))
        elif name.startswith("Attach("):
            # Format: Attach([(0, Psychic)], true) OR Attach(Psychic, 0)
            # Check for active position (0)
            if "(0," in name or "[(0," in name or ", 0)" in name:
                attach_energy_active.append((aid, name))
            else:
                attach_energy_bench.append((aid, name))
        elif name.startswith("Evolve("):
            if ", 0)" in name:
                evolutions_active.append((aid, name))
            else:
                evolutions_bench.append((aid, name))
        elif name.startswith("Place("):
            if ", 0)" in name:
                place_active.append((aid, name))
            else:
                place_bench.append((aid, name))
        elif name.startswith("Play("):
            # Play usually means playing a Trainer card (Item, Supporter, Stadium)
            if is_supporter(name):
                supporters.append((aid, name))
            else:
                items.append((aid, name))
        elif name.startswith("UseItem("):
            items.append((aid, name))
        elif name.startswith("UseSupporter("):
            supporters.append((aid, name))
        elif name.startswith("UseAbility("):
            abilities.append((aid, name))
        elif name == "EndTurn":
            end_turn.append((aid, name))
        elif name.startswith("Retreat("):
            retreat.append((aid, name))
        else:
            # Fallback
            items.append((aid, name))

    # 1. Setup Phase: Must place active
    if place_active:
        return place_active[0][0]

    current_player = state.current_player
    active = state.get_active_pokemon(current_player)

    # Safety check: if active is None but game continues (e.g. KO replacement),
    # and no place_active actions, maybe we need to select active from bench?
    # Usually handled by specific actions, but let's assume if active is None we can't do much else.
    if active is None:
        # If we have bench, maybe a specialized action is available?
        # But usually place_active handles initial setup.
        pass

    opp_active = state.get_active_pokemon(1 - current_player)
    opp_hp = opp_active.remaining_hp if opp_active else 0

    # Helper to estimate damage
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
                    if dmg >= opp_hp and opp_hp > 0:
                        return aid

    # 3. Evolution (High Priority)
    if evolutions_active:
        return evolutions_active[0][0]
    if evolutions_bench:
        return evolutions_bench[0][0]

    # 4. Draw Supporters (If hand low)
    hand = state.get_hand(current_player)
    hand_size = len(hand)

    draw_supporters = []
    for aid, name in supporters:
        if "Professor" in name or "Research" in name or "Erika" in name or "Bill" in name:
            draw_supporters.append(aid)

    if draw_supporters and hand_size < 4:
        return draw_supporters[0]

    # 5. Energy Attachment
    needs_energy = False
    if active and hasattr(active, 'attacks'):
        attached = len(active.attached_energy)
        max_cost = 0
        for atk in active.attacks:
            cost_val = 0
            if hasattr(atk, 'cost'):
                if isinstance(atk.cost, int):
                    cost_val = atk.cost
                elif isinstance(atk.cost, list):
                    cost_val = len(atk.cost)
            if hasattr(atk, 'energy_required'):
                 if isinstance(atk.energy_required, int):
                     cost_val = atk.energy_required
                 elif isinstance(atk.energy_required, list):
                     cost_val = len(atk.energy_required)

            if cost_val > max_cost:
                max_cost = cost_val

        if attached < max_cost:
            needs_energy = True

    if needs_energy and attach_energy_active:
        return attach_energy_active[0][0]

    # If active full, attach to bench
    if attach_energy_bench:
        return attach_energy_bench[0][0]

    # If no bench, attach to active anyway
    if attach_energy_active:
        return attach_energy_active[0][0]

    # 6. Bench Setup
    bench = state.get_bench_pokemon(current_player)
    bench_count = len([p for p in bench if p is not None])

    if place_bench and bench_count < 3:
        return place_bench[0][0]

    # 7. Items
    potions = [aid for aid, name in items if "Potion" in name]
    if potions and active and active.remaining_hp < active.total_hp:
        return potions[0]

    balls = [aid for aid, name in items if "Ball" in name]
    if balls and bench_count < 3:
        return balls[0]

    other_items = [aid for aid, name in items if aid not in potions and aid not in balls]
    if other_items:
        return other_items[0]

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
    if retreat and active and active.remaining_hp <= 40 and bench_count > 0:
        return retreat[0][0]

    # 11. End Turn
    if end_turn:
        return end_turn[0][0]

    return legal_actions[0]
