import re
import random

def play(state, game):
    """
    Decides the best action for the current player.
    """
    legal_actions = game.legal_actions()
    if not legal_actions:
        return 0

    # 1. Parse Legal Actions
    actions = []
    for aid in legal_actions:
        name = game.action_name(aid)
        actions.append((aid, name))

    action_types = {
        "attack": [],
        "attach_active": [],
        "attach_bench": [],
        "evolve": [],
        "place_active": [],
        "place_bench": [],
        "play_item": [],
        "play_supporter": [],
        "ability": [],
        "retreat": [],
        "end_turn": []
    }

    for aid, name in actions:
        if name.startswith("Attack("):
            match = re.search(r"Attack\((\d+)\)", name)
            idx = int(match.group(1)) if match else 0
            action_types["attack"].append((aid, name, idx))
        elif name.startswith("Attach("):
            if ", 0)" in name:
                action_types["attach_active"].append((aid, name))
            else:
                action_types["attach_bench"].append((aid, name))
        elif name.startswith("Evolve("):
            action_types["evolve"].append((aid, name))
        elif name.startswith("Place("):
            if ", 0)" in name:
                action_types["place_active"].append((aid, name))
            else:
                action_types["place_bench"].append((aid, name))
        elif name.startswith("PlayPokemon("):
            action_types["place_bench"].append((aid, name))
        elif name.startswith("Play(") or name.startswith("Use"):
            if any(x in name for x in ["Research", "Sabrina", "Giovanni", "Erika", "Misty", "Blaine", "Koga"]):
                action_types["play_supporter"].append((aid, name))
            else:
                action_types["play_item"].append((aid, name))
        elif name.startswith("UseItem("):
             action_types["play_item"].append((aid, name))
        elif name.startswith("UseSupporter("):
             action_types["play_supporter"].append((aid, name))
        elif name.startswith("UseAbility("):
            action_types["ability"].append((aid, name))
        elif name == "EndTurn":
            action_types["end_turn"].append((aid, name))
        elif name.startswith("Retreat("):
            action_types["retreat"].append((aid, name))

    # 2. Analyze State
    current_player = state.current_player
    opponent = 1 - current_player

    my_active = state.get_active_pokemon(current_player)
    my_bench = state.get_bench_pokemon(current_player)
    my_hand = state.get_hand(current_player)

    opp_active = state.get_active_pokemon(opponent)
    opp_bench = state.get_bench_pokemon(opponent)
    opp_hand = state.get_hand(opponent)

    # Helpers
    def get_damage(card, attack_idx):
        if not card or not hasattr(card, 'attacks') or attack_idx >= len(card.attacks):
            return 0
        atk = card.attacks[attack_idx]
        dmg = getattr(atk, 'fixed_damage', 0)
        if dmg == 0:
            dmg = getattr(atk, 'damage', 0)
        return dmg

    def is_lethal(damage):
        if not opp_active: return False
        return damage >= opp_active.remaining_hp

    def get_missing_energy(card, attack_idx=None):
        if not card or not hasattr(card, 'attacks') or not card.attacks:
            return []

        target_attack = None
        if attack_idx is not None and attack_idx < len(card.attacks):
             target_attack = card.attacks[attack_idx]
        else:
            max_dmg = -1
            for atk in card.attacks:
                d = getattr(atk, 'fixed_damage', 0)
                if d >= max_dmg:
                    max_dmg = d
                    target_attack = atk

        if not target_attack:
            return []

        cost = getattr(target_attack, 'cost', [])
        attached = [str(e) for e in card.attached_energy]
        sorted_cost = sorted([str(c) for c in cost], key=lambda x: 1 if x == "Colorless" else 0)

        temp_attached = list(attached)
        missing = []
        for c_str in sorted_cost:
            found = False
            if c_str != "Colorless":
                if c_str in temp_attached:
                    temp_attached.remove(c_str)
                    found = True
            else:
                if temp_attached:
                    temp_attached.pop(0)
                    found = True
            if not found:
                missing.append(c_str)
        return missing

    # --- Strategy Execution ---

    # 0. Setup: Place Active
    if action_types["place_active"]:
        mewtwo = [a for a in action_types["place_active"] if "Mewtwo" in a[1]]
        if mewtwo: return mewtwo[0][0]
        return action_types["place_active"][0][0]

    # 1. Win Game (Lethal)
    best_attack_dmg = 0
    best_attack_id = None

    if action_types["attack"]:
        for aid, name, idx in action_types["attack"]:
            dmg = get_damage(my_active, idx)
            if is_lethal(dmg):
                return aid
            if dmg > best_attack_dmg:
                best_attack_dmg = dmg
                best_attack_id = aid

        if best_attack_id is None and action_types["attack"]:
             # If all attacks do 0 dmg or just uncalculated, pick first
             best_attack_id = action_types["attack"][0][0]

        # Check Giovanni + Attack
        giovanni = [a for a in action_types["play_supporter"] if "Giovanni" in a[1]]
        if giovanni:
            for aid, name, idx in action_types["attack"]:
                dmg = get_damage(my_active, idx)
                if is_lethal(dmg + 10):
                    return giovanni[0][0]

    # 2. Evolve
    if action_types["evolve"]:
        evolve_active = [a for a in action_types["evolve"] if ", 0)" in a[1]]
        if evolve_active: return evolve_active[0][0]
        return action_types["evolve"][0][0]

    # 3. Attach Energy
    if action_types["attach_active"] or action_types["attach_bench"]:
        active_missing = get_missing_energy(my_active)
        if active_missing:
            for aid, name in action_types["attach_active"]:
                match = re.search(r"Attach\((.+?), 0\)", name)
                if match:
                    etype = match.group(1)
                    if etype.startswith("Some("): etype = etype[5:-1]
                    if etype in active_missing or "Colorless" in active_missing:
                        return aid

        for i, b_card in enumerate(my_bench):
            if b_card:
                bench_missing = get_missing_energy(b_card)
                if bench_missing:
                    pos = i + 1
                    target_actions = [a for a in action_types["attach_bench"] if f", {pos})" in a[1]]
                    for aid, name in target_actions:
                         match = re.search(r"Attach\((.+?), " + str(pos) + r"\)", name)
                         if match:
                            etype = match.group(1)
                            if etype.startswith("Some("): etype = etype[5:-1]
                            if etype in bench_missing or "Colorless" in bench_missing:
                                return aid

        # Fallback: Attach to active (even if not strictly missing for BEST attack, maybe charges second best or just to have energy)
        if action_types["attach_active"]:
             return action_types["attach_active"][0][0]
        if action_types["attach_bench"]:
            return action_types["attach_bench"][0][0]

    # 4. Play Basics to Bench
    if action_types["place_bench"]:
        mewtwo = [a for a in action_types["place_bench"] if "Mewtwo" in a[1]]
        if mewtwo: return mewtwo[0][0]
        return action_types["place_bench"][0][0]

    # 5. Supporters
    if action_types["play_supporter"]:
        # Research
        research = [a for a in action_types["play_supporter"] if "Research" in a[1]]
        if research:
            # Conservative: only if hand is very small
            if len(my_hand) <= 2:
                return research[0][0]

        # Sabrina
        sabrina = [a for a in action_types["play_supporter"] if "Sabrina" in a[1]]
        if sabrina:
            # Use if opponent active is strong and I can't kill it
            # and they have bench to switch to.
            if opp_active and opp_active.remaining_hp > 80 and not is_lethal(best_attack_dmg):
                 if opp_bench and any(b is not None for b in opp_bench):
                     return sabrina[0][0]

        # Misty (Water acceleration?)
        misty = [a for a in action_types["play_supporter"] if "Misty" in a[1]]
        if misty: return misty[0][0]

        # Blaine/Koga/Erika... Generic use?
        # Maybe random if nothing else?
        pass

    # 6. Items
    if action_types["play_item"]:
        potion = [a for a in action_types["play_item"] if "Potion" in a[1]]
        if potion and my_active and my_active.remaining_hp < my_active.total_hp:
            return potion[0][0]

        red_card = [a for a in action_types["play_item"] if "RedCard" in a[1]]
        if red_card and len(opp_hand) >= 4:
            return red_card[0][0]

        search = [a for a in action_types["play_item"] if "Ball" in a[1] or "Computer" in a[1]]
        if search: return search[0][0]

        x_speed = [a for a in action_types["play_item"] if "XSpeed" in a[1]]
        if x_speed and my_active and my_active.remaining_hp < 60:
             return x_speed[0][0]

    # 7. Abilities
    if action_types["ability"]:
        return action_types["ability"][0][0]

    # 8. Attack
    if best_attack_id:
        return best_attack_id

    # 9. Retreat
    if action_types["retreat"]:
        if my_active and my_active.remaining_hp <= 40:
             has_backup = False
             for b in my_bench:
                 if b and b.attached_energy:
                     has_backup = True
                     break
             if has_backup:
                 return action_types["retreat"][0][0]

    # 10. End Turn
    if action_types["end_turn"]:
        return action_types["end_turn"][0][0]

    return legal_actions[0]
