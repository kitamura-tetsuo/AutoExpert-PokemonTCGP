import re
import math
import traceback
import sys

def play(state, game):
    """
    Decides the best action for the current player using optimized heuristics.
    """
    legal_actions = game.legal_actions()
    if not legal_actions:
        return 0

    try:
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
            name = card_details.get("name", "") if isinstance(card_details, dict) else getattr(card_details, "name", "")
            name = name.lower()

            # Energy Cards
            if "lightning energy" in name: return "Lightning"
            if "psychic energy" in name: return "Psychic"
            if "water energy" in name: return "Water"
            if "fire energy" in name: return "Fire"
            if "grass energy" in name: return "Grass"
            if "fighting energy" in name: return "Fighting"
            if "darkness energy" in name: return "Darkness"
            if "metal energy" in name: return "Metal"

            # Pokemon
            if any(x in name for x in ["pikachu", "zapdos", "raichu", "magneton", "electrode", "electabuzz", "jolteon", "blitzle", "zebstrika", "pincurchin", "mareep", "flaaffy", "ampharos", "helioptile", "heliolisk", "tynamo", "eelektrik", "eelektross"]): return "Lightning"
            if any(x in name for x in ["mewtwo", "ralts", "kirlia", "gardevoir", "gengar", "haunter", "gastly", "abra", "kadabra", "alakazam", "jynx", "mr. mime", "nidoran", "nidorina", "nidoqueen", "nidorino", "nidoking", "koffing", "weezing"]): return "Psychic"
            if any(x in name for x in ["starmie", "articuno", "blastoise", "lapras", "gyarados", "vaporeon", "golduck", "psyduck", "poliwag", "poliwhirl", "poliwrath", "seadra", "horsea", "squirtle", "wartortle", "tentacool", "tentacruel", "shellder", "cloyster", "krabby", "kingler", "goldeen", "seaking", "staryu", "magikarp"]): return "Water"
            if any(x in name for x in ["charizard", "moltres", "arcanine", "ninetales", "rapidash", "magmar", "flareon", "charmander", "charmeleon", "vulpix", "growlithe", "ponyta"]): return "Fire"
            if any(x in name for x in ["venusaur", "exeggutor", "victreebel", "vileplume", "butterfree", "beedrill", "scyther", "pinsir", "tangela", "bulbasaur", "ivysaur", "caterpie", "metapod", "weedle", "kakuna", "oddish", "gloom", "paras", "parasect", "venonat", "venomoth", "bellsprout", "weepinbell", "exeggcute"]): return "Grass"
            if any(x in name for x in ["machamp", "hitmonlee", "hitmonchan", "golem", "onix", "rhydon", "marowak", "dugtrio", "sandslash", "geodude", "graveler", "sandshrew", "diglett", "mankey", "primeape", "machop", "machoke", "cubone", "rhyhorn", "kabuto", "kabutops", "aerodactyl"]): return "Fighting"
            if any(x in name for x in ["darkrai", "weavile", "arbok", "muk", "weezing", "ekans", "grimer", "sneasel"]): return "Darkness"
            if any(x in name for x in ["dragonite", "dratini", "dragonair"]): return "Dragon"
            if any(x in name for x in ["melmetal", "meltan", "magnemite", "magneton", "magnezone"]): return "Metal"
            return "Colorless"

        def calculate_damage(card_details, attack_idx, my_bench_details):
            if not card_details or attack_idx >= len(card_details["attacks"]):
                return 0
            atk = card_details["attacks"][attack_idx]
            base_dmg = getattr(atk, "fixed_damage", 0)

            card_name = card_details["name"]
            atk_name = getattr(atk, "name", "")

            # Dynamic Damage Calculation
            if "Pikachu ex" in card_name and "Circle Circuit" in atk_name:
                lightning_count = 0
                for b in my_bench_details:
                    if b and "Lightning" in get_card_type(b):
                        lightning_count += 1
                return 30 * lightning_count

            if "Mewtwo ex" in card_name and "Psydrive" in atk_name:
                 return 150

            if "Starmie ex" in card_name and "Hydro Splash" in atk_name:
                 return 90

            if "Articuno ex" in card_name and "Blizzard" in atk_name:
                 return 80

            return base_dmg

        def get_energy_deficit(current_energy, attack_cost):
            current_counts = {}
            for e in current_energy:
                s = str(e)
                if "." in s: s = s.split(".")[-1]
                current_counts[s] = current_counts.get(s, 0) + 1

            specific_needed = {}
            colorless_cost = 0

            temp_counts = current_counts.copy()

            # First pass: satisfy specific requirements
            sorted_cost = []
            for c in attack_cost:
                s = str(c)
                if "." in s: s = s.split(".")[-1]
                if s == "Colorless":
                    sorted_cost.append((0, s))
                else:
                    sorted_cost.append((1, s))

            sorted_cost.sort(key=lambda x: x[0], reverse=True)

            remaining_cost_specific = []

            for priority, s in sorted_cost:
                if s == "Colorless":
                    colorless_cost += 1
                    continue

                if temp_counts.get(s, 0) > 0:
                    temp_counts[s] -= 1
                else:
                    remaining_cost_specific.append(s)

            for s in remaining_cost_specific:
                 specific_needed[s] = specific_needed.get(s, 0) + 1

            # Second pass: satisfy colorless with whatever is left
            remaining_energy_count = sum(temp_counts.values())
            colorless_needed = max(0, colorless_cost - remaining_energy_count)

            return specific_needed, colorless_needed

        def get_best_attack_cost(card_details, my_bench_details):
            if not card_details or not card_details["attacks"]:
                return []

            best_cost = []
            max_dmg = -1

            for i, atk in enumerate(card_details["attacks"]):
                cost = getattr(atk, "cost", [])
                dmg = calculate_damage(card_details, i, my_bench_details)

                if dmg > max_dmg:
                    max_dmg = dmg
                    best_cost = cost
                elif dmg == max_dmg:
                     if len(cost) < len(best_cost) or not best_cost:
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

                if "Some(" in card_name:
                    card_name = card_name.replace("Some(", "").replace(")", "")

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

        # A. Lethal Attacks (Priority #1)
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
            is_ko_switch = False
            if my_active and my_active["hp"] == 0:
                is_ko_switch = True
            elif not my_active:
                is_ko_switch = True

            if is_ko_switch:
                best_aid = actions["activate"][0][0]
                max_score = -float('inf')

                for aid, idx in actions["activate"]:
                    if idx < len(my_bench):
                        card = my_bench[idx]
                        if not card: continue

                        score = 0
                        score += card["hp"]
                        score += len(card["energy"]) * 50

                        name_lower = card["name"].lower()
                        if "ex" in name_lower:
                            if "pikachu" in name_lower: score += 100
                            elif "mewtwo" in name_lower: score += 90
                            elif "starmie" in name_lower: score += 90
                            elif "articuno" in name_lower: score += 80
                            else: score += 50
                        elif "kangaskhan" in name_lower: score += 40
                        elif "farfetch" in name_lower: score += 40

                        if "ralts" in name_lower or "kirlia" in name_lower: score -= 50

                        if score > max_score:
                            max_score = score
                            best_aid = aid
                return best_aid
            else:
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
                        if "ex" in card["name"].lower():
                             score += 50
                             if card["hp"] < 60: score += 500
                        if len(card["energy"]) == 0: score += 100
                        if card["hp"] < 60: score += 200

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
                if "articuno" in n and "ex" in n: return 80
                if "starmie" in n and "ex" in n: return 75
                if "mewtwo" in n and "ex" in n: return 60
                if "ex" in n: return 70
                if "ralts" in n: return 10
                if "magikarp" in n: return 5
                return 50

            best = max(actions["place_active"], key=lambda x: score_starter(x[1]))
            return best[0]

        # D. Evolution
        if actions["evolve"]:
            return actions["evolve"][0][0]

        # E. Bench Placement
        if actions["place_bench"]:
            is_pikachu_active = my_active and "Pikachu ex" in my_active["name"]
            current_bench_count = sum(1 for b in my_bench if b)

            best_bench_action = None
            max_bench_score = -float('inf')

            for aid, name in actions["place_bench"]:
                n = name.lower()
                score = 0
                score += 10
                if "ex" in n: score += 50
                if is_pikachu_active:
                     if "Lightning" in get_card_type({"name": name}): score += 40

                has_gardevoir = any("gardevoir" in getattr(h, "name", "").lower() for h in my_hand)
                if "ralts" in n and not has_gardevoir:
                     score -= 10

                if score > max_bench_score:
                    max_bench_score = score
                    best_bench_action = aid

            if current_bench_count < 3 and max_bench_score > 0:
                return best_bench_action

            if is_pikachu_active and current_bench_count < 3:
                 for aid, name in actions["place_bench"]:
                      if "Lightning" in get_card_type({"name": name}):
                           return aid

        # F. Supporters
        if actions["play_supporter"]:
            misty = [a for a in actions["play_supporter"] if "Misty" in a[1]]
            if misty:
                for aid, name, target in misty:
                    card = None
                    if target == 0: card = my_active
                    elif target > 0 and (target-1) < len(my_bench): card = my_bench[target-1]

                    if card and "Water" in get_card_type(card):
                        cost = get_best_attack_cost(card, my_bench)
                        spec, col = get_energy_deficit(card["energy"], cost)
                        if spec or col > 0:
                            return aid

            research = [a for a in actions["play_supporter"] if "Research" in a[1]]
            if research:
                if my_hand_size <= 5:
                    return research[0][0]

            sabrina = [a for a in actions["play_supporter"] if "Sabrina" in a[1]]
            if sabrina:
                opp_bench_count = sum(1 for b in opp_bench if b)
                if opp_bench_count > 0:
                    return sabrina[0][0]

            others = [a for a in actions["play_supporter"] if "Misty" not in a[1] and "Research" not in a[1] and "Sabrina" not in a[1]]
            if others:
                giovanni = [a for a in others if "Giovanni" in a[1]]
                if giovanni and actions["attack"] and opp_active:
                    max_dmg = max(calculate_damage(my_active, idx, my_bench) for _, idx in actions["attack"])
                    if max_dmg < opp_active["hp"] and (max_dmg + 10) >= opp_active["hp"]:
                        return giovanni[0][0]
                pass

        # G. Items
        if actions["play_item"]:
            potions = [a for a in actions["play_item"] if "Potion" in a[1]]
            if potions and my_active and my_active["hp"] < my_active["max_hp"]:
                if my_active["hp"] <= (my_active["max_hp"] - 20):
                     return potions[0][0]

            red_cards = [a for a in actions["play_item"] if "RedCard" in a[1]]
            if red_cards and opp_hand_size >= 4:
                return red_cards[0][0]

            balls = [a for a in actions["play_item"] if "Ball" in a[1]]
            if balls: return balls[0][0]

        # H. Energy Attachment
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

                cost = get_best_attack_cost(target_card, my_bench)
                spec_needed, col_needed = get_energy_deficit(target_card["energy"], cost)

                s_etype = str(etype)
                if "." in s_etype: s_etype = s_etype.split(".")[-1]

                is_useful = False

                if spec_needed.get(s_etype, 0) > 0:
                    is_useful = True
                    score += 100
                elif col_needed > 0:
                    is_useful = True
                    score += 60

                if not is_useful:
                    score -= 100

                if is_useful:
                    if pos == 0:
                        score += 50
                        if my_active["hp"] <= 30: score -= 80
                    else:
                        if "ex" in target_card["name"].lower(): score += 40
                        if "mewtwo" in target_card["name"].lower(): score += 20

                if score > max_attach_score:
                    max_attach_score = score
                    best_attach = aid

            if best_attach and max_attach_score > 0:
                return best_attach

        # I. Retreat
        if actions["retreat"]:
            should_retreat = False

            if my_active:
                if my_active["hp"] <= 50:
                     for b in my_bench:
                         if b and b["hp"] > 50 and len(b["energy"]) >= 1:
                             should_retreat = True
                             break

                if len(my_active["energy"]) == 0:
                     for b in my_bench:
                         if not b: continue
                         cost = get_best_attack_cost(b, my_bench)
                         s, c = get_energy_deficit(b["energy"], cost)
                         if not s and c == 0:
                              should_retreat = True
                              break

            if should_retreat:
                return actions["retreat"][0][0]

        # J. Attacks (Non-Lethal)
        if actions["attack"]:
            best_atk = None
            max_score = -float('inf')

            for aid, idx in actions["attack"]:
                dmg = calculate_damage(my_active, idx, my_bench)
                atk_name = getattr(my_active["attacks"][idx], "name", "").lower()

                score = dmg

                if "paralyze" in atk_name: score += 40
                if "sleep" in atk_name: score += 30
                if "confusion" in atk_name: score += 20

                if score > max_score:
                    max_score = score
                    best_atk = aid

            return best_atk

        # K. End Turn
        if actions["end_turn"]:
            return actions["end_turn"][0][0]

    except Exception:
        # Fallback to random legal action or just EndTurn if available
        # Also print traceback for debugging (it will show in logs)
        print("EXCEPTION IN PLAY FUNC:", file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)

        # Try to find EndTurn to safely end turn, otherwise random
        for aid in legal_actions:
            if game.action_name(aid) == "EndTurn":
                return aid
        return legal_actions[0]

    return legal_actions[0]
