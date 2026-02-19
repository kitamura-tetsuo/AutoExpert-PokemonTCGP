import re
import random

def play(state, game):
    """
    Decides the best action for the current player.
    """
    legal_actions = game.legal_actions()

    if not legal_actions:
        return 0

    # Parse all actions
    parsed_actions = []
    for action_id in legal_actions:
        name = game.action_name(action_id)
        parsed_actions.append((action_id, name))

    current_player = state.current_player
    opponent = 1 - current_player

    active_pokemon = state.get_active_pokemon(current_player)
    bench_pokemon = state.get_bench_pokemon(current_player)

    opp_active = state.get_active_pokemon(opponent)
    opp_hp = opp_active.remaining_hp if opp_active else 0

    hand = state.get_hand(current_player)

    # --- CATEGORIZE ACTIONS ---
    setup_actions = [] # Place(..., 0)
    bench_actions = [] # Place(..., 1..3)
    attack_actions = [] # Attack(...)
    attach_energy_active = [] # Attach(Type, 0)
    attach_energy_bench = [] # Attach(Type, 1..3)
    evolve_actions = [] # Evolve(...)
    play_trainer_actions = [] # Play(...) (Trainer cards)
    ability_actions = [] # UseAbility(...) or similar? Need to verify.
    retreat_actions = [] # Retreat(...)
    end_turn_action = None

    for aid, name in parsed_actions:
        if name == "EndTurn":
            end_turn_action = aid
        elif name.startswith("Place(") and ", 0)" in name:
            setup_actions.append((aid, name))
        elif name.startswith("Place("):
            bench_actions.append((aid, name))
        elif name.startswith("Attack("):
            attack_actions.append((aid, name))
        elif name.startswith("Attach(") and ", 0)" in name:
            attach_energy_active.append((aid, name))
        elif name.startswith("Attach("):
            attach_energy_bench.append((aid, name))
        elif name.startswith("Evolve("):
            evolve_actions.append((aid, name))
        elif name.startswith("Play("):
            play_trainer_actions.append((aid, name))
        elif name.startswith("UseAbility("):
            ability_actions.append((aid, name))
        elif name.startswith("Retreat("):
            retreat_actions.append((aid, name))

    # --- STRATEGY ---

    # 1. Setup Phase: Prioritize Mewtwo ex (A1129MewtwoEx)
    if setup_actions:
        for aid, name in setup_actions:
            if "MewtwoEx" in name or "129" in name:
                return aid
        return setup_actions[0][0]

    # 2. Check for Lethal Attack
    if attack_actions and opp_active:
        for aid, name in attack_actions:
            match = re.search(r"Attack\((\d+)\)", name)
            if match:
                idx = int(match.group(1))
                if idx < len(active_pokemon.attacks):
                    damage = active_pokemon.attacks[idx].fixed_damage
                    if damage >= opp_hp:
                        return aid

    # 3. Evolution: Always evolve if possible
    if evolve_actions:
        # Prioritize evolving active
        for aid, name in evolve_actions:
            if ", 0)" in name:
                return aid
        return evolve_actions[0][0]

    # 4. Use Abilities (Psy Embrace, etc.)
    if ability_actions:
        # If we have Gardevoir/Kirlia ability available, use it.
        # Assuming ability is generally beneficial (energy attachment/draw)
        return ability_actions[0][0]

    # 5. Play Basic Pokemon to Bench
    if bench_actions:
        # If active is not Mewtwo, prioritize benching Mewtwo
        active_is_mewtwo = active_pokemon and "Mewtwo" in active_pokemon.name

        if not active_is_mewtwo:
             for aid, name in bench_actions:
                 if "Mewtwo" in name:
                     return aid

        # If active is Mewtwo, play Ralts for Gardevoir line
        if len(bench_pokemon) < 3:
             return bench_actions[0][0]

    # 6. Attach Energy
    # Check max energy needed for active
    if active_pokemon:
        current_energy = len(active_pokemon.attached_energy)
        max_cost = 0
        if hasattr(active_pokemon, "attacks"):
            for attack in active_pokemon.attacks:
                if hasattr(attack, "cost") and len(attack.cost) > max_cost:
                    max_cost = len(attack.cost)

        needs_energy = current_energy < max_cost

        if needs_energy and attach_energy_active:
            return attach_energy_active[0][0]

        # If active doesn't need energy, attach to bench Mewtwo or Ralts/Kirlia if needed
        if not needs_energy and attach_energy_bench:
             return attach_energy_bench[0][0]
        elif needs_energy and not attach_energy_active and attach_energy_bench:
            # Can't attach to active, attach to bench
            return attach_energy_bench[0][0]

    # 7. Play Trainers (Items/Supporters)
    if play_trainer_actions:
        # Prioritize drawing cards if hand is bad
        hand_size = len(hand)

        for aid, name in play_trainer_actions:
            if "Professor" in name or "Research" in name: # PA007ProfessorsResearch
                if hand_size <= 4:
                    return aid
            elif "Erika" in name: # Heal
                if active_pokemon and active_pokemon.remaining_hp < active_pokemon.total_hp:
                    return aid
            elif "Sabrina" in name:
                # Use Sabrina to disrupt
                 return aid
            elif "Potion" in name:
                 if active_pokemon and active_pokemon.remaining_hp < active_pokemon.total_hp:
                     return aid
                 for p in bench_pokemon:
                     if p.remaining_hp < p.total_hp:
                         return aid
            elif "Ball" in name: # Poke Ball
                return aid
            elif "Speed" in name: # X Speed
                return aid
            elif "RedCard" in name:
                 if state.get_hand_size(opponent) >= 4:
                     return aid
            elif "MythicalSlab" in name: # Tool?
                return aid
            elif "Giovanni" in name: # Supporter +10 dmg
                if attack_actions: # Use if attacking
                    return aid

    # 8. Retreat
    if retreat_actions and active_pokemon:
        # Retreat if active is low HP or weak active and bench has strong attacker
        is_weak_active = "Ralts" in active_pokemon.name or "Kirlia" in active_pokemon.name
        bench_has_mewtwo = any("Mewtwo" in p.name for p in bench_pokemon)

        if is_weak_active and bench_has_mewtwo:
             return retreat_actions[0][0]

        if active_pokemon.remaining_hp <= 30 and bench_pokemon:
             return retreat_actions[0][0]

    # 9. Attack (Best Damage)
    if attack_actions:
        best_dmg = -1
        best_aid = -1
        for aid, name in attack_actions:
            match = re.search(r"Attack\((\d+)\)", name)
            if match:
                idx = int(match.group(1))
                if idx < len(active_pokemon.attacks):
                    damage = active_pokemon.attacks[idx].fixed_damage
                    if damage > best_dmg:
                        best_dmg = damage
                        best_aid = aid

        if best_aid != -1:
            return best_aid

    # 10. End Turn
    if end_turn_action is not None:
        return end_turn_action

    # Fallback
    return random.choice(legal_actions)
