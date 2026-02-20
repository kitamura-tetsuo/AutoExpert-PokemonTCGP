import re
import math

def play(state, game):
    """
    Decides the best action for the current player using optimized heuristics.
    """
    legal_actions = game.legal_actions()
    if not legal_actions:
        return 0

    # --- 1. Helper Functions ---
    def get_card_details(card):
        if not card:
            return None
        return {
            "name": getattr(card, "name", ""),
            "hp": getattr(card, "remaining_hp", 0),
            "max_hp": getattr(card, "total_hp", 0),
            "energy": getattr(card, "attached_energy", []),
            "attacks": getattr(card, "attacks", [])
        }

    def get_card_type(card_details):
        if not card_details: return "Colorless"
        name = card_details["name"].lower()
        if any(x in name for x in ["pikachu", "zapdos", "raichu", "magneton", "electrode", "electabuzz", "jolteon", "blitzle", "zebstrika", "pincurchin"]): return "Lightning"
        if any(x in name for x in ["mewtwo", "ralts", "kirlia", "gardevoir", "gengar", "haunter", "gastly", "abra", "kadabra", "alakazam", "jynx", "mr. mime"]): return "Psychic"
        if any(x in name for x in ["starmie", "articuno", "blastoise", "lapras", "gyarados", "vaporeon", "golduck", "psyduck", "poliwag", "poliwhirl", "poliwrath", "seadra", "horsea"]): return "Water"
        if any(x in name for x in ["charizard", "moltres", "arcanine", "ninetales", "rapidash", "magmar", "flareon"]): return "Fire"
        if any(x in name for x in ["venusaur", "exeggutor", "victreebel", "vileplume", "butterfree", "beedrill", "scyther", "pinsir", "tangela"]): return "Grass"
        if any(x in name for x in ["machamp", "hitmonlee", "hitmonchan", "golem", "onix", "rhydon", "marowak", "dugtrio", "sandslash"]): return "Fighting"
        if any(x in name for x in ["darkrai", "weavile", "arbok", "muk", "weezing"]): return "Darkness"
        if any(x in name for x in ["dragonite"]): return "Dragon"
        if any(x in name for x in ["melmetal"]): return "Metal"
        return "Colorless"

    def calculate_damage(card_details, attack_idx, my_bench_details):
        if not card_details or attack_idx >= len(card_details["attacks"]):
            return 0
        atk = card_details["attacks"][attack_idx]
        base_dmg = getattr(atk, "fixed_damage", 0)

        card_name = card_details["name"]
        atk_name = getattr(atk, "name", "")

        if "Pikachu ex" in card_name and "Circle Circuit" in atk_name:
            lightning_count = 0
            for b in my_bench_details:
                if b and "Lightning" in get_card_type(b):
                    lightning_count += 1
            return 30 * lightning_count

        if "Mewtwo ex" in card_name and "Psydrive" in atk_name:
             return 150

        if "Articuno ex" in card_name and "Blizzard" in atk_name:
             return 80

        if "Starmie ex" in card_name and "Hydro Splash" in atk_name:
            return 90

        return base_dmg

    def get_energy_deficit(current_energy, attack_cost):
        current_counts = {}
        for e in current_energy:
            s = str(e)
            current_counts[s] = current_counts.get(s, 0) + 1

        specific_needed = {}
        colorless_cost = 0

        temp_counts = current_counts.copy()

        for c in attack_cost:
            s = str(c)
            if s == "Colorless":
                colorless_cost += 1
                continue

            if temp_counts.get(s, 0) > 0:
                temp_counts[s] -= 1
            else:
                specific_needed[s] = specific_needed.get(s, 0) + 1

        remaining_energy = sum(temp_counts.values())
        colorless_needed = max(0, colorless_cost - remaining_energy)

        return specific_needed, colorless_needed

    def get_best_attack_cost(card_details):
        if not card_details or not card_details["attacks"]:
            return []

        best_cost = []
        max_len = -1

        for atk in card_details["attacks"]:
            cost = getattr(atk, "cost", [])
            dmg = getattr(atk, "fixed_damage", 0)
            if "Psydrive" in getattr(atk, "name", ""): dmg = 150
            if "Circle Circuit" in getattr(atk, "name", ""): dmg = 120

            if dmg > 0:
                if len(cost) > max_len:
                    max_len = len(cost)
                    best_cost = cost
            elif not best_cost:
                 best_cost = cost

        return best_cost

    # --- 2. State Parsing ---
    current_player = state.current_player
    opponent = 1 - current_player

    my_active_card = state.get_active_pokemon(current_player)
    my_bench_cards = state.get_bench_pokemon(current_player)

    my_active = get_card_details(my_active_card)
    my_bench = [get_card_details(c) for c in my_bench_cards]

    opp_active_card = state.get_active_pokemon(opponent)
    opp_bench_cards = state.get_bench_pokemon(opponent)
    opp_active = get_card_details(opp_active_card)
    opp_bench = [get_card_details(c) for c in opp_bench_cards]

    my_hand = state.get_hand(current_player)
    my_hand_size = len(my_hand)

    try:
        opp_hand_size = len(state.get_hand(opponent))
    except:
        opp_hand_size = 0

    actions = {
        "attack": [], "attach": [], "attach_tool": [], "evolve": [],
        "place_active": [], "place_bench": [], "play_item": [],
        "play_supporter": [], "ability": [], "retreat": [],
        "activate": [], "end_turn": []
    }

    for aid in legal_actions:
        name = game.action_name(aid)

        if name.startswith("Attack("):
            m = re.search(r"Attack\((\d+)\)", name)
            if m: actions["attack"].append((aid, int(m.group(1))))

        elif name.startswith("AttachTool"):
            m = re.search(r"AttachTool\((?:Some\()?(.*?)\)?, (\d+)\)", name)
            if m: actions["attach_tool"].append((aid, m.group(1), int(m.group(2))))

        elif name.startswith("Attach"):
            if "Tool" in name: continue
            m = re.search(r"Attach\((?:Some\()?(.*?)\)?, (\d+)\)", name)
            if m:
                actions["attach"].append((aid, m.group(1).replace(")", ""), int(m.group(2))))
            else:
                m = re.search(r"AttachEnergy\((\d+), (.*?)\)", name)
                if m: actions["attach"].append((aid, m.group(2), int(m.group(1))))

        elif name.startswith("Evolve("):
             m = re.search(r"Evolve\((?:Some\()?(.*?)\)?, (\d+)\)", name)
             target_pos = int(m.group(2)) if m else -1
             actions["evolve"].append((aid, target_pos))

        elif name.startswith("Place("):
            m = re.search(r"Place\((?:Some\()?(.*?)\)?, (\d+)\)", name)
            if m:
                card_name = m.group(1)
                pos = int(m.group(2))
                if pos == 0: actions["place_active"].append((aid, card_name))
                else: actions["place_bench"].append((aid, card_name))

        elif name.startswith("PlayPokemon("):
             if ", 0)" in name: actions["place_active"].append((aid, name))
             else: actions["place_bench"].append((aid, name))

        elif name.startswith("Play(") or name.startswith("UseItem") or name.startswith("UseSupporter"):
            card_name = name
            target = -1
            m = re.search(r"Play\((?:Some\()?(.*?)\)?(?:, (\d+))\)", name)
            if m:
                card_name = m.group(1)
                target = int(m.group(2))
            else:
                m = re.search(r"Play\((?:Some\()?(.*?)\)?\)", name)
                if m: card_name = m.group(1)

            supporters = ["Research", "Sabrina", "Giovanni", "Erika", "Misty", "Blaine", "Koga", "Lt. Surge", "Brock", "Copycat", "Lisia", "Cyrus", "Mars", "Red", "Guzma", "Judge", "Acerola", "Hau", "Bill"]
            if any(s in card_name for s in supporters):
                actions["play_supporter"].append((aid, card_name, target))
            else:
                actions["play_item"].append((aid, card_name, target))

        elif name.startswith("UseAbility("):
            actions["ability"].append((aid, name))

        elif name.startswith("Retreat"):
             actions["retreat"].append((aid, name))

        elif name.startswith("Activate("):
            m = re.search(r"Activate\((\d+)\)", name)
            if m: actions["activate"].append((aid, int(m.group(1))))

        elif name == "EndTurn":
            actions["end_turn"].append((aid,))

    # --- 3. Decision Logic ---

    # A. Lethal Attacks
    if actions["attack"] and opp_active:
        lethal = []
        for aid, idx in actions["attack"]:
            dmg = calculate_damage(my_active, idx, my_bench)
            if dmg >= opp_active["hp"]:
                lethal.append((aid, idx, dmg))

        if lethal:
            lethal.sort(key=lambda x: x[1])
            return lethal[0][0]

    # B. Activate (Switching)
    if actions["activate"]:
        if not my_active or my_active["hp"] == 0:
            best_aid = actions["activate"][0][0]
            max_score = -float('inf')
            for aid, idx in actions["activate"]:
                if idx < len(my_bench):
                    card = my_bench[idx]
                    if not card: continue
                    score = 0
                    score += len(card["energy"]) * 50
                    name_lower = card["name"].lower()
                    if "ex" in name_lower:
                        if "pikachu" in name_lower: score += 60
                        elif "starmie" in name_lower: score += 50
                        elif "mewtwo" in name_lower:
                            if len(card["energy"]) >= 2: score += 40
                            else: score -= 20
                        else: score += 30
                    elif "kangaskhan" in name_lower or "farfetch" in name_lower: score += 20
                    elif "articuno" in name_lower: score += 30
                    if "ralts" in name_lower or "kirlia" in name_lower: score -= 50
                    score += card["hp"]
                    if score > max_score:
                        max_score = score
                        best_aid = aid
            return best_aid
        else:
            # Sabrina effect on Opponent
            best_aid = actions["activate"][0][0]
            max_score = -float('inf')
            max_dmg = 0
            if actions["attack"]:
                max_dmg = max(calculate_damage(my_active, idx, my_bench) for _, idx in actions["attack"])

            for aid, idx in actions["activate"]:
                if idx < len(opp_bench):
                    card = opp_bench[idx]
                    if not card: continue
                    score = 0
                    if card["hp"] <= max_dmg: score += 1000
                    if "ex" in card["name"].lower() and card["hp"] < 60: score += 500
                    if len(card["energy"]) == 0: score += 100
                    if "ex" not in card["name"].lower(): score += 50
                    if score > max_score:
                        max_score = score
                        best_aid = aid
            return best_aid

    # C. Place Active
    if actions["place_active"]:
        def score_starter(name):
            n = name.lower()
            if "pikachu" in n and "ex" in n: return 100
            if "kangaskhan" in n: return 90
            if "farfetch" in n: return 85
            if "starmie" in n and "ex" in n: return 80
            if "articuno" in n and "ex" in n: return 80
            if "mewtwo" in n and "ex" in n: return 60
            if "ex" in n: return 70
            if "ralts" in n: return 10
            return 50
        best = max(actions["place_active"], key=lambda x: score_starter(x[1]))
        return best[0]

    # D. Evolution
    if actions["evolve"]:
        return actions["evolve"][0][0]

    # E. Bench Placement
    if actions["place_bench"]:
        is_pikachu_active = my_active and "Pikachu ex" in my_active["name"]
        if is_pikachu_active:
            return actions["place_bench"][0][0]

        current_bench_count = sum(1 for b in my_bench if b)
        if current_bench_count < 3:
            def score_bench(name):
                n = name.lower()
                s = 0
                if "ex" in n: s += 50
                if "pikachu" in n: s += 30
                if "zapdos" in n: s += 30
                if "ralts" in n: s += 40
                return s
            best = max(actions["place_bench"], key=lambda x: score_bench(x[1]))
            return best[0]

    # F. Supporters - Misty
    misty = [a for a in actions["play_supporter"] if "Misty" in a[1]]
    if misty:
        best_misty = None
        for aid, name, target in misty:
            card = None
            if target == 0: card = my_active
            elif target > 0 and (target-1) < len(my_bench): card = my_bench[target-1]
            if card:
                if "Water" in get_card_type(card):
                    best_cost = get_best_attack_cost(card)
                    spec, col = get_energy_deficit(card["energy"], best_cost)
                    if spec or col > 0:
                        best_misty = aid
                        if target == 0: break
        if best_misty: return best_misty

    # G. Energy Attachment
    if actions["attach"]:
        best_attach = None
        max_attach_score = -float('inf')

        candidates = []
        if my_active: candidates.append((0, my_active))
        for i, b in enumerate(my_bench):
            if b: candidates.append((i+1, b))

        for aid, etype, pos in actions["attach"]:
            target_card = None
            for p, c in candidates:
                if p == pos: target_card = c; break

            if not target_card: continue

            score = 0
            cost = get_best_attack_cost(target_card)
            spec_needed, col_needed = get_energy_deficit(target_card["energy"], cost)

            is_useful = False
            s_etype = str(etype)
            if spec_needed.get(s_etype, 0) > 0:
                is_useful = True
                score += 50
            elif col_needed > 0:
                is_useful = True
                score += 30

            if not is_useful:
                score -= 20

            if is_useful:
                if pos == 0:
                    score += 40
                    if my_active["hp"] < 40: score -= 60
                else:
                    if "ex" in target_card["name"].lower(): score += 30
                    if "mewtwo" in target_card["name"].lower(): score += 20
            else:
                # If useless, prefer Bench EX strongly over Active
                if "ex" in target_card["name"].lower() and pos != 0:
                    score += 60 # Bench EX gets +60, total 40. Active gets -20. Active EX gets -20.
                if pos == 0:
                    score -= 40 # Penalize useless on active even more

            if score > max_attach_score:
                max_attach_score = score
                best_attach = aid

        if best_attach:
            return best_attach

    # H. Items
    if actions["play_item"]:
        potions = [a for a in actions["play_item"] if "Potion" in a[1]]
        if potions and my_active and my_active["hp"] < my_active["max_hp"]:
            if my_active["hp"] <= 60: return potions[0][0]

        red_cards = [a for a in actions["play_item"] if "RedCard" in a[1]]
        if red_cards and opp_hand_size >= 4:
            return red_cards[0][0]

        others = [a for a in actions["play_item"] if "Ball" in a[1] or "Candy" in a[1]]
        if others: return others[0][0]

    # I. Retreat
    if actions["retreat"]:
        should_retreat = False

        # 1. Active is dead weight (0 energy) and we have a hitter ready
        # REMOVED AGGRESSIVE RETREAT

        # 2. Survival
        if my_active and my_active["hp"] <= 50:
            for b in my_bench:
                # Must be reasonably healthy and have some energy
                if b and len(b["energy"]) >= 2 and b["hp"] > 40:
                    should_retreat = True
                    break

        # 3. Swap for Lethal
        # If active cannot kill, but bench can
        if not should_retreat and my_active and opp_active:
             # Can active kill?
             active_lethal = False
             # Check if any attack is lethal (already checked in Step A, but maybe we didn't attack because we wanted to evolve/attach first?)
             # Actually Step A returns immediately if lethal.
             # So if we are here, Active CANNOT kill.

             # Check Bench
             for b in my_bench:
                 if not b: continue
                 # Need to check bench attacks.
                 # But we can't easily calculate damage for bench without swapping them active?
                 # Actually `calculate_damage` assumes active?
                 # No, `calculate_damage` takes `card_details`.
                 # So we can calculate.
                 # But bench pokemon attacks might have requirements (e.g. Energy).
                 # We need to check energy.
                 cost = get_best_attack_cost(b)
                 deficit, col = get_energy_deficit(b["energy"], cost)
                 if not deficit and col == 0:
                     # Charged. Check damage.
                     # Assuming attack 0 is best? Or iterate?
                     max_bench_dmg = 0
                     for i in range(len(b["attacks"])):
                         d = calculate_damage(b, i, my_bench) # my_bench logic for Pikachu might be slightly off if b moves to active (one less bench), but close enough.
                         if d > max_bench_dmg: max_bench_dmg = d

                     if max_bench_dmg >= opp_active["hp"]:
                         should_retreat = True
                         break

        if should_retreat:
             return actions["retreat"][0][0]

    # J. Supporters - Research
    research = [a for a in actions["play_supporter"] if "Research" in a[1]]
    if research:
        if my_hand_size <= 5:
            return research[0][0]

    # K. Supporters - Sabrina
    sabrina = [a for a in actions["play_supporter"] if "Sabrina" in a[1]]
    if sabrina:
        # Always play if opponent has bench (Disruption)
        opp_bench_count = sum(1 for b in opp_bench if b)
        if opp_bench_count > 0:
            return sabrina[0][0]

    # L. Attacks
    if actions["attack"]:
        best_atk = None
        max_dmg = -1
        for aid, idx in actions["attack"]:
            dmg = calculate_damage(my_active, idx, my_bench)
            atk_name = getattr(my_active["attacks"][idx], "name", "").lower()
            if "paralyze" in atk_name: dmg += 40
            if "sleep" in atk_name: dmg += 30
            if dmg > max_dmg:
                max_dmg = dmg
                best_atk = aid
        return best_atk

    # M. End Turn
    if actions["end_turn"]:
        return actions["end_turn"][0][0]

    return legal_actions[0]
