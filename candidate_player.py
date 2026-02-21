
import re
import random
import sys
import logging
from db_dump import CARD_DB

# Setup logging
logging.basicConfig(filename='player.log', level=logging.INFO, filemode='w', format='%(asctime)s - %(message)s')

def play(state, game):
    """
    Advanced Pokemon TCG Pocket Player (v14 - Strategic Logic)
    """
    legal_actions = game.legal_actions()
    if not legal_actions:
        return 0

    try:
        # --- 1. Helper Functions ---
        def get_card_name(card_obj):
            if not card_obj: return "Unknown"
            val = getattr(card_obj, "name", "Unknown")
            return val if val is not None else "Unknown"

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

            # Fallback Heuristics
            if any(x in n for x in ["pikachu", "zapdos", "raichu", "magneton", "electrode", "blitzle", "electabuzz", "zebstrika", "luxray", "heliolisk"]): return "lightning"
            if any(x in n for x in ["mewtwo", "ralts", "kirlia", "gardevoir", "gengar", "abra", "gastly", "mew", "indeedee", "nidoran", "arbok", "weezing", "koffing", "muk", "grimer"]): return "psychic"
            if any(x in n for x in ["starmie", "articuno", "blastoise", "greninja", "squirtle", "poliwag", "suicune", "lapras", "psyduck", "golduck"]): return "water"
            if any(x in n for x in ["charizard", "moltres", "arcanine", "charmander", "vulpix", "ponyta", "magmar", "rapidash", "ninetales"]): return "fire"
            if any(x in n for x in ["venusaur", "exeggutor", "bulbasaur", "caterpie", "weedle", "scyther", "pinsir", "oddish", "gloom", "vileplume"]): return "grass"
            if any(x in n for x in ["machamp", "marowak", "golem", "geodude", "onix", "rhyhorn", "hitmon", "kabuto", "diglett", "dugtrio", "primeape"]): return "fighting"
            if any(x in n for x in ["dragonite", "dratini", "dragonair"]): return "dragon"
            if any(x in n for x in ["melmetal", "meltan", "mawile"]): return "metal"
            if any(x in n for x in ["weavile", "muk", "koffing", "ekans", "nidoran", "zubat", "darkrai", "umbreon"]): return "darkness"
            return "colorless"

        def calculate_damage(attacker_card, attack_idx, my_bench, opp_active_card=None):
            name = get_card_name(attacker_card)
            n_lower = name.lower()
            my_bench_len = len([b for b in my_bench if b])

            opp_energy_count = len(get_card_energy(opp_active_card)) if opp_active_card else 0

            damage = 0

            if n_lower in CARD_DB and "attacks" in CARD_DB[n_lower]:
                attacks_db = CARD_DB[n_lower]["attacks"]
                if attack_idx < len(attacks_db):
                    atk = attacks_db[attack_idx]
                    base = atk.get("dmg", 0)
                    text_val = atk.get("text")
                    text = text_val.lower() if text_val else ""

                    damage = base

                    if "pikachu ex" in n_lower and attack_idx == 0:
                        lightning_bench = 0
                        for b in my_bench:
                            if b:
                                b_name = get_card_name(b)
                                if "lightning" in get_energy_type(b_name): lightning_bench += 1
                        return 30 * lightning_bench

                    if "marowak ex" in n_lower and attack_idx == 0: return 100
                    if "indeedee ex" in n_lower and attack_idx == 0: return 30 + (30 * opp_energy_count)
                    if "mewtwo ex" in n_lower and attack_idx == 1: return 150
                    if "starmie ex" in n_lower and attack_idx == 0: return 90
                    if "articuno ex" in n_lower and attack_idx == 1: return 80
                    if "greninja" in n_lower and "ex" not in n_lower and attack_idx == 0: return 60

                    if atk.get("scaling"):
                        if "bench" in text and "damage for each of your benched" in text:
                             m_bench = re.search(r"(\d+) damage for each of your benched", text)
                             mult = int(m_bench.group(1)) if m_bench else 20
                             damage = base + (mult * my_bench_len)
                        elif "bench" in text and "more damage" in text:
                             damage = base + (20 * my_bench_len)
                        elif "damage on it" in text:
                             if get_card_hp(attacker_card) < get_card_max_hp(attacker_card): damage = base + 60
                        elif "extra" in text and "energy" in text: damage = base + 40
                        elif "opponent's active pokemon" in text and "energy" in text:
                             m_energy = re.search(r"(\d+) more damage for each energy", text)
                             mult = int(m_energy.group(1)) if m_energy else 20
                             damage = base + (mult * opp_energy_count)

                    if "coin_flips" in atk:
                        m_each = re.search(r"(\d+) damage for each heads", text)
                        if m_each:
                            dmg_per_head = int(m_each.group(1))
                            damage = base + (atk["coin_flips"] * dmg_per_head * 0.5)
                        else:
                            m_plus = re.search(r"(\d+) more damage", text)
                            if m_plus:
                                plus_dmg = int(m_plus.group(1))
                                damage = base + (plus_dmg * 0.5)

            if damage == 0:
                attacks_obj = getattr(attacker_card, "attacks", [])
                if attack_idx < len(attacks_obj):
                    atk_obj = attacks_obj[attack_idx]
                    fixed = getattr(atk_obj, "fixed_damage", 0)
                    if fixed > 0: damage = fixed
                    else:
                        dmg = getattr(atk_obj, "damage", 0)
                        if dmg > 0: damage = dmg
            return damage

        def needs_energy(card_obj):
            name = get_card_name(card_obj)
            current_energy = len(get_card_energy(card_obj))
            n_lower = name.lower()

            if n_lower in CARD_DB:
                attacks = CARD_DB[n_lower].get("attacks", [])
                if not attacks: return False

                best_cost = 0
                for atk in attacks:
                    cost_list = atk.get("cost", [])
                    cost_len = len(cost_list)
                    if cost_len > best_cost: best_cost = cost_len

                if "mewtwo ex" in n_lower:
                    if current_energy < 2: return True
                    if current_energy < 4: return True
                    return False
                if "starmie ex" in n_lower: return current_energy < 2
                if "pikachu ex" in n_lower: return current_energy < 2
                if "charizard ex" in n_lower: return current_energy < 4

                return current_energy < best_cost

            if "ex" in n_lower: return current_energy < 3
            return current_energy < 2

        # --- 2. Parse State ---
        me = state.current_player
        opp = 1 - me
        my_active = state.get_active_pokemon(me)
        my_bench_raw = state.get_bench_pokemon(me)
        my_bench = [b for b in my_bench_raw if b is not None]
        my_hand = state.get_hand(me)
        opp_active = state.get_active_pokemon(opp)
        opp_bench = [b for b in state.get_bench_pokemon(opp) if b is not None]

        my_active_name = get_card_name(my_active)
        my_active_hp = get_card_hp(my_active)
        my_active_max_hp = get_card_max_hp(my_active)
        opp_active_hp = get_card_hp(opp_active) if opp_active else 0

        acts = {
            "attack": [], "attach_energy": [], "attach_tool": [],
            "evolve": [], "place_basic": [], "place_active": [], "play_supporter": [],
            "play_item": [], "ability": [], "retreat": [],
            "activate": [], "end": [], "draw": [], "stadium": []
        }

        # Parsing Regexes
        re_attack = re.compile(r"Attack\((\d+)\)")
        re_attach_tool = re.compile(r"AttachTool\((?:Some\()?(.*?)\)?, (\d+)\)")
        re_attach_energy = re.compile(r"Attach\((?:Some\()?(.*?)\)?, (\d+)\)")
        re_attach_energy_alt = re.compile(r"AttachEnergy\((\d+), (.*?)\)")
        re_evolve = re.compile(r"Evolve\((?:Some\()?(.*?)\)?, (\d+)\)")
        re_place = re.compile(r"Place\((?:Some\()?(.*?)\)?, (\d+)\)")
        re_play_target = re.compile(r"Play\((?:Some\()?(.*?)\)?, (\d+)\)")
        re_play_simple = re.compile(r"Play\((?:Some\()?(.*?)\)\)?")
        re_ability = re.compile(r"UseAbility\((\d+)\)")
        re_activate = re.compile(r"Activate\((\d+)\)")

        supporters = ["Research", "Sabrina", "Giovanni", "Erika", "Misty", "Blaine", "Koga", "Lt. Surge", "Brock", "Copycat", "Lisia", "Cyrus", "Mars", "Red", "Guzma", "Judge", "Acerola", "Hau", "Bill"]

        for aid in legal_actions:
            aname = game.action_name(aid)

            if aname == "EndTurn": acts["end"].append(aid)
            elif aname == "DrawCard": acts["draw"].append(aid)

            elif aname.startswith("Attack"):
                m = re_attack.search(aname)
                if m: acts["attack"].append((aid, int(m.group(1))))

            elif aname.startswith("AttachTool"):
                m = re_attach_tool.search(aname)
                if m: acts["attach_tool"].append((aid, m.group(1).replace(")", ""), int(m.group(2))))

            elif aname.startswith("Attach"):
                if "Tool" in aname: continue
                m = re_attach_energy.search(aname)
                if m: acts["attach_energy"].append((aid, m.group(1).replace(")", ""), int(m.group(2))))
                else:
                    m = re_attach_energy_alt.search(aname)
                    if m: acts["attach_energy"].append((aid, m.group(2), int(m.group(1))))

            elif aname.startswith("Evolve"):
                m = re_evolve.search(aname)
                if m: acts["evolve"].append((aid, m.group(1).replace(")", ""), int(m.group(2))))

            elif aname.startswith("Place") or aname.startswith("PlayPokemon"):
                 m = re_place.search(aname)
                 if m:
                     if int(m.group(2)) == 0: acts["place_active"].append((aid, m.group(1).replace(")", "")))
                     else: acts["place_basic"].append((aid, m.group(1).replace(")", ""), int(m.group(2))))
                 elif "PlayPokemon" in aname:
                     if ", 0)" in aname: acts["place_active"].append((aid, "Unknown"))
                     else: acts["place_basic"].append((aid, "Unknown", -1))

            elif aname.startswith("Play") or aname.startswith("UseItem") or aname.startswith("UseSupporter"):
                m = re_play_target.search(aname)
                if m:
                    card_name = m.group(1).replace(")", "")
                    target = int(m.group(2))
                    if any(s in card_name for s in supporters): acts["play_supporter"].append((aid, card_name, target))
                    else: acts["play_item"].append((aid, card_name, target))
                else:
                    m = re_play_simple.search(aname)
                    if m:
                        card_name = m.group(1).replace(")", "")
                        target = -1
                        if any(s in card_name for s in supporters): acts["play_supporter"].append((aid, card_name, target))
                        else: acts["play_item"].append((aid, card_name, target))
                    else:
                         if "UseItem" in aname or "UseSupporter" in aname:
                             parts = aname.split("(")
                             if len(parts) > 1:
                                 name_part = parts[1].split(")")[0]
                                 if any(s in name_part for s in supporters): acts["play_supporter"].append((aid, name_part, -1))
                                 else: acts["play_item"].append((aid, name_part, -1))

            elif aname.startswith("UseAbility"):
                m = re_ability.search(aname)
                if m: acts["ability"].append((aid, int(m.group(1))))

            elif aname.startswith("Retreat"): acts["retreat"].append(aid)

            elif aname.startswith("Activate"):
                m = re_activate.search(aname)
                if m: acts["activate"].append((aid, int(m.group(1))))

            elif "Stadium" in aname: acts["stadium"].append(aid)

        # --- 3. Strategic Execution ---

        # 0. Draw
        if acts["draw"]: return acts["draw"][0]

        # 1. Lethal Check (Priority)
        if acts["attack"] and opp_active_hp > 0:
            max_dmg = 0; best_atk = acts["attack"][0][0]
            giovanni = [a for a in acts["play_supporter"] if "Giovanni" in a[1]]

            for aid, idx in acts["attack"]:
                d = calculate_damage(my_active, idx, my_bench, opp_active)
                if d > max_dmg: max_dmg = d; best_atk = aid

            if max_dmg >= opp_active_hp: return best_atk
            if giovanni and (max_dmg + 10) >= opp_active_hp: return giovanni[0][0]

        # 2. Forced Activate (Switch in new active)
        if acts["activate"]:
            if not my_active or my_active_hp == 0:
                best_act = acts["activate"][0][0]; best_score = -9999
                for aid, idx in acts["activate"]:
                    if idx < len(my_bench_raw):
                         b = my_bench_raw[idx]
                         if b:
                             name = get_card_name(b).lower()
                             score = get_card_hp(b)

                             # Prefer powered up mons
                             if not needs_energy(b): score += 500
                             elif len(get_card_energy(b)) > 0: score += 100

                             # Prefer EX
                             if "ex" in name: score += 50

                             if score > best_score: best_score = score; best_act = aid
                return best_act
            # If Activate is available but we have an active, it targets opponent bench (e.g. Sabrina/Pidgeot)
            # Handled in Supporters/Abilities phase usually, but if here, handle it?
            # Usually Activate(idx) for opponent is implicit in effect, but if explicitly actionable:
            return acts["activate"][0][0]

        # 3. Survival / Retreat
        if acts["retreat"] and my_active and my_active_hp > 0:
            # Retreat if active is low and we have a better option
            if my_active_hp <= 70:
                for b in my_bench:
                    if b and get_card_hp(b) > 70 and not needs_energy(b):
                         return acts["retreat"][0]

        # 4. Setup Phase

        # A. Evolve (High Priority)
        if acts["evolve"]: return acts["evolve"][0][0]

        # B. Place Active (Start of Game)
        if acts["place_active"]:
            best_active = acts["place_active"][0][0]; max_score = -1000
            for aid, name in acts["place_active"]:
                score = 0; n = name.lower()
                if "pikachu ex" in n: score += 200
                if "mewtwo ex" in n: score += 180
                if "starmie ex" in n: score += 180
                if "articuno ex" in n: score += 180
                if "moltres ex" in n: score += 180
                if "zapdos ex" in n: score += 180
                if "charizard ex" in n: score += 150
                if "venusaur ex" in n: score += 150
                if "kangaskhan" in n: score += 140
                if "farfetch" in n: score += 130
                if "ex" in n: score += 100
                if "pidgey" in n: score -= 50
                if "ralts" in n: score -= 50
                if score > max_score: max_score = score; best_active = aid
            return best_active

        # C. Place Basic on Bench
        if acts["place_basic"]:
            bench_count = len(my_bench)
            if bench_count < 3:
                best_bp = None; best_score = -9999
                for aid, name, _ in acts["place_basic"]:
                    score = 10; n = name.lower()
                    if "ex" in n: score += 50
                    if "pikachu" in n: score += 60
                    if "ralts" in n: score += 70
                    if "articuno" in n: score += 50
                    if "moltres" in n: score += 50

                    # Avoid empty bench
                    if bench_count == 0: score += 500

                    if score > best_score: best_score = score; best_bp = aid
                if best_bp: return best_bp

        # D. Abilities (Draw/Setup)
        if acts["ability"]:
            for aid, idx in acts["ability"]:
                user = my_active if idx == 0 else (my_bench_raw[idx-1] if idx-1 < 3 else None)
                if user:
                    n = get_card_name(user).lower()
                    # Greninja/Pidgeot are mostly free value
                    if "greninja" in n: return aid
                    if "pidgeot" in n: return aid
                    # Gardevoir: Only if needed
                    if "gardevoir" in n:
                         if needs_energy(my_active) or any(needs_energy(b) for b in my_bench): return aid
            # Default to using ability if available? Maybe risky if it discards.
            # But usually safe to check known cards.
            # For now, simplistic:
            return acts["ability"][0][0]

        # E. Play Supporters
        if acts["play_supporter"]:
            # Misty (Energy Acceleration)
            misty = [a for a in acts["play_supporter"] if "Misty" in a[1]]
            if misty:
                best_misty = None; best_score = -1
                # Targets: Active (0), Bench (1-3)
                targets = [(my_active, 0)] + [(b, i+1) for i, b in enumerate(my_bench_raw) if b]
                for t_card, t_idx in targets:
                    if not t_card: continue
                    name = get_card_name(t_card)
                    if "water" in get_energy_type(name):
                        score = 100
                        if "ex" in name.lower(): score += 50
                        if not needs_energy(t_card): score -= 80 # Don't overcharge
                        if t_idx == 0: score += 20 # Active priority

                        for aid, _, target_act in misty:
                            # Misty usually doesn't have a target index in regex if it's "Play(Misty)"
                            # But if it's "Play(Misty, 1)", it does.
                            # Simulator usually asks for target AFTER play? Or is it Action(Misty, Target)?
                            # Assuming targeted action is fully defined in legal actions.
                            if target_act == t_idx and score > best_score:
                                best_score = score; best_misty = aid
                if best_misty: return best_misty
                # If no target match found but Misty is legal (maybe non-targeted?), just play it
                if not best_misty and misty: return misty[0][0]

            # Research (Draw)
            research = [a for a in acts["play_supporter"] if "Research" in a[1]]
            if research and len(my_hand) <= 5: return research[0][0]

            # Sabrina (Disruption)
            sabrina = [a for a in acts["play_supporter"] if "Sabrina" in a[1]]
            if sabrina and opp_bench and opp_active_hp > 60: return sabrina[0][0]

        # F. Attach Energy
        if acts["attach_energy"]:
            best_attach = None; max_score = -1000
            for aid, type_str, pos in acts["attach_energy"]:
                score = 0
                target = my_active if pos == 0 else (my_bench_raw[pos-1] if pos-1 < 3 else None)
                if not target: continue

                t_name = get_card_name(target); t_type = get_energy_type(t_name)
                type_str_lower = type_str.lower()

                # Color Match Check
                match = (type_str_lower == t_type) or (t_type == "colorless")
                if not match: score -= 500

                if needs_energy(target):
                    score += 100
                    if pos == 0: score += 50 # Priority to active
                    if "ex" in t_name.lower(): score += 50
                    if "mewtwo" in t_name.lower(): score += 60
                else:
                    score -= 50

                if score > max_score: max_score = score; best_attach = aid

            if best_attach and max_score > 0: return best_attach

        # G. Play Items
        if acts["play_item"]:
            potion = [a for a in acts["play_item"] if "Potion" in a[1]]
            if potion:
                 # Use potion if active damaged but not dead
                 if my_active_hp > 0 and my_active_hp <= my_active_max_hp - 20: return potion[0][0]

            x_speed = [a for a in acts["play_item"] if "X Speed" in a[1]]
            if x_speed and my_active_hp <= 70: return x_speed[0][0]

            redcard = [a for a in acts["play_item"] if "Red Card" in a[1]]
            if redcard: return redcard[0][0] # Always good to disrupt?

            pokeball = [a for a in acts["play_item"] if "Ball" in a[1]]
            if pokeball: return pokeball[0][0]

        # 5. Attack (Final Action)
        if acts["attack"]:
            best_atk = acts["attack"][0][0]; max_score = -1
            for aid, idx in acts["attack"]:
                d = calculate_damage(my_active, idx, my_bench, opp_active)
                score = d

                # Check status effects
                text = ""
                if my_active_name.lower() in CARD_DB:
                     attacks = CARD_DB[my_active_name.lower()].get("attacks", [])
                     if idx < len(attacks): text = str(attacks[idx].get("text", ""))

                if "Asleep" in text: score += 15
                if "Paralyzed" in text: score += 20
                if "Confused" in text: score += 5

                if score > max_score: max_score = score; best_atk = aid
            return best_atk

        # 6. End Turn
        if acts["end"]: return acts["end"][0]

        return legal_actions[0]

    except Exception as e:
        logging.error(f"Error in play: {e}")
        return legal_actions[0]
