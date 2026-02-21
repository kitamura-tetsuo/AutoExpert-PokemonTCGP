
import re
import random
import logging
from db_dump import CARD_DB

# Setup logging
logging.basicConfig(filename='player.log', level=logging.INFO, filemode='w', format='%(asctime)s - %(message)s')

def play(state, game):
    """
    Advanced Pokemon TCG Pocket Player (v20 - Optimized Logic)
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
            # Fallback
            if "pikachu" in n or "zapdos" in n or "raichu" in n: return "lightning"
            if "mewtwo" in n or "gardevoir" in n: return "psychic"
            if "starmie" in n or "greninja" in n or "articuno" in n: return "water"
            if "charizard" in n or "moltres" in n: return "fire"
            if "venusaur" in n: return "grass"
            if "marowak" in n or "machamp" in n: return "fighting"
            if "dragonite" in n: return "dragon"
            if "melmetal" in n: return "metal"
            if "weavile" in n or "muk" in n: return "darkness"
            return "colorless"

        def calculate_damage(attacker_card, attack_idx, my_bench, opp_active_card=None, opp_bench_count=0):
            name = get_card_name(attacker_card)
            n_lower = name.lower()
            my_bench_len = len([b for b in my_bench if b])
            opp_energy_count = len(get_card_energy(opp_active_card)) if opp_active_card else 0

            damage = 0

            # Special Cases (Hardcoded for accuracy)
            if "marowak ex" in n_lower and attack_idx == 0: return 160 # Max potential (2 heads * 80)
            if "pikachu ex" in n_lower and attack_idx == 0:
                lightning_bench = 0
                for b in my_bench:
                    if b:
                        b_name = get_card_name(b)
                        if "lightning" in get_energy_type(b_name): lightning_bench += 1
                return 30 * lightning_bench
            if "indeedee ex" in n_lower and attack_idx == 0: return 30 + (30 * opp_energy_count)
            if "cinccino" in n_lower and attack_idx == 0: return 30 * my_bench_len
            if "greninja" in n_lower and "ex" not in n_lower and attack_idx == 0: return 60
            if "mewtwo ex" in n_lower:
                if attack_idx == 0: return 50
                if attack_idx == 1: return 150
            if "starmie ex" in n_lower and attack_idx == 0: return 90
            if "articuno ex" in n_lower:
                if attack_idx == 0: return 40
                if attack_idx == 1: return 80

            # General Logic from DB
            if n_lower in CARD_DB and "attacks" in CARD_DB[n_lower]:
                attacks_db = CARD_DB[n_lower]["attacks"]
                if attack_idx < len(attacks_db):
                    atk = attacks_db[attack_idx]
                    base = atk.get("dmg", 0)
                    text_val = atk.get("text")
                    text = text_val.lower() if text_val else ""
                    damage = base

                    # Scaling / Coin Flips
                    if atk.get("coin_flips"):
                         # Optimistic: assume heads
                         if "damage for each heads" in text:
                             m = re.search(r"(\d+) damage for each heads", text)
                             dmg_per_head = int(m.group(1)) if m else base
                             damage = atk["coin_flips"] * dmg_per_head
                         elif "more damage" in text:
                             m = re.search(r"(\d+) more damage", text)
                             plus = int(m.group(1)) if m else 0
                             damage += plus

                    elif atk.get("scaling"):
                        if "bench" in text:
                             if "your benched" in text: damage += (30 * my_bench_len) # Generic assumption, usually 20 or 30
                             elif "opponent's benched" in text: damage += (20 * opp_bench_count) # Estimate
                        elif "energy" in text:
                             if "opponent's active" in text: damage += (20 * opp_energy_count) # Estimate

                    return damage

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

        def needs_energy(card_obj):
            if not card_obj: return False
            name = get_card_name(card_obj)
            current_energy = len(get_card_energy(card_obj))
            n_lower = name.lower()

            # Hardcoded Best Attack thresholds
            if "mewtwo ex" in n_lower: return current_energy < 4 # Needs 4 for 150
            if "charizard ex" in n_lower: return current_energy < 4 # Needs 4 for 200
            if "venusaur ex" in n_lower: return current_energy < 4
            if "blastoise ex" in n_lower: return current_energy < 3
            if "pikachu ex" in n_lower: return current_energy < 2
            if "starmie ex" in n_lower: return current_energy < 2
            if "marowak ex" in n_lower: return current_energy < 2
            if "articuno ex" in n_lower: return current_energy < 3
            if "moltres ex" in n_lower: return current_energy < 3
            if "zapdos ex" in n_lower: return current_energy < 3
            if "greninja" in n_lower and "ex" not in n_lower: return current_energy < 2
            if "cinccino" in n_lower: return current_energy < 3 # Usually 2 or 3

            # General DB check
            if n_lower in CARD_DB:
                attacks = CARD_DB[n_lower].get("attacks", [])
                if not attacks: return False
                max_cost = 0
                for atk in attacks:
                    cost_len = len(atk.get("cost", []))
                    if cost_len > max_cost: max_cost = cost_len
                return current_energy < max_cost

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
        re_ability = re.compile(r"UseAbility\((\d+)(?:, (\d+))?\)") # Handle potential target index
        re_activate = re.compile(r"Activate\((\d+)\)")
        re_item_support = re.compile(r"(UseItem|UseSupporter)\((?:Some\()?(.*?)\)?(?:, (\d+))?\)")

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

        # --- 3. Strategic Execution ---

        # 0. Draw
        if acts["draw"]: return acts["draw"][0]

        # 1. Lethal Check (Priority)
        giovanni = [a for a in acts["play_supporter"] if "Giovanni" in a[1]]

        if acts["attack"] and opp_active_hp > 0:
            max_dmg = 0; best_atk = acts["attack"][0][0]

            for aid, idx in acts["attack"]:
                d = calculate_damage(my_active, idx, my_bench, opp_active, len(opp_bench))
                if d > max_dmg: max_dmg = d; best_atk = aid

            if max_dmg >= opp_active_hp: return best_atk

            # Use Giovanni if it secures Lethal
            if giovanni and (max_dmg + 10) >= opp_active_hp: return giovanni[0][0]

        # 2. Setup Phase (Evolve, Place, Abilities, Supporters)

        # Evolve (Always good usually)
        if acts["evolve"]: return acts["evolve"][0][0]

        # Place Active (Start of Game)
        if acts["place_active"]:
            best_active = acts["place_active"][0][0]; max_score = -1000
            for aid, name in acts["place_active"]:
                score = 0; n = name.lower()
                # Prioritize fast/strong EX
                if "pikachu ex" in n: score += 500
                if "starmie ex" in n: score += 500
                if "mewtwo ex" in n: score += 450
                if "articuno ex" in n: score += 450
                if "marowak ex" in n: score += 400
                if "zapdos ex" in n: score += 400
                if "moltres ex" in n: score += 400
                if "kangaskhan" in n: score += 300
                if "farfetch" in n: score += 250
                if "ex" in n: score += 200

                # Penalize weak setup mons
                if "pidgey" in n or "ralts" in n or "nidoran" in n: score -= 100

                if score > max_score: max_score = score; best_active = aid
            return best_active

        # Place Basic on Bench
        if acts["place_basic"]:
            bench_count = len(my_bench)
            # Fill bench to at least 1-2 to avoid donk, max 3
            if bench_count < 3:
                best_bp = None; best_score = -9999
                for aid, name, _ in acts["place_basic"]:
                    score = 10; n = name.lower()
                    if "ex" in n: score += 50
                    if "pikachu" in n: score += 60 # Synergy
                    if "ralts" in n: score += 70 # Setup for Gardevoir
                    if "articuno" in n: score += 50
                    if "moltres" in n: score += 50
                    if "zapdos" in n: score += 50

                    # If empty bench, desperate need to place anything
                    if bench_count == 0: score += 1000

                    if score > best_score: best_score = score; best_bp = aid
                if best_bp: return best_bp

        # Abilities
        if acts["ability"]:
            for aid, idx, target in acts["ability"]:
                user = my_active if idx == 0 else (my_bench_raw[idx-1] if idx-1 < len(my_bench_raw) else None)
                if user:
                    n = get_card_name(user).lower()
                    # Free value abilities
                    if "greninja" in n: return aid
                    if "pidgeot" in n:
                        # Use only if opponent is healthy to disrupt
                        if opp_active_hp > 60: return aid
                    if "gardevoir" in n:
                        # Only if someone needs energy
                        if needs_energy(my_active) or any(needs_energy(b) for b in my_bench): return aid

            # Default: use if available (often safe)
            return acts["ability"][0][0]

        # Supporters
        if acts["play_supporter"]:
            # Misty
            misty = [a for a in acts["play_supporter"] if "Misty" in a[1]]
            if misty:
                best_misty = None; best_score = -1
                for aid, _, target_idx in misty:
                    # Target might be -1 if not parsed, but usually Misty targets
                    # If target_idx is -1, it might be untargeted or we need to look at arguments
                    # Assuming we pick the best target if multiple actions exist

                    # Logic: Find Water pokemon needing energy
                    t_card = None
                    if target_idx == 0: t_card = my_active
                    elif target_idx > 0 and (target_idx-1) < len(my_bench_raw): t_card = my_bench_raw[target_idx-1]

                    score = 0
                    if t_card:
                        name = get_card_name(t_card)
                        if "water" in get_energy_type(name):
                             score = 100
                             if needs_energy(t_card): score += 50
                             if target_idx == 0: score += 20
                        else:
                             score = -100 # Don't waste Misty on non-water
                    else:
                        # If target_idx is -1, maybe it's random/auto? Use with caution.
                        score = 10

                    if score > best_score: best_score = score; best_misty = aid

                if best_misty and best_score > 0: return best_misty

            # Research
            research = [a for a in acts["play_supporter"] if "Research" in a[1]]
            if research and len(my_hand) <= 5: return research[0][0]

            # Sabrina
            sabrina = [a for a in acts["play_supporter"] if "Sabrina" in a[1]]
            if sabrina:
                # Use if opponent active is strong/healthy (>60 HP) or we can't kill it
                if opp_active_hp > 60: return sabrina[0][0]

            # Giovanni (if not used for lethal)
            if giovanni:
                 # Use if opponent is EX and healthy to chip damage?
                 if "ex" in get_card_name(opp_active).lower() and opp_active_hp > 100:
                     return giovanni[0][0]

        # Attach Energy
        if acts["attach_energy"]:
            best_attach = None; max_score = -1000
            for aid, type_str, pos in acts["attach_energy"]:
                score = 0
                target = my_active if pos == 0 else (my_bench_raw[pos-1] if pos-1 < len(my_bench_raw) else None)
                if not target: continue

                t_name = get_card_name(target)
                t_type = get_energy_type(t_name)
                type_str_lower = type_str.lower()

                # Strict Type Match (unless Colorless pokemon)
                match = (type_str_lower == t_type) or (t_type == "colorless")
                if not match: score -= 500

                if needs_energy(target):
                    score += 100
                    if pos == 0: score += 60 # Priority to active
                    if "ex" in t_name.lower(): score += 40
                else:
                    score -= 50 # Already full

                if score > max_score: max_score = score; best_attach = aid

            if best_attach and max_score > 0: return best_attach

        # Items
        if acts["play_item"]:
            potion = [a for a in acts["play_item"] if "Potion" in a[1]]
            if potion:
                 if my_active_hp > 0 and my_active_hp <= my_active_max_hp - 20: return potion[0][0]

            x_speed = [a for a in acts["play_item"] if "X Speed" in a[1]]
            if x_speed and my_active_hp <= 70: return x_speed[0][0] # Retreat helper

            redcard = [a for a in acts["play_item"] if "Red Card" in a[1]]
            if redcard: return redcard[0][0]

            pokeball = [a for a in acts["play_item"] if "Ball" in a[1]]
            if pokeball: return pokeball[0][0]

        # Retreat
        if acts["retreat"] and my_active and my_active_hp > 0:
            if my_active_hp <= 60: # Threshold
                # Check if we have a better bench option
                for b in my_bench:
                     if b and get_card_hp(b) > 60 and not needs_energy(b):
                         return acts["retreat"][0]

        # Activate (Switch)
        if acts["activate"]:
            # If we have no active (hp=0 or None), we MUST choose one
            # The simulator forces this usually, but if we have choice:
            if not my_active or my_active_hp == 0:
                best_act = acts["activate"][0][0]; best_score = -9999
                for aid, idx in acts["activate"]:
                    if idx < len(my_bench_raw):
                         b = my_bench_raw[idx]
                         if b:
                             name = get_card_name(b).lower()
                             score = get_card_hp(b)
                             if not needs_energy(b): score += 500 # Charged
                             elif len(get_card_energy(b)) > 0: score += 100
                             if "ex" in name: score += 50
                             if score > best_score: best_score = score; best_act = aid
                return best_act
            else:
                # Switch caused by our own effect (e.g. escape rope / switch)
                return acts["activate"][0][0]

        # Attack
        if acts["attack"]:
            best_atk = acts["attack"][0][0]; max_score = -1
            for aid, idx in acts["attack"]:
                d = calculate_damage(my_active, idx, my_bench, opp_active, len(opp_bench))
                score = d
                # Status checks
                text = ""
                if my_active_name.lower() in CARD_DB:
                     attacks = CARD_DB[my_active_name.lower()].get("attacks", [])
                     if idx < len(attacks): text = str(attacks[idx].get("text", ""))
                if "Asleep" in text: score += 10
                if "Paralyzed" in text: score += 15
                if "Confused" in text: score += 5

                if score > max_score: max_score = score; best_atk = aid
            return best_atk

        # End Turn
        if acts["end"]: return acts["end"][0]

        # Fallback
        return legal_actions[0]

    except Exception as e:
        logging.error(f"Error in play: {e}")
        return legal_actions[0]
