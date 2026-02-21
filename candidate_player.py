
import re
import random
import logging
from db_dump import CARD_DB

# Setup logging
logging.basicConfig(filename='player.log', level=logging.INFO, filemode='w', format='%(asctime)s - %(message)s')

def play(state, game):
    """
    Advanced Pokemon TCG Pocket Player (v31 - Aggressive Refinement)
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

        def get_pokemon_energy_type(card_name):
            if not card_name: return "colorless"
            n = card_name.lower()
            if n in CARD_DB:
                return CARD_DB[n].get("energy_type", "colorless").lower()
            # Fallback based on name keywords
            if "pikachu" in n or "zapdos" in n or "raichu" in n or "electrode" in n or "magneton" in n or "blitzle" in n or "zebra" in n or "mareep" in n: return "lightning"
            if "mewtwo" in n or "gardevoir" in n or "ralts" in n or "kirlia" in n or "abra" in n or "kadabra" in n or "alakazam" in n or "gastly" in n or "haunter" in n or "gengar" in n: return "psychic"
            if "starmie" in n or "greninja" in n or "articuno" in n or "squirtle" in n or "wartortle" in n or "blastoise" in n or "lapras" in n or "seaking" in n or "goldeen" in n: return "water"
            if "charizard" in n or "moltres" in n or "charmander" in n or "charmeleon" in n or "vulpix" in n or "ninetales" in n or "magmar" in n or "ponyta" in n or "rapidash" in n: return "fire"
            if "venusaur" in n or "bulbasaur" in n or "ivysaur" in n or "exeggutor" in n or "exeggcute" in n or "oddish" in n or "gloom" in n or "vileplume" in n or "pinsir" in n or "scyther" in n: return "grass"
            if "marowak" in n or "machamp" in n or "machop" in n or "machoke" in n or "cubone" in n or "hitmonlee" in n or "hitmonchan" in n or "onix" in n or "geodude" in n or "graveler" in n or "golem" in n or "rhyhorn" in n or "rhydon" in n: return "fighting"
            if "dragonite" in n or "dratini" in n or "dragonair" in n: return "dragon"
            if "melmetal" in n or "meltan" in n or "magnemite" in n or "magneton" in n: return "metal"
            if "weavile" in n or "muk" in n or "grimer" in n or "koffing" in n or "weezing" in n or "ekans" in n or "arbok" in n or "nidoran" in n or "nidorina" in n or "nidorino" in n or "nidoking" in n or "nidoqueen" in n: return "darkness"
            return "colorless"

        def calculate_damage(attacker_card, attack_idx, my_bench, opp_active_card=None, opp_bench_count=0):
            if not attacker_card: return 0
            name = get_card_name(attacker_card)
            n_lower = name.lower()
            my_bench_len = len([b for b in my_bench if b])
            opp_energy_count = len(get_card_energy(opp_active_card)) if opp_active_card else 0

            # Helper to count energy types
            def count_energy_on_bench(type_str):
                count = 0
                for b in my_bench:
                    if b:
                        b_name = get_card_name(b)
                        if type_str in get_pokemon_energy_type(b_name): count += 1
                return count

            damage = 0

            # --- Specific Hardcoded Logic for Meta Cards ---

            # Mewtwo ex
            if "mewtwo ex" in n_lower:
                if attack_idx == 0: return 50
                if attack_idx == 1: return 150 # Psydrive

            # Pikachu ex
            elif "pikachu ex" in n_lower:
                if attack_idx == 0:
                    return 30 * count_energy_on_bench("lightning") # Circle Circuit

            # Charizard ex
            elif "charizard ex" in n_lower:
                if attack_idx == 0: return 60
                if attack_idx == 1: return 200 # Crimson Storm

            # Starmie ex
            elif "starmie ex" in n_lower:
                if attack_idx == 0: return 90 # Hydro Splash

            # Articuno ex
            elif "articuno ex" in n_lower:
                if attack_idx == 0: return 40
                if attack_idx == 1: return 80 # Blizzard (also bench damage, but active is 80)

            # Moltres ex
            elif "moltres ex" in n_lower:
                if attack_idx == 0: return 0 # Energy accel
                if attack_idx == 1: return 70

            # Zapdos ex
            elif "zapdos ex" in n_lower:
                if attack_idx == 0: return 0 # Peck usually? Or 20
                if attack_idx == 1: return 100 # Random Spark (flip 4 coins, avg 2 heads = 100)

            # Venusaur ex
            elif "venusaur ex" in n_lower:
                if attack_idx == 0: return 60
                if attack_idx == 1: return 100 # Giant Bloom + Heal

            # Blastoise ex
            elif "blastoise ex" in n_lower:
                if attack_idx == 0: return 40
                if attack_idx == 1: return 140 # Hydro Bazooka (100 + 40 extra energy likely)

            # Marowak ex
            elif "marowak ex" in n_lower:
                if attack_idx == 0: return 160 # Bonemerang (2 flips * 80). Optimistic for lethal check.

            # Greninja (non-ex)
            elif "greninja" in n_lower and "ex" not in n_lower:
                if attack_idx == 0: return 60 # Mist Slash

            # Indeedee ex
            elif "indeedee ex" in n_lower:
                 if attack_idx == 0: return 30 + (30 * opp_energy_count)

            # Cinccino
            elif "cinccino" in n_lower:
                if attack_idx == 0: return 30 * my_bench_len

            # --- General Logic from DB ---
            if n_lower in CARD_DB and "attacks" in CARD_DB[n_lower]:
                attacks_db = CARD_DB[n_lower]["attacks"]
                if attack_idx < len(attacks_db):
                    atk = attacks_db[attack_idx]
                    base = atk.get("dmg", 0)
                    text_val = atk.get("text")
                    text = text_val.lower() if text_val else ""
                    damage = base

                    # Coin Flips
                    if atk.get("coin_flips"):
                         if "damage for each heads" in text:
                             m = re.search(r"(\d+) damage for each heads", text)
                             dmg_per_head = int(m.group(1)) if m else base
                             damage = (atk["coin_flips"] * dmg_per_head) * 0.5
                         elif "more damage" in text and "heads" in text:
                             m = re.search(r"(\d+) more damage", text)
                             plus = int(m.group(1)) if m else 0
                             damage += (plus * 0.5)

                    elif atk.get("scaling"):
                        if "bench" in text:
                             if "your benched" in text: damage += (30 * my_bench_len) # Generic guess
                             elif "opponent's benched" in text: damage += (20 * opp_bench_count)
                        elif "energy" in text:
                             if "opponent's active" in text: damage += (20 * opp_energy_count)

                    # Status Effects Bonus
                    if "asleep" in text or "paralyzed" in text or "confused" in text:
                        damage += 15 # Bonus for status

                    return int(damage)

            # Fallback to object attribute
            attacks_obj = getattr(attacker_card, "attacks", [])
            if attack_idx < len(attacks_obj):
                atk_obj = attacks_obj[attack_idx]
                fixed = getattr(atk_obj, "fixed_damage", 0)
                if fixed > 0: damage = fixed
                else:
                    dmg = getattr(atk_obj, "damage", 0)
                    if dmg > 0: damage = dmg
            return damage

        def get_energy_cost(card_obj, attack_idx=None):
            if not card_obj: return 99
            name = get_card_name(card_obj).lower()

            # Hardcoded max costs for main attacks
            if "mewtwo ex" in name: return 4 # Psydrive
            if "pikachu ex" in name: return 2 # Circle Circuit
            if "charizard ex" in name: return 4 # Crimson Storm
            if "starmie ex" in name: return 2 # Hydro Splash
            if "articuno ex" in name: return 3 # Blizzard
            if "moltres ex" in name: return 3
            if "zapdos ex" in name: return 3
            if "venusaur ex" in name: return 4
            if "blastoise ex" in name: return 3
            if "marowak ex" in name: return 2
            if "greninja" in name and "ex" not in name: return 2
            if "cinccino" in name: return 2 # Do the Wave

            # General heuristic
            if name in CARD_DB and "attacks" in CARD_DB[name]:
                attacks = CARD_DB[name]["attacks"]
                if not attacks: return 99
                if attack_idx is not None and attack_idx < len(attacks):
                    return len(attacks[attack_idx].get("cost", []))
                # Return max cost
                max_cost = 0
                for atk in attacks:
                    c = len(atk.get("cost", []))
                    if c > max_cost: max_cost = c
                return max_cost

            return 2 # Default fallback

        def needs_energy(card_obj):
            if not card_obj: return False
            current = len(get_card_energy(card_obj))
            req = get_energy_cost(card_obj)
            return current < req

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
        opp_active_max_hp = get_card_max_hp(opp_active) if opp_active else 0

        # Action Categories
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
        re_ability = re.compile(r"UseAbility\((\d+)(?:, (\d+))?\)")
        re_activate = re.compile(r"Activate\((\d+)\)")
        re_item_support = re.compile(r"(UseItem|UseSupporter)\((?:Some\()?(.*?)\)?(?:, (\d+))?\)")

        supporters = ["Research", "Sabrina", "Giovanni", "Erika", "Misty", "Blaine", "Koga", "Lt. Surge", "Brock", "Copycat", "Lisia", "Cyrus", "Mars", "Red", "Guzma", "Judge", "Acerola", "Hau", "Bill", "Professor's Research"]

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
                         m = re_item_support.search(aname)
                         if m:
                             card_name = m.group(2).replace(")", "")
                             target = int(m.group(3)) if m.group(3) else -1
                             if any(s in card_name for s in supporters): acts["play_supporter"].append((aid, card_name, target))
                             else: acts["play_item"].append((aid, card_name, target))

            elif aname.startswith("UseAbility"):
                m = re_ability.search(aname)
                if m:
                    idx = int(m.group(1))
                    target = int(m.group(2)) if m.group(2) else -1
                    acts["ability"].append((aid, idx, target))

            elif aname.startswith("Retreat"): acts["retreat"].append(aid)

            elif aname.startswith("Activate"):
                m = re_activate.search(aname)
                if m: acts["activate"].append((aid, int(m.group(1))))

            elif "Stadium" in aname: acts["stadium"].append(aid)

        # --- 3. Strategic Decision Making ---

        # 0. Always Draw
        if acts["draw"]: return acts["draw"][0]

        # 1. Lethal Calculation (Priority High)
        giovanni = [a for a in acts["play_supporter"] if "Giovanni" in a[1]]

        # Check Attacks
        if acts["attack"] and opp_active_hp > 0:
            best_attack_aid = None
            max_dmg = 0

            for aid, idx in acts["attack"]:
                dmg = calculate_damage(my_active, idx, my_bench, opp_active, len(opp_bench))
                if dmg > max_dmg:
                    max_dmg = dmg
                    best_attack_aid = aid

            # Simple Lethal
            if max_dmg >= opp_active_hp:
                return best_attack_aid

            # Giovanni Lethal
            if giovanni and (max_dmg + 10 >= opp_active_hp):
                return giovanni[0][0]

        # 2. Setup (Evolve, Bench, Attach, Abilities)

        # Evolve: Almost always good
        if acts["evolve"]: return acts["evolve"][0][0]

        # Place Active (Start of Game)
        if acts["place_active"]:
            # Pick best starter: High HP or Fast attacker (Pikachu, Starmie)
            best_aid = acts["place_active"][0][0]
            best_score = -1000
            for aid, name in acts["place_active"]:
                score = 0
                n = name.lower()
                if "pikachu" in n and "ex" in n: score += 100
                if "starmie" in n and "ex" in n: score += 100
                if "mewtwo" in n and "ex" in n: score += 80 # Needs energy ramp
                if "articuno" in n and "ex" in n: score += 90
                if "charizard" in n and "ex" in n: score += 70 # Slow
                if "kangaskhan" in n: score += 60 # Good tank
                if "hitmonchan" in n: score += 60
                if "farfetch" in n: score += 50

                # Avoid weak basics if possible
                if "ralts" in n: score -= 20
                if "magikarp" in n: score -= 50

                if score > best_score:
                    best_score = score
                    best_aid = aid
            return best_aid

        # Place Basic (Bench)
        if acts["place_basic"]:
            bench_count = len(my_bench)
            should_bench = False
            # Aggressive bench filling to prevent donks and prepare attackers
            if bench_count < 3: should_bench = True

            if should_bench or len(acts["place_basic"]) > 0:
                best_aid = None
                best_score = -1000

                for aid, name, _ in acts["place_basic"]:
                    score = 0
                    n = name.lower()

                    if bench_count == 0: score += 1000 # Critical to place something
                    elif bench_count < 2: score += 200 # Important backup

                    if "ex" in n: score += 50
                    if "ralts" in n: score += 60 # Gardevoir engine
                    if "pikachu" in n: score += 50
                    if "pidgey" in n: score += 40 # Pidgeot engine
                    if "articuno" in n: score += 40
                    if "moltres" in n: score += 40
                    if "zapdos" in n: score += 40

                    if score > best_score:
                        best_score = score
                        best_aid = aid

                if best_aid and best_score > 0: return best_aid
                # Usually always bench unless negative score?
                if best_aid and bench_count < 3: return best_aid

        # Attach Energy (Prioritized before Supporters to avoid discard risk)
        if acts["attach_energy"]:
            # Prioritize Active if it needs energy. Then Bench EX.
            best_attach = None
            best_score = -1000

            for aid, type_str, pos in acts["attach_energy"]:
                score = 0
                target = my_active if pos == 0 else (my_bench_raw[pos-1] if pos-1 < len(my_bench_raw) else None)
                if not target: continue

                t_name = get_card_name(target)
                t_type = get_pokemon_energy_type(t_name)

                # Match type
                is_match = (type_str.lower() == t_type) or (t_type == "colorless")
                if not is_match: score -= 500

                needed = needs_energy(target)

                if needed:
                    score += 100
                    if pos == 0: score += 50 # Active priority
                    if "ex" in t_name.lower(): score += 30
                else:
                    score -= 50 # Overcharge
                    # Exception: Mewtwo ex / Charizard ex might need extra for discard cost mechanics (though needs_energy tries to handle this)

                if score > best_score:
                    best_score = score
                    best_attach = aid

            if best_attach and best_score > 0: return best_attach

        # Abilities (Greninja, Pidgeot, etc.)
        if acts["ability"]:
            for aid, idx, target in acts["ability"]:
                # Identify ability user
                user_card = my_active if idx == 0 else (my_bench_raw[idx-1] if idx-1 < len(my_bench_raw) else None)
                if user_card:
                    n = get_card_name(user_card).lower()
                    if "greninja" in n: return aid # Water Shuriken usually free damage
                    if "pidgeot" in n:
                         # Gust effect. Use if Opponent Active is not KOable but Benched is?
                         # Or just to disrupt.
                         # Simple heuristic: Use if we can't KO active.
                         if acts["attack"]:
                             # Check if we KO active
                             d = 0
                             for _, a_idx in acts["attack"]:
                                 d = max(d, calculate_damage(my_active, a_idx, my_bench, opp_active, len(opp_bench)))
                             if d < opp_active_hp: return aid # Gust something else
                    if "gardevoir" in n:
                        # Energy accel. Always use if someone needs energy.
                        if needs_energy(my_active) or any(needs_energy(b) for b in my_bench): return aid

            # Default to using ability if it's not harmful (most aren't)
            return acts["ability"][0][0]

        # Supporters
        if acts["play_supporter"]:
            # Misty
            misty = [a for a in acts["play_supporter"] if "Misty" in a[1]]
            if misty:
                # Target best water type
                best_misty = None; best_val = -1
                for aid, _, target_idx in misty:
                    t_card = None
                    if target_idx == 0: t_card = my_active
                    elif target_idx > 0:
                        b_idx = target_idx - 1
                        if b_idx < len(my_bench_raw): t_card = my_bench_raw[b_idx]

                    if t_card:
                        nm = get_card_name(t_card)
                        if "water" in get_pokemon_energy_type(nm):
                            val = 10
                            if needs_energy(t_card): val += 20
                            if "ex" in nm.lower(): val += 10
                            if target_idx == 0: val += 5 # Priority active
                            if val > best_val:
                                best_val = val; best_misty = aid
                if best_misty and best_val > 10: return best_misty

            # Research
            research = [a for a in acts["play_supporter"] if "Research" in a[1]]
            if research:
                 if len(my_hand) <= 5: return research[0][0] # Increased threshold

            # Sabrina
            sabrina = [a for a in acts["play_supporter"] if "Sabrina" in a[1]]
            if sabrina:
                # Use if opponent active is healthy and strong
                if opp_active_hp > 80: return sabrina[0][0]

            # Giovanni (Chip damage if not lethal)
            if giovanni:
                 if opp_active_hp > 0: return giovanni[0][0]

        # Items
        if acts["play_item"]:
            potion = [a for a in acts["play_item"] if "Potion" in a[1]]
            if potion:
                # Heal if damaged significantly
                if my_active_hp > 0 and (my_active_max_hp - my_active_hp) >= 20:
                     return potion[0][0]

            xspeed = [a for a in acts["play_item"] if "X Speed" in a[1]]
            if xspeed:
                # Use if we want to retreat but lack energy? Or just reduce cost.
                # Heuristic: If we are active and have high retreat cost.
                # Simplified: Use if active
                return xspeed[0][0]

            redcard = [a for a in acts["play_item"] if "Red Card" in a[1]]
            if redcard:
                return redcard[0][0]

            balls = [a for a in acts["play_item"] if "Ball" in a[1]]
            if balls: return balls[0][0]

        # Retreat
        if acts["retreat"] and my_active and my_active_hp > 0:
            # Retreat if active is dying AND we have a backup
            damage_threat = 70 # Increased threshold
            if my_active_hp <= damage_threat:
                # Do we have a charged benched mon?
                for b in my_bench:
                     if b and not needs_energy(b):
                         return acts["retreat"][0]

        # Activate (Switch due to KO or effect)
        if acts["activate"]:
            best_act = acts["activate"][0][0]
            best_score = -1000
            for aid, idx in acts["activate"]:
                if idx < len(my_bench_raw):
                    b = my_bench_raw[idx]
                    if b:
                        score = 0
                        if not needs_energy(b): score += 100
                        if get_card_hp(b) > 80: score += 50
                        if "ex" in get_card_name(b).lower(): score += 20
                        if score > best_score:
                            best_score = score
                            best_act = aid
            return best_act

        # Attack (Best Damage)
        if acts["attack"]:
            best_attack = acts["attack"][0][0]
            max_dmg = -1
            for aid, idx in acts["attack"]:
                d = calculate_damage(my_active, idx, my_bench, opp_active, len(opp_bench))
                if d > max_dmg:
                    max_dmg = d
                    best_attack = aid
            return best_attack

        # End Turn
        if acts["end"]: return acts["end"][0]

        return legal_actions[0]

    except Exception as e:
        logging.error(f"Error in play: {e}")
        return legal_actions[0]
