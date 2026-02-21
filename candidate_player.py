
import re
import random
import sys
import logging
from db_dump import CARD_DB

# Setup logging
logging.basicConfig(filename='player.log', level=logging.INFO, filemode='w', format='%(asctime)s - %(message)s')

def play(state, game):
    """
    Advanced Pokemon TCG Pocket Player (v9 - DB Integrated)
    """
    legal_actions = game.legal_actions()
    if not legal_actions:
        return 0

    try:
        # --- 1. Helper Functions ---
        def get_card_name(card_obj):
            if not card_obj: return None
            return getattr(card_obj, "name", "Unknown")

        def get_card_hp(card_obj):
            if not card_obj: return 0
            return getattr(card_obj, "remaining_hp", 0)

        def get_card_max_hp(card_obj):
            if not card_obj: return 0
            return getattr(card_obj, "total_hp", 0)

        def get_card_energy(card_obj):
            if not card_obj: return []
            return [str(e) for e in getattr(card_obj, "attached_energy", [])]

        def get_energy_type(card_name):
            if not card_name: return "colorless"
            n = card_name.lower()
            if n in CARD_DB:
                return CARD_DB[n].get("energy_type", "colorless").lower()

            # Fallback for cards not in DB or if DB is incomplete
            if any(x in n for x in ["pikachu", "zapdos", "raichu", "magneton", "electrode", "blitzle", "electabuzz"]): return "lightning"
            if any(x in n for x in ["mewtwo", "ralts", "kirlia", "gardevoir", "gengar", "abra", "gastly", "mew"]): return "psychic"
            if any(x in n for x in ["starmie", "articuno", "blastoise", "greninja", "squirtle", "poliwag", "suicune", "lapras"]): return "water"
            if any(x in n for x in ["charizard", "moltres", "arcanine", "charmander", "vulpix", "ponyta", "magmar"]): return "fire"
            if any(x in n for x in ["venusaur", "exeggutor", "bulbasaur", "caterpie", "weedle", "scyther", "pinsir"]): return "grass"
            if any(x in n for x in ["machamp", "marowak", "golem", "geodude", "onix", "rhyhorn", "hitmon", "kabuto"]): return "fighting"
            if any(x in n for x in ["dragonite", "dratini"]): return "dragon"
            if any(x in n for x in ["melmetal", "meltan", "mawile"]): return "metal"
            if any(x in n for x in ["weavile", "muk", "koffing", "ekans", "nidoran", "zubat", "darkrai"]): return "darkness"
            return "colorless"

        def calculate_damage(attacker_card, attack_idx, my_bench_len, opp_active_hp, opp_active_card=None):
            name = get_card_name(attacker_card)
            if not name: return 0
            n_lower = name.lower()

            # 1. Check DB first
            if n_lower in CARD_DB and "attacks" in CARD_DB[n_lower]:
                attacks_db = CARD_DB[n_lower]["attacks"]
                if attack_idx < len(attacks_db):
                    atk = attacks_db[attack_idx]
                    base = atk.get("dmg", 0)

                    # Scaling logic
                    if atk.get("scaling"):
                        text = atk.get("text", "").lower()
                        if "bench" in text and "20 more damage" in text: # e.g. Pidgeot
                             return base + (20 * my_bench_len)
                        if "bench" in text and "30 damage for each" in text: # e.g. Pikachu ex
                             # Estimate bench lightning pokemon. Assume 50% are lightning if type is lightning
                             return 30 * my_bench_len # Simplified
                        if "damage on it" in text:
                             if get_card_hp(attacker_card) < get_card_max_hp(attacker_card):
                                 return base + 60 # Estimate
                        if "extra" in text and "energy" in text:
                             return base + 40 # Assume extra energy attached if we are attacking

                    if "coin_flips" in atk:
                        # Return expected value for planning, or max for potential
                        return base + (atk["coin_flips"] * 40 * 0.5) # Assuming avg 40 dmg per head or similar logic?
                        # Actually most coin flips are "x damage for each heads". Let's look at Marowak ex
                        if "80 damage for each heads" in atk.get("text", ""):
                             return 80 * atk["coin_flips"] * 0.5 # Expected value

                    if base > 0: return base

            # 2. Check Object Attributes
            attacks_obj = getattr(attacker_card, "attacks", [])
            if attack_idx < len(attacks_obj):
                atk_obj = attacks_obj[attack_idx]
                fixed = getattr(atk_obj, "fixed_damage", 0)
                if fixed > 0: return fixed
                dmg = getattr(atk_obj, "damage", 0)
                if dmg > 0: return dmg
            return 0

        def needs_energy(card_obj):
            name = get_card_name(card_obj)
            if not name: return False
            current_energy = len(get_card_energy(card_obj))

            n_lower = name.lower()
            if n_lower in CARD_DB:
                attacks = CARD_DB[n_lower].get("attacks", [])
                if not attacks: return False
                # Aim for the cost of the strongest attack
                max_cost = 0
                for atk in attacks:
                    cost_list = atk.get("cost", [])
                    if len(cost_list) > max_cost:
                        max_cost = len(cost_list)
                return current_energy < max_cost

            # Fallback
            if "ex" in n_lower: return current_energy < 3
            return current_energy < 2

        # --- 2. Parse State ---
        me = state.current_player
        opp = 1 - me
        my_active = state.get_active_pokemon(me)
        my_bench = [b for b in state.get_bench_pokemon(me) if b is not None]
        my_hand = state.get_hand(me)
        opp_active = state.get_active_pokemon(opp)
        opp_bench = [b for b in state.get_bench_pokemon(opp) if b is not None]

        my_active_name = get_card_name(my_active)
        my_active_hp = get_card_hp(my_active)
        my_active_max_hp = get_card_max_hp(my_active)
        opp_active_hp = get_card_hp(opp_active) if opp_active else 0

        # Categorize Actions
        acts = {
            "attack": [], "attach_energy": [], "attach_tool": [],
            "evolve": [], "place_basic": [], "place_active": [], "play_supporter": [],
            "play_item": [], "ability": [], "retreat": [],
            "activate": [], "end": [], "draw": [], "stadium": []
        }

        for aid in legal_actions:
            aname = game.action_name(aid)

            if aname == "EndTurn": acts["end"].append(aid)
            elif aname == "DrawCard": acts["draw"].append(aid)
            elif aname.startswith("Attack("):
                m = re.search(r"Attack\((\d+)\)", aname)
                if m: acts["attack"].append((aid, int(m.group(1))))
            elif aname.startswith("AttachTool"):
                m = re.search(r"AttachTool\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
                if m: acts["attach_tool"].append((aid, m.group(1).replace(")", ""), int(m.group(2))))
            elif aname.startswith("Attach"):
                if "Tool" in aname: continue
                m = re.search(r"Attach\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
                if m: acts["attach_energy"].append((aid, m.group(1).replace(")", ""), int(m.group(2))))
                else:
                    m = re.search(r"AttachEnergy\((\d+), (.*?)\)", aname)
                    if m: acts["attach_energy"].append((aid, m.group(2), int(m.group(1))))
            elif aname.startswith("Evolve"):
                m = re.search(r"Evolve\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
                if m: acts["evolve"].append((aid, m.group(1).replace(")", ""), int(m.group(2))))
            elif aname.startswith("Place") or aname.startswith("PlayPokemon"):
                 m = re.search(r"Place\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
                 if m:
                     if int(m.group(2)) == 0: acts["place_active"].append((aid, m.group(1).replace(")", "")))
                     else: acts["place_basic"].append((aid, m.group(1).replace(")", ""), int(m.group(2))))
                 elif "PlayPokemon" in aname:
                     if ", 0)" in aname: acts["place_active"].append((aid, "Unknown"))
                     else: acts["place_basic"].append((aid, "Unknown", -1))
            elif aname.startswith("Play") or aname.startswith("UseItem") or aname.startswith("UseSupporter"):
                target = -1
                m_t = re.search(r", (\d+)\)", aname)
                if m_t: target = int(m_t.group(1))
                m_n = re.search(r"Some\((.*?)\)", aname)
                if m_n: card_name = m_n.group(1).replace(")", "")
                else: card_name = aname

                supporters = ["Research", "Sabrina", "Giovanni", "Erika", "Misty", "Blaine", "Koga", "Lt. Surge", "Brock", "Copycat", "Lisia", "Cyrus", "Mars", "Red", "Guzma", "Judge", "Acerola", "Hau", "Bill"]
                if any(s in card_name for s in supporters): acts["play_supporter"].append((aid, card_name, target))
                else: acts["play_item"].append((aid, card_name, target))
            elif aname.startswith("UseAbility"):
                m = re.search(r"UseAbility\((\d+)\)", aname)
                if m: acts["ability"].append((aid, int(m.group(1))))
            elif aname.startswith("Retreat"): acts["retreat"].append(aid)
            elif aname.startswith("Activate"):
                m = re.search(r"Activate\((\d+)\)", aname)
                if m: acts["activate"].append((aid, int(m.group(1))))
            elif "Stadium" in aname: acts["stadium"].append(aid)

        # --- 3. Strategy Execution ---

        # 0. Draw Card
        if acts["draw"]: return acts["draw"][0]

        # 1. Check for Lethal (Priority)
        if acts["attack"] and opp_active_hp > 0:
            giovanni = [a for a in acts["play_supporter"] if "Giovanni" in a[1]]

            best_lethal_action = None
            min_lethal_cost = 999

            for aid, idx in acts["attack"]:
                dmg = calculate_damage(my_active, idx, len(my_bench), opp_active_hp)

                # Check direct lethal
                if dmg >= opp_active_hp:
                    return aid # Immediate win

                # Check Giovanni lethal
                if giovanni and (dmg + 10) >= opp_active_hp:
                    return giovanni[0][0] # Play Giovanni then attack next loop

        # 2. Forced Switch (Activate)
        if acts["activate"]:
            # If we need to choose a new active (e.g. ours died)
            if not my_active or my_active_hp == 0:
                best_cand = acts["activate"][0][0]
                max_score = -2000
                for aid, idx in acts["activate"]:
                    if idx >= len(my_bench): continue
                    c = my_bench[idx]
                    if not c: continue
                    name = get_card_name(c); score = 0
                    is_ex = "ex" in name.lower()
                    energy_count = len(get_card_energy(c))
                    hp = get_card_hp(c)

                    # Prioritize pokemon with energy and full HP
                    if not needs_energy(c): score += 500
                    elif energy_count > 0: score += 100 * energy_count
                    if is_ex: score += 50
                    score += hp
                    if score > max_score: max_score = score; best_cand = aid
                return best_cand
            else:
                # This is likely Sabrina effect or similar targeting opponent?
                # Actually Activate usually targets OWN bench if active slot empty.
                # If active is present, Activate usually means nothing unless card effect.
                return acts["activate"][0][0]

        # 3. Setup Phase Actions

        # A. Place Active (Start of Game)
        if acts["place_active"]:
            best_active = acts["place_active"][0][0]; max_score = -1000
            for aid, name in acts["place_active"]:
                score = 0; n = name.lower()
                # Prioritize high HP / Strong attackers
                if "ex" in n: score += 100
                if "kangaskhan" in n: score += 80
                if "articuno" in n: score += 70
                if "moltres" in n: score += 70
                if "zapdos" in n: score += 70
                if "mewtwo" in n: score += 60

                # Deprioritize support
                if "pidgey" in n: score -= 50
                if "ralts" in n: score -= 50
                if "meowth" in n: score -= 20

                if score > max_score: max_score = score; best_active = aid
            return best_active

        # B. Evolve (Always good usually)
        if acts["evolve"]:
            return acts["evolve"][0][0]

        # C. Place Basic on Bench
        if acts["place_basic"]:
            if len(my_bench) < 3:
                best_bp = None; best_score = -100
                for aid, name, _ in acts["place_basic"]:
                    score = 10; n = name.lower() # Base score 10 to ensure we place something
                    # Setup bench with support or secondary attackers
                    if "ralts" in n: score += 90 # Gardevoir line is good
                    if "pidgey" in n: score += 80 # Pidgeot line is good
                    if "ex" in n: score += 70
                    if "meowth" in n: score += 20 # Draw engine
                    if "articuno" in n: score += 50
                    if "moltres" in n: score += 50
                    if "zapdos" in n: score += 50

                    if score > best_score: best_score = score; best_bp = aid

                if best_bp: return best_bp

        # D. Abilities (Draw/Search/Energy)
        if acts["ability"]:
            for aid, idx in acts["ability"]:
                # Identify ability user
                user = my_active if idx == 0 else (my_bench[idx-1] if idx-1 < len(my_bench) else None)
                if user:
                    n = get_card_name(user).lower()
                    # Greninja Water Shuriken: Always good
                    if "greninja" in n: return aid
                    # Pidgeot Quick Search: Always good
                    if "pidgeot" in n: return aid
                    # Gardevoir Psy Shadow: Only if we need energy
                    if "gardevoir" in n:
                         if needs_energy(my_active) or any(needs_energy(b) for b in my_bench): return aid
            return acts["ability"][0][0]

        # E. Play Supporters
        if acts["play_supporter"]:
            # Misty
            misty = [a for a in acts["play_supporter"] if "Misty" in a[1]]
            if misty:
                best_misty = None; best_score = -1
                # Target Water types that need energy
                targets = [(my_active, 0)] + [(b, i+1) for i, b in enumerate(my_bench) if b]
                for t_card, t_idx in targets:
                    if not t_card: continue
                    name = get_card_name(t_card)
                    if "water" in get_energy_type(name):
                        score = 100
                        if "ex" in name.lower(): score += 50
                        if not needs_energy(t_card): score -= 80

                        # Find action for this target
                        for aid, _, target_act in misty:
                            if target_act == t_idx and score > best_score:
                                best_score = score; best_misty = aid
                if best_misty: return best_misty

            # Research
            research = [a for a in acts["play_supporter"] if "Research" in a[1]]
            if research and len(my_hand) <= 5: return research[0][0]

            # Sabrina
            sabrina = [a for a in acts["play_supporter"] if "Sabrina" in a[1]]
            if sabrina and opp_bench:
                # Use if we can't kill active but might kill something else, or just to disrupt
                if opp_active_hp > 60: return sabrina[0][0]

        # F. Attach Energy
        if acts["attach_energy"]:
            best_attach = None; max_score = -1000
            for aid, type_str, pos in acts["attach_energy"]:
                score = 0
                target = my_active if pos == 0 else (my_bench[pos-1] if pos-1 < len(my_bench) else None)
                if not target: continue

                t_name = get_card_name(target);
                t_type = get_energy_type(t_name);
                type_str_lower = type_str.lower()

                # Match type
                match = (type_str_lower == t_type) or (t_type == "colorless")
                if not match: score -= 100 # Wrong energy type penalty

                if needs_energy(target):
                    score += 100
                    if pos == 0: score += 50 # Active priority
                    if "ex" in t_name.lower(): score += 30

                    # Specific combos
                    if "mewtwo" in t_name.lower() and "psychic" in type_str_lower: score += 50
                    if "pikachu" in t_name.lower() and "lightning" in type_str_lower: score += 50
                    if "charizard" in t_name.lower() and "fire" in type_str_lower: score += 50
                    if "blastoise" in t_name.lower() and "water" in type_str_lower: score += 50
                    if "venusaur" in t_name.lower() and "grass" in type_str_lower: score += 50
                else:
                    score -= 50 # Already has energy

                if score > max_score: max_score = score; best_attach = aid

            if best_attach and max_score > 0: return best_attach

        # G. Play Items
        if acts["play_item"]:
            # Potion
            potion = [a for a in acts["play_item"] if "Potion" in a[1]]
            if potion:
                 if my_active_hp > 0 and my_active_hp <= my_active_max_hp - 20: return potion[0][0]

            # X Speed
            x_speed = [a for a in acts["play_item"] if "X Speed" in a[1]]
            if x_speed and my_active_hp <= 70: return x_speed[0][0]

            # Red Card
            redcard = [a for a in acts["play_item"] if "Red Card" in a[1]]
            # Cannot see opponent hand size easily in provided state object wrapper (maybe?)
            # Assuming large hand is bad for them
            if redcard: return redcard[0][0]

            # Pokeball
            pokeball = [a for a in acts["play_item"] if "Ball" in a[1]]
            if pokeball: return pokeball[0][0]

        # H. Retreat
        if acts["retreat"] and my_active:
            # Retreat if low HP and we have a bench replacement ready
            if my_active_hp <= 60:
                 for b in my_bench:
                     if b and get_card_hp(b) > 50 and not needs_energy(b):
                         return acts["retreat"][0]

        # I. Attack
        if acts["attack"]:
            best_atk = acts["attack"][0][0]
            max_score = -1

            for aid, idx in acts["attack"]:
                d = calculate_damage(my_active, idx, len(my_bench), opp_active_hp)
                score = d
                # Status effects bonus
                text = ""
                if my_active_name.lower() in CARD_DB:
                     attacks = CARD_DB[my_active_name.lower()].get("attacks", [])
                     if idx < len(attacks): text = str(attacks[idx].get("text", ""))

                if "Asleep" in text: score += 15
                if "Paralyzed" in text: score += 20
                if "Confused" in text: score += 5

                if score > max_score:
                    max_score = score
                    best_atk = aid
            return best_atk

        # J. End Turn
        if acts["end"]: return acts["end"][0]

        return legal_actions[0]

    except Exception as e:
        logging.error(f"Error in play: {e}")
        return legal_actions[0]
