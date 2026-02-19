import re
import random

def play(state, game):
    """
    Decides the best action for the current player.
    """
    legal_actions = game.legal_actions()

    if not legal_actions:
        return 0

    parsed_actions = []
    for action_id in legal_actions:
        name = game.action_name(action_id)
        parsed_actions.append((action_id, name))

    current_player = state.current_player
    active_pokemon = state.get_active_pokemon(current_player)
    bench_pokemon = state.get_bench_pokemon(current_player)
    hand = state.get_hand(current_player)

    # Priority 0: Place Active (Must do this if no active)
    # Action: Place(Some(Card), 0)
    place_active_actions = [
        (aid, name) for aid, name in parsed_actions
        if name.startswith("Place(") and ", 0)" in name
    ]
    if place_active_actions:
        return place_active_actions[0][0]

    # Priority 1: Check for lethal (Win Game)
    # Action: Attack(index)
    attack_actions = [
        (aid, name) for aid, name in parsed_actions
        if name.startswith("Attack(")
    ]

    opponent = 1 - current_player
    opp_active = state.get_active_pokemon(opponent)
    opp_hp = opp_active.remaining_hp if opp_active else 0

    best_attack_id = None
    max_damage = -1

    if attack_actions and active_pokemon:
        for aid, name in attack_actions:
            match = re.search(r"Attack\((\d+)\)", name)
            if match:
                idx = int(match.group(1))
                if hasattr(active_pokemon, 'attacks') and idx < len(active_pokemon.attacks):
                    damage = 0
                    attack = active_pokemon.attacks[idx]
                    if hasattr(attack, 'damage'):
                        damage = attack.damage
                    elif hasattr(attack, 'fixed_damage'):
                        damage = attack.fixed_damage

                    if damage >= opp_hp and opp_hp > 0:
                        return aid # Lethal!

                    if damage > max_damage:
                        max_damage = damage
                        best_attack_id = aid

    # Priority 2: Evolve
    # Action: Evolve(Some(Card), pos)
    evolve_actions = [
        (aid, name) for aid, name in parsed_actions
        if name.startswith("Evolve(")
    ]
    if evolve_actions:
        return evolve_actions[0][0]

    # Priority 3: Attach Energy to Active (if needed)
    # Action: Attach(Type, pos)
    if active_pokemon:
        attached_energy_count = len(active_pokemon.attached_energy)

        # Check max energy requirement of attacks
        max_cost = 0
        if hasattr(active_pokemon, 'attacks'):
            for attack in active_pokemon.attacks:
                # attack.cost is likely a list or int.
                # From logs: 'cost', 'energy_required'.
                # Let's assume cost is a list of energy types.
                if hasattr(attack, 'cost'):
                    cost = 0
                    if isinstance(attack.cost, list):
                        cost = len(attack.cost)
                    elif isinstance(attack.cost, int):
                        cost = attack.cost
                    if cost > max_cost:
                        max_cost = cost

        if attached_energy_count < max_cost:
            # Action: Attach(Type, 0)
            attach_active = [
                (aid, name) for aid, name in parsed_actions
                if name.startswith("Attach(") and ", 0)" in name
            ]
            if attach_active:
                return attach_active[0][0]

    # Priority 4: Place Bench Pokemon (if meaningful)
    # Action: Place(Some(Card), pos) where pos > 0
    # Don't fill bench unnecessarily, but having 1-2 is good.
    occupied_bench_count = len([p for p in bench_pokemon if p is not None])
    if occupied_bench_count < 3:
         place_bench_actions = [
             (aid, name) for aid, name in parsed_actions
             if name.startswith("Place(") and ", 0)" not in name
         ]
         if place_bench_actions:
             return place_bench_actions[0][0]

    # Priority 5: Use Supporters / Items (Play)
    # Action: Play(Some(Card))
    play_actions = [
        (aid, name) for aid, name in parsed_actions
        if name.startswith("Play(")
    ]

    # Check for "Professor's Research" or similar draw cards
    for aid, name in play_actions:
        if "Professor" in name or "Research" in name or "Bill" in name or "Hau" in name:
            # Avoid using if hand is already big?
            # But normally we want to draw.
            return aid

    # Priority 6: Use Ability
    # Action: UseAbility(index)
    ability_actions = [
        (aid, name) for aid, name in parsed_actions
        if name.startswith("UseAbility(")
    ]
    if ability_actions:
        return ability_actions[0][0]

    # Priority 7: Attach Energy to Bench (if active full or can't attach to active)
    attach_bench = [
        (aid, name) for aid, name in parsed_actions
        if name.startswith("Attach(") and ", 0)" not in name
    ]
    if attach_bench:
        return attach_bench[0][0]

    # Priority 8: Use other items (Potion, Speed, etc)
    for aid, name in play_actions:
        if "Potion" in name:
             if active_pokemon and active_pokemon.remaining_hp < 100:
                 return aid
        if "Speed" in name: # X Speed
             return aid
        if "Ball" in name: # Poke Ball
             if occupied_bench_count < 3:
                 return aid
        if "Slab" in name: # Mythical Slab
             return aid

    # Priority 9: Attach Energy to Active (Overcharge - usually good for retreat or effects)
    attach_active_any = [
        (aid, name) for aid, name in parsed_actions
        if name.startswith("Attach(") and ", 0)" in name
    ]
    if attach_active_any:
        return attach_active_any[0][0]

    # Priority 10: Attack (Best damage)
    if best_attack_id is not None:
        return best_attack_id
    elif attack_actions:
        return attack_actions[0][0]

    # Priority 11: End Turn
    end_turn_actions = [
        (aid, name) for aid, name in parsed_actions
        if name == "EndTurn"
    ]
    if end_turn_actions:
        return end_turn_actions[0][0]

    # Fallback
    return legal_actions[0]
