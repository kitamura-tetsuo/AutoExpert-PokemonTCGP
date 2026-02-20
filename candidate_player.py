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
        return len(getattr(card, "attached_energy", [])) if card else 0

    def get_energy_type(card):
        if card and hasattr(card, "energy_type"):
            return str(card.energy_type)
        return "Colorless"

    def get_attack_damage(card, attack_idx, my_bench=None):
        if not card or not hasattr(card, "attacks") or attack_idx >= len(card.attacks):
            return 0
        atk = card.attacks[attack_idx]
        base_dmg = getattr(atk, "fixed_damage", 0)

        card_name = getattr(card, "name", "")
        atk_name = getattr(atk, "name", "")

        # Handle Pikachu ex "Circle Circuit"
        if "Pikachu ex" in card_name and "Circle Circuit" in atk_name:
            lightning_count = 0
            if my_bench:
                for b in my_bench:
                    if b and "Lightning" in get_energy_type(b):
                        lightning_count += 1
            return 30 * lightning_count

        # Handle Mewtwo ex "Psydrive"
        if "Mewtwo ex" in card_name and "Psydrive" in atk_name:
             return 150

        return base_dmg

    def get_energy_deficit(current_energy, cost):
        current_counts = {}
        for e in current_energy:
            s = str(e)
            current_counts[s] = current_counts.get(s, 0) + 1

        specific_needed = {}
        colorless_cost = 0

        # 1. Match specific types first
        temp_counts = current_counts.copy()

        for c in cost:
            s = str(c)
            if s == "Colorless":
                colorless_cost += 1
                continue

            if temp_counts.get(s, 0) > 0:
                temp_counts[s] -= 1
            else:
                specific_needed[s] = specific_needed.get(s, 0) + 1

        # 2. Check colorless
        remaining_energy = sum(temp_counts.values())
        colorless_needed = max(0, colorless_cost - remaining_energy)

        return specific_needed, colorless_needed

    def is_useful_energy(new_energy_type, current_energy, cost):
        specific_needed, colorless_needed = get_energy_deficit(current_energy, cost)

        s = str(new_energy_type)
        if specific_needed.get(s, 0) > 0:
            return True
        if colorless_needed > 0:
            return True
        return False

    def get_best_attack_cost(card):
        if not card or not hasattr(card, "attacks") or not card.attacks:
            return []

        # Prefer the cost of the strongest attack, or the most expensive one
        max_cost_len = -1
        best_cost = []
        for atk in card.attacks:
            cost = getattr(atk, "cost", [])
            if len(cost) > max_cost_len:
                max_cost_len = len(cost)
                best_cost = cost
        return best_cost

    def can_kill(damage, target_hp):
        return damage >= target_hp

    # --- 2. State Analysis ---
    current_player = state.current_player
    my_active = state.get_active_pokemon(current_player)
    my_bench = state.get_bench_pokemon(current_player)

    opponent = 1 - current_player
    opp_active = state.get_active_pokemon(opponent)
    opp_bench = state.get_bench_pokemon(opponent)

    opp_hp = get_hp(opp_active)
    my_hp = get_hp(my_active)
    my_max_hp = get_max_hp(my_active)

    try:
        opp_hand_size = len(state.get_hand(opponent))
    except:
        opp_hand_size = 0

    my_hand = state.get_hand(current_player)
    my_hand_size = len(my_hand)

    # --- 3. Parse Actions ---
    parsed_actions = {
        "attack": [], "attach": [], "attach_tool": [], "evolve": [], "place_active": [], "place_bench": [],
        "play_item": [], "play_supporter": [], "ability": [], "retreat": [], "activate": [], "end_turn": []
    }

    for aid in legal_actions:
        name = game.action_name(aid)

        # Helper to simplify parsing
        if name.startswith("Attack("):
            match = re.search(r"Attack\((\d+)\)", name)
            if match:
                idx = int(match.group(1))
                dmg = get_attack_damage(my_active, idx, my_bench)
                parsed_actions["attack"].append((aid, idx, dmg))

        elif name.startswith("AttachTool"):
             match = re.search(r"AttachTool\((?:Some\()?(.*?)\)?, (\d+)\)", name)
             if match:
                 parsed_actions["attach_tool"].append((aid, match.group(1), int(match.group(2))))

        elif name.startswith("Attach"):
            if "Tool" in name: continue
            match = re.search(r"Attach\((?:Some\()?(.*?)\)?, (\d+)\)", name)
            if match:
                etype = match.group(1).replace(")", "")
                pos = int(match.group(2))
                parsed_actions["attach"].append((aid, etype, pos))
            else:
                 match = re.search(r"AttachEnergy\((\d+), (.*?)\)", name)
                 if match:
                     pos = int(match.group(1))
                     etype = match.group(2)
                     parsed_actions["attach"].append((aid, etype, pos))
                 else:
                     parts = name[7:-1].split(", ")
                     if len(parts) == 2:
                         etype = parts[0]
                         try:
                             pos = int(parts[1])
                             parsed_actions["attach"].append((aid, etype, pos))
                         except:
                             pass

        elif name.startswith("Evolve("):
             parsed_actions["evolve"].append((aid, name))

        elif name.startswith("Place("):
            if ", 0)" in name:
                parsed_actions["place_active"].append((aid, name))
            else:
                parsed_actions["place_bench"].append((aid, name))

        elif name.startswith("PlayPokemon("):
             if ", 0)" in name:
                parsed_actions["place_active"].append((aid, name))
             else:
                parsed_actions["place_bench"].append((aid, name))

        elif name.startswith("Play(") or name.startswith("UseItem") or name.startswith("UseSupporter"):
            card_name = name
            target = -1
            # Try to parse with target
            match = re.search(r"Play\((?:Some\()?(.*?)\)?(?:, (\d+))\)", name)
            if match:
                card_name = match.group(1)
                target = int(match.group(2))
            else:
                match = re.search(r"Play\((?:Some\()?(.*?)\)?\)", name)
                if match:
                    card_name = match.group(1)

            supporters = ["Research", "Sabrina", "Giovanni", "Erika", "Misty", "Blaine", "Koga", "Lt. Surge", "Brock", "Copycat", "Lisia", "Cyrus", "Mars", "Red", "Guzma", "Judge", "Acerola", "Hau", "Bill"]
            if any(s in card_name for s in supporters):
                parsed_actions["play_supporter"].append((aid, card_name, target))
            else:
                parsed_actions["play_item"].append((aid, card_name, target))

        elif name.startswith("UseAbility("):
            match = re.search(r"UseAbility\((\d+)\)", name)
            idx = int(match.group(1)) if match else 0
            parsed_actions["ability"].append((aid, idx))

        elif name.startswith("Retreat("):
            match = re.search(r"Retreat\((\d+)\)", name)
            idx = int(match.group(1)) if match else 0
            parsed_actions["retreat"].append((aid, idx))
        elif name == "Retreat":
            parsed_actions["retreat"].append((aid, -1))

        elif name.startswith("Activate("):
            match = re.search(r"Activate\((\d+)\)", name)
            idx = int(match.group(1)) if match else 0
            parsed_actions["activate"].append((aid, idx))

        elif name == "EndTurn":
            parsed_actions["end_turn"].append((aid,))

    # --- 4. Decision Logic ---

    # A. Lethal Check
    if parsed_actions["attack"]:
        lethal_attacks = []
        for aid, idx, dmg in parsed_actions["attack"]:
            if can_kill(dmg, opp_hp):
                lethal_attacks.append((aid, idx, dmg))

        if lethal_attacks:
            lethal_attacks.sort(key=lambda x: x[1])
            return lethal_attacks[0][0]

    # B. Activate (Switching Logic)
    if parsed_actions["activate"]:
        # Case 1: My Active is KO'd (Zombie with 0 HP), need to promote from bench
        if not my_active or get_hp(my_active) == 0:
            best_aid = parsed_actions["activate"][0][0]
            max_score = -float('inf')

            for aid, idx in parsed_actions["activate"]:
                score = 0
                if idx < len(my_bench):
                    card = my_bench[idx]
                    if card:
                        # Prefer powered up Pokemon
                        score += count_energy(card) * 50

                        # Prefer "Fast" EX
                        name = getattr(card, "name", "").lower()
                        if "pikachu" in name and "ex" in name: score += 40
                        if "starmie" in name and "ex" in name: score += 40
                        if "articuno" in name and "ex" in name: score += 30

                        # Avoid promoting support/slow Pokemon if not ready
                        if "mewtwo" in name and count_energy(card) < 2: score -= 20

                        score += get_hp(card) # Prefer high HP

                if score > max_score:
                    max_score = score
                    best_aid = aid
            return best_aid

        # Case 2: Sabrina/Switch effect on Opponent
        else:
            # We are forcing opponent to switch.
            max_dmg = 0
            if parsed_actions["attack"]:
                max_dmg = max(a[2] for a in parsed_actions["attack"])

            # 1. Look for killable targets
            for aid, idx in parsed_actions["activate"]:
                if idx < len(opp_bench):
                    card = opp_bench[idx]
                    if card:
                        hp = get_hp(card)
                        if hp <= max_dmg:
                            return aid

            # 2. Look for stall targets
            best_stall_aid = None
            max_stall_score = -1
            for aid, idx in parsed_actions["activate"]:
                if idx < len(opp_bench):
                    card = opp_bench[idx]
                    if card:
                        score = 0
                        if count_energy(card) == 0: score += 100
                        if get_hp(card) < 60: score += 50

                        if "ex" in getattr(card, "name", "").lower() and count_energy(card) >= 2:
                            score = -100

                        if score > max_stall_score:
                            max_stall_score = score
                            best_stall_aid = aid

            if best_stall_aid and max_stall_score > 0: return best_stall_aid
            return parsed_actions["activate"][0][0]

    # C. Setup Active (Start of Game)
    if parsed_actions["place_active"]:
        def score_active(name):
            s = 0
            name_lower = name.lower()
            if "pikachu" in name_lower and "ex" in name_lower: return 1000
            if "starmie" in name_lower and "ex" in name_lower: return 900
            if "articuno" in name_lower and "ex" in name_lower: return 850
            if "kangaskhan" in name_lower: return 600
            if "farfetch" in name_lower: return 500
            if "mewtwo" in name_lower and "ex" in name_lower: return 400
            if "ex" in name_lower: return 300
            return 100

        best = max(parsed_actions["place_active"], key=lambda x: score_active(x[1]))
        return best[0]

    # D. Evolution
    if parsed_actions["evolve"]:
        return parsed_actions["evolve"][0][0]

    # E. Bench Placement
    if parsed_actions["place_bench"]:
        def score_bench(name):
            s = 0
            name_lower = name.lower()
            if "ex" in name_lower: s += 100
            if "mewtwo" in name_lower: s += 50
            if "pikachu" in name_lower: s += 50
            if "articuno" in name_lower: s += 50
            if "moltres" in name_lower: s += 50
            if "zapdos" in name_lower: s += 50
            if "starmie" in name_lower: s += 50
            if "ralts" in name_lower: s += 80
            return s
        best = max(parsed_actions["place_bench"], key=lambda x: score_bench(x[1]))
        return best[0]

    # F. Supporters
    # 1. Misty - Acceleration (High Priority)
    misty = [a for a in parsed_actions["play_supporter"] if "Misty" in a[1]]
    if misty:
        # Prioritize Active
        for aid, name, target in misty:
            if target == 0: return aid
        return misty[0][0]

    # 2. Draw/Search Supporters
    draw_supporters = []
    for aid, name, target in parsed_actions["play_supporter"]:
        if "Research" in name: draw_supporters.append((aid, name, 10))
        elif "Copycat" in name: draw_supporters.append((aid, name, 9))
        elif "Bill" in name: draw_supporters.append((aid, name, 8))
        elif "Hau" in name: draw_supporters.append((aid, name, 8))
        elif "Clemont" in name: draw_supporters.append((aid, name, 8))
        elif "Mars" in name: draw_supporters.append((aid, name, 8))
        elif "Red" in name: draw_supporters.append((aid, name, 8))
        elif "Judge" in name: draw_supporters.append((aid, name, 8))
        elif "Guzma" in name: draw_supporters.append((aid, name, 8))

    draw_supporters.sort(key=lambda x: x[2], reverse=True)

    bench_count = sum(1 for b in my_bench if b)

    for aid, name, score in draw_supporters:
        should_play = False

        # Always play if bench < 3 (Need setup) or hand is small
        if bench_count < 3 or my_hand_size < 5: should_play = True

        # Specific Logic
        if "Copycat" in name:
            if opp_hand_size > my_hand_size: should_play = True
        if "Clemont" in name:
            if count_energy(my_active) < 2: should_play = True

        if should_play: return aid

    # 3. Giovanni (Damage) - Only if it matters
    giovanni = [a for a in parsed_actions["play_supporter"] if "Giovanni" in a[1]]
    if giovanni and parsed_actions["attack"]:
        useful_giovanni = False
        for aid, idx, dmg in parsed_actions["attack"]:
            if not can_kill(dmg, opp_hp) and can_kill(dmg + 10, opp_hp):
                useful_giovanni = True
                break
        if useful_giovanni:
            return giovanni[0][0]

    # 4. Sabrina (Disruption)
    sabrina = [a for a in parsed_actions["play_supporter"] if "Sabrina" in a[1]]
    if sabrina:
        can_kill_active = any(can_kill(a[2], opp_hp) for a in parsed_actions["attack"])
        should_use_sabrina = False
        if not can_kill_active:
            my_max_dmg = max([a[2] for a in parsed_actions["attack"]]) if parsed_actions["attack"] else 0
            for b in opp_bench:
                if b and get_hp(b) <= my_max_dmg:
                    should_use_sabrina = True
                    break
            if not should_use_sabrina and opp_hp > 60 and count_energy(opp_active) >= 2:
                 if any(b and count_energy(b) == 0 for b in opp_bench):
                     should_use_sabrina = True
        if should_use_sabrina: return sabrina[0][0]

    # G. Abilities
    if parsed_actions["ability"]:
        return parsed_actions["ability"][0][0]

    # H. Items
    if parsed_actions["play_item"]:
        potion = [a for a in parsed_actions["play_item"] if "Potion" in a[1]]
        if potion and my_active and my_hp < my_max_hp:
             if my_hp <= 80: return potion[0][0]

        red_card = [a for a in parsed_actions["play_item"] if "RedCard" in a[1]]
        if red_card and opp_hand_size >= 4: return red_card[0][0]

        balls = [a for a in parsed_actions["play_item"] if "Ball" in a[1]]
        if balls: return balls[0][0]

        candy = [a for a in parsed_actions["play_item"] if "RareCandy" in a[1]]
        if candy: return candy[0][0]

    # I. Tool Attachment (New)
    if parsed_actions["attach_tool"]:
        # Prioritize Active
        for aid, name, pos in parsed_actions["attach_tool"]:
            if pos == 0: return aid
        return parsed_actions["attach_tool"][0][0]

    # J. Energy Attachment
    if parsed_actions["attach"]:
        candidates = []
        if my_active: candidates.append((0, my_active))
        for i, b in enumerate(my_bench):
            if b: candidates.append((i + 1, b))

        best_attach = None
        best_attach_score = -float('inf')

        for aid, etype, pos in parsed_actions["attach"]:
            target_card = None
            for p, c in candidates:
                if p == pos: target_card = c; break
            if not target_card: continue

            score = 0
            name = getattr(target_card, "name", "").lower()
            cost = get_best_attack_cost(target_card)
            attached = getattr(target_card, "attached_energy", [])

            if not is_useful_energy(etype, attached, cost): score = -1000
            else:
                score += 10
                if "ex" in name: score += 20
                if "mewtwo" in name: score += 15
                if "pikachu" in name: score += 15
                if "starmie" in name: score += 15
                new_attached = attached + [etype]
                spec, col = get_energy_deficit(new_attached, cost)
                if not spec and col == 0: score += 50
                if pos == 0:
                    if my_hp < 40: score -= 30
                    if count_energy(target_card) < 2: score += 5
                    # Bonus for enabling attack on healthy active
                    if not spec and col == 0 and my_hp >= 60: score += 20
                else:
                    score += 5

            if score > best_attach_score:
                best_attach_score = score
                best_attach = aid

        if best_attach and best_attach_score > -100: return best_attach
        return parsed_actions["attach"][0][0]

    # K. Retreat Logic
    if parsed_actions["retreat"]:
        should_retreat = False
        if my_active and my_hp <= 50:
             has_backup = False
             for card in my_bench:
                 if card and count_energy(card) >= 2 and get_hp(card) > 50:
                     has_backup = True
                     break
             if has_backup: should_retreat = True

        best_bench_idx = -1
        if not should_retreat and my_active and parsed_actions["attack"]:
             current_dmg = max([x[2] for x in parsed_actions["attack"]])
             if current_dmg < 40:
                 max_bench_dmg = 0
                 for i, card in enumerate(my_bench):
                     if card and count_energy(card) >= 2:
                         card_dmg = 0
                         for idx in range(len(getattr(card, "attacks", []))):
                             d = get_attack_damage(card, idx, my_bench)
                             if d > card_dmg: card_dmg = d
                         if card_dmg > max_bench_dmg:
                             max_bench_dmg = card_dmg
                             best_bench_idx = i
                 if max_bench_dmg > current_dmg + 30: should_retreat = True

        if should_retreat: return parsed_actions["retreat"][0][0]

    # L. Attack (Non-Lethal)
    if parsed_actions["attack"]:
        def score_attack(attack_tuple):
            aid, idx, dmg = attack_tuple
            score = dmg
            try:
                atk = my_active.attacks[idx]
                name = getattr(atk, "name", "").lower()
                if "paralyze" in name or "sleep" in name or "hypno" in name or "thunder wave" in name:
                    score += 50
                if "confuse" in name or "poison" in name or "burn" in name:
                    score += 20
            except: pass
            return score

        best_attack = max(parsed_actions["attack"], key=score_attack)
        return best_attack[0]

    # M. Play remaining Supporters (Safe Fallback)
    if parsed_actions["play_supporter"]:
        safe_names = ["Research", "Copycat", "Bill", "Hau", "Clemont", "Misty", "Lisia", "Erika", "Blaine", "Koga", "Lt. Surge", "Brock", "Mars", "Red", "Judge", "Acerola"]
        for aid, name, target in parsed_actions["play_supporter"]:
            if any(s in name for s in safe_names):
                return aid

    # N. End Turn
    if parsed_actions["end_turn"]:
        return parsed_actions["end_turn"][0][0]

    return legal_actions[0]
