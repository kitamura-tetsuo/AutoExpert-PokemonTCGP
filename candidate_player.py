
import re
import random
import logging
from db_dump import CARD_DB

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', handlers=[
    logging.FileHandler("player.log", mode='w'),
    logging.StreamHandler()
])

def play(state, game):
    """
    Advanced Pokemon TCG Pocket Player (v30 - Optimized Logic)
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

        def get_retreat_cost(card_name):
            if not card_name: return 1
            n = card_name.lower()
            if n in CARD_DB:
                return CARD_DB[n].get("retreat", 1)
            # Fallback
            if "snorlax" in n or "onix" in n or "golem" in n: return 4
            if "ex" in n: return 2
            return 1

        def get_energy_type(card_name):
            if not card_name: return "colorless"
            n = card_name.lower()
            if n in CARD_DB:
                return CARD_DB[n].get("energy_type", "colorless").lower()
            # Fallback
            if "pikachu" in n or "zapdos" in n or "raichu" in n or "electrode" in n or "magneton" in n: return "lightning"
            if "mewtwo" in n or "gardevoir" in n or "gengar" in n or "abra" in n: return "psychic"
            if "starmie" in n or "greninja" in n or "articuno" in n or "blastoise" in n: return "water"
            if "charizard" in n or "moltres" in n or "arcanine" in n or "ninetales" in n: return "fire"
            if "venusaur" in n or "exeggutor" in n: return "grass"
            if "marowak" in n or "machamp" in n or "onix" in n or "golem" in n: return "fighting"
            if "dragonite" in n: return "dragon"
            if "melmetal" in n: return "metal"
            if "weavile" in n or "muk" in n or "arbok" in n: return "darkness"
            return "colorless"

        def calculate_damage(attacker_card, attack_idx, my_bench, opp_active_card=None, opp_bench_count=0):
            name = get_card_name(attacker_card)
            n_lower = name.lower()
            my_bench_len = len([b for b in my_bench if b])
            opp_energy_count = len(get_card_energy(opp_active_card)) if opp_active_card else 0

            damage = 0

            # --- Hardcoded Logic for Meta Cards ---

            # Pikachu ex: Circle Circuit (30 * Lightning Bench)
            if "pikachu ex" in n_lower and attack_idx == 0:
                lightning_bench = 0
                for b in my_bench:
                    if b:
                        b_name = get_card_name(b)
                        if "lightning" in get_energy_type(b_name): lightning_bench += 1
                return 30 * lightning_bench

            # Marowak ex: Bonemerang (80 * 2 flips -> Max 160)
            if "marowak ex" in n_lower and attack_idx == 0: return 160

            # Zapdos ex: Thunderous Kick (50 * 4 flips -> Max 200)
            if "zapdos ex" in n_lower:
                if attack_idx == 0: return 20 # Peck
                if attack_idx == 1: return 200 # Max potential

            # Moltres ex: Inferno Dance (0) / Heat Blast (70)
            if "moltres ex" in n_lower:
                if attack_idx == 0: return 0 # Setup
                if attack_idx == 1: return 70

            # Articuno ex: Ice Beam (40) / Blizzard (80)
            if "articuno ex" in n_lower:
                if attack_idx == 0: return 40
                if attack_idx == 1: return 80

            # Mewtwo ex: Psydrive (150) / Energy Ball (50)
            if "mewtwo ex" in n_lower:
                if attack_idx == 0: return 50
                if attack_idx == 1: return 150

            # Starmie ex: Hydro Splash (90)
            if "starmie ex" in n_lower and attack_idx == 0: return 90

            # Charizard ex: Slash (60) / Crimson Storm (200)
            if "charizard ex" in n_lower:
                if attack_idx == 0: return 60
                if attack_idx == 1: return 200

            # Blastoise ex: Hydro Pump (100+)
            if "blastoise ex" in n_lower:
                if attack_idx == 0: return 40
                if attack_idx == 1: return 160 # Assume max scaling

            # Venusaur ex: Razor Leaf (60) / Giant Bloom (100)
            if "venusaur ex" in n_lower:
                if attack_idx == 0: return 60
                if attack_idx == 1: return 100

            # Greninja: Mist Slash (60)
            if "greninja" in n_lower and "ex" not in n_lower and attack_idx == 0: return 60

            # Indeedee ex: Psychic (30 + 30*opp_energy)
            if "indeedee ex" in n_lower and attack_idx == 0: return 30 + (30 * opp_energy_count)

            # Cinccino: Do the Wave (30 * Bench)
            if "cinccino" in n_lower and attack_idx == 0: return 30 * my_bench_len

            # --- General Logic from DB ---
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
                         # Optimistic: assume all heads for max potential
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
                             if "your benched" in text: damage += (30 * my_bench_len) # Generic assumption
                             elif "opponent's benched" in text: damage += (20 * opp_bench_count)
                        elif "energy" in text:
                             if "opponent's active" in text: damage += (20 * opp_energy_count)

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

            # Hardcoded Requirements for Best Attack
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
            if "cinccino" in n_lower: return current_energy < 3
            if "machamp ex" in n_lower: return current_energy < 3

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
        opp_active_name = get_card_name(opp_active)

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

        # 0. Draw (Always first)
        if acts["draw"]: return acts["draw"][0]

        # 1. Lethal Check (Priority)
        giovanni = [a for a in acts["play_supporter"] if "Giovanni" in a[1]]

        # Calculate max damage available now
        current_max_dmg = 0
        current_best_atk = None
        if acts["attack"] and opp_active_hp > 0:
            for aid, idx in acts["attack"]:
                d = calculate_damage(my_active, idx, my_bench, opp_active, len(opp_bench))
                if d > current_max_dmg:
                    current_max_dmg = d
                    current_best_atk = aid

        if current_best_atk:
            if current_max_dmg >= opp_active_hp:
                return current_best_atk # LETHAL!

            # Check Giovanni for Lethal
            if giovanni and (current_max_dmg + 10) >= opp_active_hp:
                return giovanni[0][0]

        # 2. Setup (Evolve > Place Active > Place Bench)
        if acts["evolve"]: return acts["evolve"][0][0]

        if acts["place_active"]:
            # Pick best starter
            best_active = acts["place_active"][0][0]; max_score = -1000
            for aid, name in acts["place_active"]:
                score = 0; n = name.lower()
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
                if "pidgey" in n or "ralts" in n or "nidoran" in n: score -= 100
                if score > max_score: max_score = score; best_active = aid
            return best_active

        if acts["place_basic"]:
            bench_count = len(my_bench)
            # Fill bench to avoid donk (loss by no pokemon)
            must_place = (bench_count == 0)

            best_bp = None; best_score = -9999
            for aid, name, _ in acts["place_basic"]:
                score = 10; n = name.lower()
                if "ex" in n: score += 50
                if "pikachu" in n: score += 60 # Synergy
                if "ralts" in n: score += 70 # Gardevoir Setup
                if "articuno" in n: score += 50
                if "moltres" in n: score += 50
                if "zapdos" in n: score += 50
                if "greninja" in n: score += 50 # Mist Slash / Shuriken

                if must_place: score += 1000
                elif bench_count >= 3: score -= 50 # Don't overfill with junk

                if score > best_score: best_score = score; best_bp = aid

                if best_bp is not None: return best_bp

        # 3. Energy Attachment (Before Supporters/Abilities to ensure we use it)
        if acts["attach_energy"]:
            best_attach = None; max_score = -1000
            for aid, type_str, pos in acts["attach_energy"]:
                score = 0
                target = my_active if pos == 0 else (my_bench_raw[pos-1] if pos-1 < len(my_bench_raw) else None)
                if not target: continue

                t_name = get_card_name(target)
                t_type = get_energy_type(t_name)
                type_str_lower = type_str.lower()

                # Loose Type Match (e.g. "fire" in "fire energy")
                match = (t_type in type_str_lower) or (t_type == "colorless")

                if not match: score -= 500

                if needs_energy(target):
                    score += 100
                    if pos == 0: score += 60 # Priority to Active
                    if "ex" in t_name.lower(): score += 40
                else:
                    score -= 50 # Already full

                # Special case: Gardevoir helps attach from discard, so manual attach to others first?
                # Actually, attaching from hand is once per turn, so prioritize it heavily.

                if score > max_score: max_score = score; best_attach = aid

            if best_attach is not None and max_score > 0: return best_attach

        # 4. Abilities (Free value)
        if acts["ability"]:
            # Prioritize Greninja/Pidgeot
            for aid, idx, target in acts["ability"]:
                user = my_active if idx == 0 else (my_bench_raw[idx-1] if idx-1 < len(my_bench_raw) else None)
                if user:
                    n = get_card_name(user).lower()
                    if "greninja" in n: return aid # Water Shuriken
                    if "pidgeot" in n and opp_active_hp > 60: return aid # Drive Off
                    if "moltres ex" in n: return aid # Inferno Dance setup

            # Use Gardevoir if needed
            for aid, idx, target in acts["ability"]:
                user = my_active if idx == 0 else (my_bench_raw[idx-1] if idx-1 < len(my_bench_raw) else None)
                if user:
                    n = get_card_name(user).lower()
                    if "gardevoir" in n:
                        # Only if someone needs energy
                        if needs_energy(my_active) or any(needs_energy(b) for b in my_bench): return aid

            # Generic fallback for abilities
            return acts["ability"][0][0]

        # 5. Supporters
        if acts["play_supporter"]:
            # Misty
            misty = [a for a in acts["play_supporter"] if "Misty" in a[1]]
            if misty:
                best_misty = None; best_score = -1
                for aid, _, target_idx in misty:
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
                        else: score = -100

                    if score > best_score: best_score = score; best_misty = aid
                if best_misty is not None and best_score > 0: return best_misty

            # Research (Draw)
            research = [a for a in acts["play_supporter"] if "Research" in a[1]]
            if research:
                 if len(my_hand) <= 5: return research[0][0] # Avoid clogging

            # Sabrina
            sabrina = [a for a in acts["play_supporter"] if "Sabrina" in a[1]]
            if sabrina:
                # Use if Opp Active is strong and healthy
                if opp_active_hp > 70:
                    # Target logic: usually sabrina forces opponent to switch.
                    # If we can pick target (unlikely in some implementations, but check regex)
                    # Assuming we just play it and opponent chooses or random.
                    return sabrina[0][0]

            # Giovanni (if not used for lethal)
            if giovanni:
                 if "ex" in get_card_name(opp_active).lower() and opp_active_hp > 120:
                     return giovanni[0][0] # Chip damage on big boss

        # 6. Items
        if acts["play_item"]:
            potion = [a for a in acts["play_item"] if "Potion" in a[1]]
            if potion:
                 # Heal if Active has taken damage but isn't dead
                 if my_active_hp > 0 and my_active_hp <= my_active_max_hp - 20: return potion[0][0]

            x_speed = [a for a in acts["play_item"] if "X Speed" in a[1]]
            if x_speed and my_active_hp <= 70 and my_active_hp > 0:
                 # Check if bench has a better attacker
                 for b in my_bench:
                     if b and get_card_hp(b) > 70 and not needs_energy(b):
                         return x_speed[0][0]

            redcard = [a for a in acts["play_item"] if "Red Card" in a[1]]
            if redcard: return redcard[0][0]

            pokeball = [a for a in acts["play_item"] if "Ball" in a[1]]
            if pokeball: return pokeball[0][0]

        # 7. Retreat (Strategic)
        if acts["retreat"] and my_active and my_active_hp > 0:
            if my_active_hp <= 70: # Danger Zone
                # Only retreat if we have a backup
                for b in my_bench:
                     if b and get_card_hp(b) > 60 and (not needs_energy(b) or get_card_name(b) == "Mewtwo ex"):
                         return acts["retreat"][0]

        # 8. Activate (Switch - Forced or Item)
        if acts["activate"]:
            # Priority: Charged EX > Charged Basic > High HP
            best_act = acts["activate"][0][0]; best_score = -9999
            for aid, idx in acts["activate"]:
                if idx < len(my_bench_raw):
                        b = my_bench_raw[idx]
                        if b:
                            name = get_card_name(b).lower()
                            score = get_card_hp(b)
                            if not needs_energy(b): score += 1000 # Fully charged!
                            elif len(get_card_energy(b)) > 0: score += 200
                            if "ex" in name: score += 100
                            if score > best_score: best_score = score; best_act = aid
            return best_act

        # 9. Attack (Non-Lethal)
        if acts["attack"]:
            # Already calculated best attack for lethal check
            if current_best_atk:
                return current_best_atk
            return acts["attack"][0][0]

        # 10. End Turn
        if acts["end"]: return acts["end"][0]

        # Fallback
        return legal_actions[0]

    except Exception as e:
        logging.error(f"Error in play: {e}")
        return legal_actions[0]
