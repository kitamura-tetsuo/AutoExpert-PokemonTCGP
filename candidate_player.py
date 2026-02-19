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
    def get_attack_damage(attack_idx):
        if not active or not hasattr(active, 'attacks') or attack_idx >= len(active.attacks):
            return 0
        atk = active.attacks[attack_idx]
        dmg = getattr(atk, 'fixed_damage', 0)
        if dmg == 0:
            dmg = getattr(atk, 'damage', 0)
        return dmg

    # 2. Check for Lethal (Win Game)
    if attacks:
        max_dmg = -1
        best_lethal = None
        for aid, name in attacks:
            match = re.search(r"Attack\((\d+)\)", name)
            if match:
                idx = int(match.group(1))
                dmg = get_attack_damage(idx)
                if dmg > max_dmg:
                    max_dmg = dmg
                    best_lethal = aid

        if max_dmg >= opp_hp and opp_hp > 0:
            return best_lethal

    # 3. Evolution (High Priority)
    if evolutions:
        # Always evolve if possible
        return evolutions[0][0]

    # 4. Use "Free" Items (PokeBall, etc)
    balls = [a for a in play_card if "Ball" in a[1]]
    if balls:
        return balls[0][0]

    # 5. Attach Energy
    # Prioritize attaching energy before using supporters like Research which discard hand
    if attach_energy:
        # Check active needs
        active_needs = False
        max_cost = 0
        current_energy_count = 0

        if active and hasattr(active, 'attacks'):
            current_energy_count = len(active.attached_energy)
            for atk in active.attacks:
                cost = getattr(atk, 'cost', [])
                if isinstance(cost, list):
                    if len(cost) > max_cost:
                        max_cost = len(cost)
                elif isinstance(cost, int): # Fallback
                     if cost > max_cost:
                        max_cost = cost

            if current_energy_count < max_cost:
                active_needs = True

        attach_active_actions = [a for a in attach_energy if ", 0)" in a[1]]
        attach_bench_actions = [a for a in attach_energy if ", 0)" not in a[1]]

        if active_needs and attach_active_actions:
            return attach_active_actions[0][0]
        elif attach_bench_actions:
            # If active full, prefer bench
            return attach_bench_actions[0][0]
        elif attach_active_actions:
            # If no bench, attach to active
            return attach_active_actions[0][0]

    # 6. Supporters (Draw/Setup)
    # Professor's Research
    hand = state.get_hand(current_player)
    research = [a for a in play_card if "Research" in a[1]]
    if research:
        if len(hand) < 5:
            return research[0][0]

    # 7. More Supporters/Items
    # Potion
    potions = [a for a in play_card if "Potion" in a[1]]
    if potions and active and active.remaining_hp < active.total_hp:
        return potions[0][0]

    # Giovanni (if attacking)
    giovanni = [a for a in play_card if "Giovanni" in a[1]]
    if giovanni and attacks: # Only use if we can attack
        return giovanni[0][0]

    # Sabrina (Disrupt)
    sabrina = [a for a in play_card if "Sabrina" in a[1]]
    if sabrina:
        # Use if opponent active is NOT killable this turn
        can_kill = False
        if attacks:
             for aid, name in attacks:
                match = re.search(r"Attack\((\d+)\)", name)
                if match:
                    idx = int(match.group(1))
                    if get_attack_damage(idx) >= opp_hp:
                        can_kill = True
                        break
        if not can_kill:
            return sabrina[0][0]

    # Red Card (Disrupt hand)
    red_card = [a for a in play_card if "RedCard" in a[1]]
    if red_card:
        try:
            opp_hand = state.get_hand(opponent)
            if len(opp_hand) >= 4:
                return red_card[0][0]
        except:
            pass # Ignore if error

    # X Speed (Retreat assistance)
    x_speed = [a for a in play_card if "XSpeed" in a[1]]
    if x_speed and active and active.remaining_hp <= 40:
        return x_speed[0][0]

    # 8. Place Bench (Basics)
    if place_bench:
        bench_count = len([p for p in bench if p is not None])
        if bench_count < 3:
            return place_bench[0][0]

    # 9. Abilities
    if abilities:
        return abilities[0][0]

    # 10. Attack (Maximize Damage)
    if attacks:
        best_attack = None
        max_dmg = -1
        for aid, name in attacks:
            match = re.search(r"Attack\((\d+)\)", name)
            if match:
                idx = int(match.group(1))
                dmg = get_attack_damage(idx)
                if dmg > max_dmg:
                    max_dmg = dmg
                    best_attack = aid

        if best_attack:
            return best_attack
        return attacks[0][0]

    # 11. Retreat
    if retreat and active and active.remaining_hp <= 40:
        # Check if we have bench with energy?
        has_backup = False
        for p in bench:
            if p and len(p.attached_energy) > 0:
                has_backup = True
                break

        if has_backup:
            return retreat[0][0]

    # 12. End Turn
    if end_turn:
        return end_turn[0][0]

    # Fallback
    return legal_actions[0]
