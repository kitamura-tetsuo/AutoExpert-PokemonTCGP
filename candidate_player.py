
import re
import sys
import traceback

def play(state, game):
    """
    Improved Pokemon TCG Pocket Player
    Strategy: Aggressive setup, smart energy management, lethal prioritization.
    """
    legal_actions = game.legal_actions()
    if not legal_actions:
        return 0

    try:
        # --- 1. Helper Functions ---

        def get_card_data(card):
            if not card: return None
            # Handle both PyO3 objects and dicts if necessary (though state returns objects)
            return {
                "name": getattr(card, "name", ""),
                "hp": getattr(card, "remaining_hp", 0),
                "max_hp": getattr(card, "total_hp", 0),
                "energy": getattr(card, "attached_energy", []), # List of EnergyType objects
                "attacks": getattr(card, "attacks", []),
                "obj": card
            }

        def get_pokemon_type(name):
            n = name.lower()
            if any(x in n for x in ["pikachu", "zapdos", "raichu", "magneton", "electrode", "electabuzz", "jolteon", "blitzle", "zebstrika", "pincurchin", "mareep", "flaaffy", "ampharos", "helioptile", "heliolisk", "tynamo", "eelektrik", "eelektross", "luxray", "zebstrika"]): return "Lightning"
            if any(x in n for x in ["mewtwo", "ralts", "kirlia", "gardevoir", "gengar", "haunter", "gastly", "abra", "kadabra", "alakazam", "jynx", "mr. mime", "nidoran", "nidorina", "nidoqueen", "nidorino", "nidoking", "koffing", "weezing", "mew"]): return "Psychic"
            if any(x in n for x in ["starmie", "articuno", "blastoise", "lapras", "gyarados", "vaporeon", "golduck", "psyduck", "poliwag", "poliwhirl", "poliwrath", "seadra", "horsea", "squirtle", "wartortle", "tentacool", "tentacruel", "shellder", "cloyster", "krabby", "kingler", "goldeen", "seaking", "staryu", "magikarp", "greninja", "frogadier", "froakie"]): return "Water"
            if any(x in n for x in ["charizard", "moltres", "arcanine", "ninetales", "rapidash", "magmar", "flareon", "charmander", "charmeleon", "vulpix", "growlithe", "ponyta"]): return "Fire"
            if any(x in n for x in ["venusaur", "exeggutor", "victreebel", "vileplume", "butterfree", "beedrill", "scyther", "pinsir", "tangela", "bulbasaur", "ivysaur", "caterpie", "metapod", "weedle", "kakuna", "oddish", "gloom", "paras", "parasect", "venonat", "venomoth", "bellsprout", "weepinbell", "exeggcute"]): return "Grass"
            if any(x in n for x in ["machamp", "hitmonlee", "hitmonchan", "golem", "onix", "rhydon", "marowak", "dugtrio", "sandslash", "geodude", "graveler", "sandshrew", "diglett", "mankey", "primeape", "machop", "machoke", "cubone", "rhyhorn", "kabuto", "kabutops", "aerodactyl"]): return "Fighting"
            if any(x in n for x in ["darkrai", "weavile", "arbok", "muk", "weezing", "ekans", "grimer", "sneasel", "houndoom"]): return "Darkness"
            if any(x in n for x in ["dragonite", "dratini", "dragonair"]): return "Dragon"
            if any(x in n for x in ["melmetal", "meltan", "magnemite", "magneton", "magnezone"]): return "Metal"
            return "Colorless"

        def calculate_potential_damage(attacker, attack_idx, my_bench, opp_active_hp):
            """Calculates damage, accounting for some dynamic effects."""
            if not attacker or attack_idx >= len(attacker["attacks"]): return 0

            atk = attacker["attacks"][attack_idx]
            base_dmg = getattr(atk, "fixed_damage", 0)
            name = attacker["name"]
            atk_name = getattr(atk, "name", "")

            # --- Dynamic Damage Logic ---
            if "Pikachu ex" in name and "Circle Circuit" in atk_name:
                lightning_count = 0
                for b in my_bench:
                    if b and "Lightning" in get_pokemon_type(b["name"]):
                        lightning_count += 1
                return 30 * lightning_count

            if "Mewtwo ex" in name and "Psydrive" in atk_name: return 150
            if "Starmie ex" in name and "Hydro Splash" in atk_name: return 90
            if "Articuno ex" in name and "Blizzard" in atk_name: return 80
            if "Greninja" in name and "Mist Slash" in atk_name: return 60
            if "Marowak ex" in name and "Bonemerang" in atk_name: return 160 # Assume double heads for potential check, or avg 80

            if "Blastoise ex" in name and "Hydro Bazooka" in atk_name:
                w_count = sum(1 for e in attacker["energy"] if "Water" in str(e))
                return 160 if w_count >= 5 else 100

            if "Charizard ex" in name and "Crimson Storm" in atk_name: return 200

            return base_dmg

        def needs_energy(card, my_bench):
            """Returns true if the card needs more energy for its best attack."""
            if not card: return False
            if not card["attacks"]: return False

            # Find most expensive useful attack
            max_cost_len = 0

            # Special cases
            if "Mewtwo ex" in card["name"]: max_cost_len = 4 # Psydrive
            elif "Starmie ex" in card["name"]: max_cost_len = 2 # Hydro Splash
            elif "Pikachu ex" in card["name"]: max_cost_len = 2 # Circle Circuit
            elif "Charizard ex" in card["name"]: max_cost_len = 4 # Crimson Storm
            else:
                 for atk in card["attacks"]:
                     cost = getattr(atk, "cost", [])
                     if len(cost) > max_cost_len:
                         max_cost_len = len(cost)

            return len(card["energy"]) < max_cost_len

        # --- 2. Parse State ---
        me = state.current_player
        opp = 1 - me

        my_active = get_card_data(state.get_active_pokemon(me))
        my_bench = [get_card_data(c) for c in state.get_bench_pokemon(me)]
        my_hand = state.get_hand(me)

        opp_active = get_card_data(state.get_active_pokemon(opp))
        opp_bench = [get_card_data(c) for c in state.get_bench_pokemon(opp)]

        # Categorize Actions
        acts = {
            "attack": [], "attach_energy": [], "attach_tool": [],
            "evolve": [], "place_basic": [], "place_active": [], "play_supporter": [],
            "play_item": [], "ability": [], "retreat": [],
            "activate": [], "end": []
        }

        for aid in legal_actions:
            aname = game.action_name(aid)

            if aname == "EndTurn": acts["end"].append(aid)
            elif aname.startswith("Attack("):
                m = re.search(r"Attack\((\d+)\)", aname)
                if m: acts["attack"].append((aid, int(m.group(1))))
            elif aname.startswith("AttachTool"):
                # AttachTool(Some(Name), Pos)
                m = re.search(r"AttachTool\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
                if m: acts["attach_tool"].append((aid, m.group(1).replace(")", ""), int(m.group(2))))
            elif aname.startswith("Attach"):
                # Attach(Type, Pos) - Energy
                # Be careful not to catch AttachTool here if regex is loose, but distinct starts help
                if "Tool" in aname: continue
                m = re.search(r"Attach\((?:Some\()?(.*?)\)?, (\d+)\)", aname) # Standard format often Attach(Type, Pos)
                if m:
                    acts["attach_energy"].append((aid, m.group(1).replace(")", ""), int(m.group(2))))
                else:
                    # Fallback for explicit energy names if format differs
                    m = re.search(r"AttachEnergy\((\d+), (.*?)\)", aname)
                    if m: acts["attach_energy"].append((aid, m.group(2), int(m.group(1))))
            elif aname.startswith("Evolve"):
                m = re.search(r"Evolve\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
                if m: acts["evolve"].append((aid, m.group(1).replace(")", ""), int(m.group(2))))
            elif aname.startswith("Place") or aname.startswith("PlayPokemon"):
                 # Place(Some(Name), Pos)
                 m = re.search(r"Place\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
                 if m:
                     if int(m.group(2)) == 0:
                         acts["place_active"].append((aid, m.group(1).replace(")", "")))
                     else: acts["place_basic"].append((aid, m.group(1).replace(")", ""), int(m.group(2))))
                 elif "PlayPokemon" in aname:
                     # PlayPokemon(HandIdx, Pos) - less common in some versions but handled
                     if ", 0)" in aname: acts["place_active"].append((aid, "Unknown"))
                     else: acts["place_basic"].append((aid, "Unknown", -1))
            elif aname.startswith("Play") or aname.startswith("UseItem") or aname.startswith("UseSupporter"):
                # Play(Some(Name)) or Play(Some(Name), Target)
                # Need to parse Name to distinguish Item/Supporter
                target = -1
                name_str = aname
                m_t = re.search(r", (\d+)\)", aname)
                if m_t: target = int(m_t.group(1))

                # Extract inner name
                m_n = re.search(r"Some\((.*?)\)", aname)
                if m_n: card_name = m_n.group(1).replace(")", "")
                else: card_name = aname # Fallback

                supporters = ["Research", "Sabrina", "Giovanni", "Erika", "Misty", "Blaine", "Koga", "Lt. Surge", "Brock", "Copycat", "Lisia", "Cyrus", "Mars", "Red", "Guzma", "Judge", "Acerola", "Hau", "Bill"]

                is_supporter = any(s in card_name for s in supporters)
                if is_supporter:
                    acts["play_supporter"].append((aid, card_name, target))
                else:
                    acts["play_item"].append((aid, card_name, target))

            elif aname.startswith("UseAbility"):
                m = re.search(r"UseAbility\((\d+)\)", aname)
                if m: acts["ability"].append((aid, int(m.group(1))))
            elif aname.startswith("Retreat"):
                acts["retreat"].append(aid)
            elif aname.startswith("Activate"):
                m = re.search(r"Activate\((\d+)\)", aname)
                if m: acts["activate"].append((aid, int(m.group(1))))

        # --- 3. Logic & Strategy ---

        # A. Immediate Lethal Check
        lethal_action = None
        best_lethal_dmg = -1

        if acts["attack"] and opp_active:
             # Check Giovanni Lethal
             giovanni = [a for a in acts["play_supporter"] if "Giovanni" in a[1]]

             for aid, idx in acts["attack"]:
                 raw_dmg = calculate_potential_damage(my_active, idx, my_bench, opp_active["hp"])

                 # Natural Lethal
                 if raw_dmg >= opp_active["hp"]:
                     if lethal_action is None or raw_dmg > best_lethal_dmg:
                         lethal_action = aid
                         best_lethal_dmg = raw_dmg

                 # Giovanni Lethal
                 elif giovanni and (raw_dmg + 10) >= opp_active["hp"]:
                      # Can't return sequence here, but can prioritize Giovanni later
                      pass

        # B. Activate (Forced Switch / Sabrina Switch)
        if acts["activate"]:
            # Context 1: My Active KO'd -> Choose New Active
            if not my_active or my_active["hp"] == 0:
                best_cand = acts["activate"][0][0]
                max_score = -1000

                for aid, idx in acts["activate"]:
                    if idx >= len(my_bench): continue
                    c = my_bench[idx]
                    if not c: continue

                    score = c["hp"] + (len(c["energy"]) * 50)
                    if "ex" in c["name"].lower(): score += 100
                    if "Mewtwo" in c["name"]: score += 50
                    if "Pikachu" in c["name"]: score += 60

                    # Penalty for non-attackers
                    if "Ralts" in c["name"] or "Kirlia" in c["name"]: score -= 200

                    if score > max_score:
                        max_score = score
                        best_cand = aid
                return best_cand

            # Context 2: Sabrina / Opponent Switch
            else:
                 # Pick the weakest or most valuable target
                 best_cand = acts["activate"][0][0]
                 max_score = -1000

                 # Calculate my damage potential
                 my_dmg = 0
                 if acts["attack"]:
                     for _, idx in acts["attack"]:
                         d = calculate_potential_damage(my_active, idx, my_bench, 999)
                         my_dmg = max(my_dmg, d)

                 for aid, idx in acts["activate"]:
                     if idx >= len(opp_bench): continue
                     c = opp_bench[idx]
                     if not c: continue

                     score = 0
                     # Can I kill it?
                     if my_dmg >= c["hp"]: score += 1000

                     # Is it an EX?
                     if "ex" in c["name"].lower(): score += 500

                     # Is it high energy? (Threat)
                     score += len(c["energy"]) * 50

                     if score > max_score:
                         max_score = score
                         best_cand = aid
                 return best_cand

        # C. Winning Move
        if lethal_action:
            return lethal_action

        # X. Place Active (Start of Game)
        if acts["place_active"]:
             best_active = acts["place_active"][0][0]
             max_score = -1000

             for aid, name in acts["place_active"]:
                 score = 0
                 n = name.lower()
                 if "pikachu" in n and "ex" in n: score += 100
                 if "kangaskhan" in n: score += 90
                 if "farfetch" in n: score += 85
                 if "articuno" in n and "ex" in n: score += 80
                 if "starmie" in n and "ex" in n: score += 75
                 if "mewtwo" in n and "ex" in n: score += 60
                 if "ex" in n: score += 70
                 if "ralts" in n: score += 10
                 if "magikarp" in n: score += 5

                 if score > max_score:
                     max_score = score
                     best_active = aid
             return best_active

        # D. Setup Phase

        # 1. Evolve (Always good usually)
        if acts["evolve"]:
            return acts["evolve"][0][0] # Just take first available evolution

        # 2. Abilities (Draw/Energy)
        if acts["ability"]:
            for aid, idx in acts["ability"]:
                # Identify ability user
                user = my_active if idx == 0 else (my_bench[idx-1] if idx-1 < len(my_bench) else None)
                if user:
                    n = user["name"].lower()
                    # High priority abilities
                    if "gardevoir" in n: return aid # Psychic Embrace
                    if "greninja" in n: return aid # Water Shuriken
                    if "pidgeot" in n: return aid # Quick Search
                    if "draludon" in n: return aid

        # 3. Play Basic Pokemon
        if acts["place_basic"]:
            # Only play if bench not full and pokemon is useful
            # Priority: EX > High HP Basics > Others
            best_bp = None
            best_score = -1

            for aid, name, _ in acts["place_basic"]:
                score = 0
                n = name.lower()
                if "ex" in n: score += 100
                if "pikachu" in n: score += 50
                if "mewtwo" in n: score += 50
                if "articuno" in n: score += 50
                if "starmie" in n: score += 50
                if "ralts" in n:
                     # Only if we have evos
                     score += 20

                # Don't clog bench with useless stuff
                if score > best_score:
                    best_score = score
                    best_bp = aid

            if best_bp: return best_bp

        # 4. Supporters
        if acts["play_supporter"]:
            # Misty
            misty = [a for a in acts["play_supporter"] if "Misty" in a[1]]
            if misty:
                # Prioritize Active if needs energy
                if my_active and needs_energy(my_active, my_bench) and "Water" in get_pokemon_type(my_active["name"]):
                    for aid, _, target in misty:
                        if target == 0: return aid

                # Else Bench EX
                for i, b in enumerate(my_bench):
                    if b and needs_energy(b, my_bench) and "Water" in get_pokemon_type(b["name"]):
                         for aid, _, target in misty:
                             if target == i + 1: return aid

            # Professor's Research
            research = [a for a in acts["play_supporter"] if "Research" in a[1]]
            if research:
                if len(my_hand) <= 4: return research[0][0]

            # Sabrina
            sabrina = [a for a in acts["play_supporter"] if "Sabrina" in a[1]]
            if sabrina and opp_bench:
                 # Play if Opp Active is hard to kill but Bench is vulnerable
                 opp_threat_hp = opp_active["hp"] if opp_active else 0
                 my_dmg = 0
                 if acts["attack"]:
                      for _, idx in acts["attack"]:
                          my_dmg = max(my_dmg, calculate_potential_damage(my_active, idx, my_bench, opp_threat_hp))

                 if my_dmg < opp_threat_hp:
                     # Check if we can kill something on bench
                     can_kill_bench = False
                     for b in opp_bench:
                         if b and b["hp"] <= my_dmg:
                             can_kill_bench = True
                             break
                     if can_kill_bench:
                         return sabrina[0][0]

        # 5. Attach Energy
        if acts["attach_energy"]:
            best_attach = None
            max_score = -1000

            for aid, type_str, pos in acts["attach_energy"]:
                score = 0
                target = my_active if pos == 0 else (my_bench[pos-1] if pos-1 < len(my_bench) else None)
                if not target: continue

                needed = needs_energy(target, my_bench)

                if needed:
                    score += 100
                    if pos == 0: score += 50 # Priority to Active
                    if "ex" in target["name"].lower(): score += 20
                else:
                    score -= 50 # Over-attaching

                # Specific logic
                if "Mewtwo ex" in target["name"] and "Psychic" in type_str: score += 10
                if "Pikachu ex" in target["name"] and "Lightning" in type_str: score += 10

                if score > max_score:
                    max_score = score
                    best_attach = aid

            if best_attach and max_score > 0:
                return best_attach

        # 6. Items (Potion)
        if acts["play_item"]:
            potion = [a for a in acts["play_item"] if "Potion" in a[1]]
            if potion and my_active and my_active["hp"] <= my_active["max_hp"] - 20:
                return potion[0][0]

        # 7. Retreat
        if acts["retreat"]:
            if my_active and my_active["hp"] <= 40:
                # Check if we have a replacement
                has_ready_bench = False
                for b in my_bench:
                    if b and b["hp"] > 40 and not needs_energy(b, my_bench):
                        has_ready_bench = True

                if has_ready_bench:
                    return acts["retreat"][0]

        # 8. Attack (Best Damage)
        if acts["attack"]:
            best_atk = acts["attack"][0][0]
            max_dmg = -1

            for aid, idx in acts["attack"]:
                d = calculate_potential_damage(my_active, idx, my_bench, opp_active["hp"] if opp_active else 0)
                if d > max_dmg:
                    max_dmg = d
                    best_atk = aid

            return best_atk

        # 9. End Turn
        if acts["end"]:
            return acts["end"][0]

        return legal_actions[0]

    except Exception:
        # Fallback
        # print(traceback.format_exc(), file=sys.stderr)
        return legal_actions[0]
