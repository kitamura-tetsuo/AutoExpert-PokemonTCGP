import re

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

    # Priority 1: Setup (Place Active)
    # Check for "Place" action at position 0 (e.g. "Place(Some(A1001Bulbasaur), 0)")
    place_active_actions = [
        (aid, name) for aid, name in parsed_actions
        if name.startswith("Place(") and ", 0)" in name
    ]
    if place_active_actions:
        # Pick the first one.
        return place_active_actions[0][0]

    current_player = state.current_player

    # Get active pokemon
    active_pokemon = state.get_active_pokemon(current_player)

    # Priority 2: Win the game (Attack)
    attack_actions = [
        (aid, name) for aid, name in parsed_actions
        if name.startswith("Attack(")
    ]

    best_attack_id = None
    best_attack_damage = -1

    if attack_actions and active_pokemon:
        opponent = 1 - current_player
        opp_active = state.get_active_pokemon(opponent)
        opp_hp = opp_active.remaining_hp if opp_active else 0

        for aid, name in attack_actions:
            match = re.search(r"Attack\((\d+)\)", name)
            if match:
                idx = int(match.group(1))
                if idx < len(active_pokemon.attacks):
                    damage = active_pokemon.attacks[idx].fixed_damage
                    if damage >= opp_hp and opp_hp > 0:
                        return aid # Win!
                    if damage > best_attack_damage:
                        best_attack_damage = damage
                        best_attack_id = aid

    # Priority 3: Attach Energy to Active
    # Check if active needs energy.
    if active_pokemon:
        attached_energy_count = len(active_pokemon.attached_energy)

        # Check max energy requirement of attacks
        max_cost = 0
        for attack in active_pokemon.attacks:
            cost = len(attack.cost)
            if cost > max_cost:
                max_cost = cost

        if attached_energy_count < max_cost:
            # Look for AttachEnergy(0, ...)
            attach_actions = [
                (aid, name) for aid, name in parsed_actions
                if name.startswith("AttachEnergy(0,")
            ]
            if attach_actions:
                return attach_actions[0][0]

    # Priority 4: Evolve
    evolve_actions = [
        (aid, name) for aid, name in parsed_actions
        if name.startswith("Evolve(")
    ]
    if evolve_actions:
        return evolve_actions[0][0]

    # Priority 5: Play Pokemon to Bench
    play_pokemon_actions = [
        (aid, name) for aid, name in parsed_actions
        if name.startswith("PlayPokemon(")
    ]
    if play_pokemon_actions:
        return play_pokemon_actions[0][0]

    # Priority 6: Use Supporters (Professor's Research)
    supporter_actions = [
        (aid, name) for aid, name in parsed_actions
        if name.startswith("UseSupporter(")
    ]
    if supporter_actions:
        hand = state.get_hand(current_player)
        for aid, name in supporter_actions:
             match = re.search(r"UseSupporter\((\d+)\)", name)
             if match:
                 idx = int(match.group(1))
                 if idx < len(hand):
                     card = hand[idx]
                     if "Professor's Research" in card.name:
                         return aid

    # Priority 7: Attack (if not winning, but good damage)
    if best_attack_id is not None:
        return best_attack_id
    elif attack_actions:
        return attack_actions[0][0]

    # Priority 8: End Turn
    end_turn_actions = [
        (aid, name) for aid, name in parsed_actions
        if name == "EndTurn"
    ]
    if end_turn_actions:
        return end_turn_actions[0][0]

    # Fallback: Pick random legal action
    return legal_actions[0]
