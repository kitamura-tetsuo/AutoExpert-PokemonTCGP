
import re
import random
import logging
from db_dump import CARD_DB

# Setup logging
logging.basicConfig(filename='player.log', level=logging.INFO, filemode='w', format='%(asctime)s - %(message)s')

# Local DB overrides or additions
LOCAL_CARD_DB = {
    "indeedee ex": {"energy_type": "Psychic", "attacks": [{"dmg": 30, "text": "30+30 per opp energy", "scaling": True}]},
    "greninja": {"energy_type": "Water", "attacks": [{"dmg": 60}]},
    "starmie ex": {"energy_type": "Water", "attacks": [{"dmg": 90}]},
    "pikachu ex": {"energy_type": "Lightning", "attacks": [{"dmg": 30, "text": "30 per lightning bench", "scaling": True}]},
    "mewtwo ex": {"energy_type": "Psychic", "attacks": [{"dmg": 50}, {"dmg": 150}]},
    "charizard ex": {"energy_type": "Fire", "attacks": [{"dmg": 60}, {"dmg": 200}]},
    "articuno ex": {"energy_type": "Water", "attacks": [{"dmg": 40}, {"dmg": 80, "text": "10 to bench"}]},
    "moltres ex": {"energy_type": "Fire", "attacks": [{"dmg": 0}, {"dmg": 70}]},
    "zapdos ex": {"energy_type": "Lightning", "attacks": [{"dmg": 0}, {"dmg": 50, "coin_flips": 4}]},
    "marowak ex": {"energy_type": "Fighting", "attacks": [{"dmg": 80, "coin_flips": 2}]},
    "nidoqueen": {"energy_type": "Darkness", "attacks": [{"dmg": 80}]},
    "nidoking": {"energy_type": "Darkness", "attacks": [{"dmg": 90}]},
}

def play(state, game):
    """
    Advanced Pokemon TCG Pocket Player (v23 - Aggressive Tempo)
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
            if n in LOCAL_CARD_DB:
                et = LOCAL_CARD_DB[n].get("energy_type")
                return et.lower() if et else "colorless"
            if n in CARD_DB:
                et = CARD_DB[n].get("energy_type")
                return et.lower() if et else "colorless"

            if "pikachu" in n or "zapdos" in n or "raichu" in n or "electrode" in n or "magneton" in n or "blitzle" in n: return "lightning"
            if "mewtwo" in n or "gardevoir" in n or "ralts" in n or "kirlia" in n or "gastly" in n or "haunter" in n or "gengar" in n or "abra" in n: return "psychic"
            if "starmie" in n or "greninja" in n or "articuno" in n or "squirtle" in n or "blastoise" in n or "lapras" in n or "psyduck" in n or "goldeen" in n: return "water"
            if "charizard" in n or "moltres" in n or "charmander" in n or "magmar" in n or "ponyta" in n or "vulpix" in n or "ninetales" in n: return "fire"
            if "venusaur" in n or "bulbasaur" in n or "oddish" in n or "gloom" in n or "vileplume" in n or "exeggutor" in n: return "grass"
            if "marowak" in n or "machamp" in n or "geodude" in n or "onix" in n or "hitmon" in n or "cubone" in n or "sandshrew" in n: return "fighting"
            if "dragonite" in n or "dratini" in n: return "dragon"
            if "melmetal" in n or "meltan" in n: return "metal"
            if "weavile" in n or "muk" in n or "koffing" in n or "weezing" in n or "nidoran" in n or "nidoqueen" in n or "nidoking" in n: return "darkness"
            if "jigglypuff" in n or "meowth" in n or "eevee" in n or "pidgey" in n or "rattata" in n or "farfetch" in n or "kangaskhan" in n or "tauros" in n: return "colorless"
            return "colorless"

        def get_attacks(card_name):
            n = card_name.lower()
            if n in LOCAL_CARD_DB: return LOCAL_CARD_DB[n].get("attacks", [])
            if n in CARD_DB: return CARD_DB[n].get("attacks", [])
            return []

        def calculate_damage(attacker_card, attack_idx, my_bench, opp_active_card=None, opp_bench_count=0):
            name = get_card_name(attacker_card)
            n_lower = name.lower()
            my_bench_len = len([b for b in my_bench if b])
            opp_energy_count = len(get_card_energy(opp_active_card)) if opp_active_card else 0

            # Special Hardcoded Logic
            if "pikachu ex" in n_lower and attack_idx == 0:
                lightning_bench = 0
                for b in my_bench:
                    if b:
                        b_name = get_card_name(b)
                        if "lightning" in get_energy_type(b_name): lightning_bench += 1
                return 30 * lightning_bench
            if "marowak ex" in n_lower and attack_idx == 0: return 160
            if "indeedee ex" in n_lower and attack_idx == 0: return 30 + (30 * opp_energy_count)
            if "mewtwo ex" in n_lower:
                if attack_idx == 0: return 50
                if attack_idx == 1: return 150
            if "greninja" in n_lower and "ex" not in n_lower and attack_idx == 0: return 60
            if "starmie ex" in n_lower and attack_idx == 0: return 90
            if "cinccino" in n_lower and attack_idx == 0: return 30 * my_bench_len
            if "articuno ex" in n_lower:
                if attack_idx == 0: return 40
                if attack_idx == 1: return 80
            if "zapdos ex" in n_lower and attack_idx == 1: return 200

            # DB Logic
            attacks = get_attacks(name)
            damage = 0
            if attack_idx < len(attacks):
                atk = attacks[attack_idx]
                damage = atk.get("dmg", 0)
                text_val = atk.get("text")
                text = text_val.lower() if text_val else ""
                if "damage for each" in text:
                    multiplier = 0
                    m = re.search(r"(\d+) damage for each", text)
                    if m: multiplier = int(m.group(1))
                    else: multiplier = 20
                    if "benched" in text:
                        if "opponent" in text: damage += (multiplier * opp_bench_count)
                        else: damage += (multiplier * my_bench_len)
                    elif "energy" in text: damage += (multiplier * opp_energy_count)
                elif "more damage" in text:
                    m = re.search(r"(\d+) more damage", text)
                    if m: damage += int(m.group(1))
                    else: damage += 40
                elif "coin" in text and "heads" in text:
                    m = re.search(r"(\d+) damage for each heads", text)
                    if m:
                        num_coins = atk.get("coin_flips", 1)
                        damage = num_coins * int(m.group(1))

            # Fallback
            if damage == 0:
                attacks_obj = getattr(attacker_card, "attacks", [])
                if attack_idx < len(attacks_obj):
                    atk_obj = attacks_obj[attack_idx]
                    fixed = getattr(atk_obj, "fixed_damage", 0)
                    if fixed > 0: damage = fixed
                    else: damage = getattr(atk_obj, "damage", 0)
            return damage

        def has_enough_energy(card_obj, attack_idx):
            name = get_card_name(card_obj).lower()
            current_energy = len(get_card_energy(card_obj))

            # Check hardcoded
            if "mewtwo ex" in name:
                if attack_idx == 0: return current_energy >= 2
                if attack_idx == 1: return current_energy >= 4
            if "charizard ex" in name:
                if attack_idx == 0: return current_energy >= 2
                if attack_idx == 1: return current_energy >= 4

            attacks = get_attacks(name)
            if attack_idx < len(attacks):
                cost = len(attacks[attack_idx].get("cost", []))
                # Heuristic: if cost is 0 in DB, maybe it's 1 per 30 dmg?
                if cost == 0:
                    dmg = attacks[attack_idx].get("dmg", 0)
                    if dmg > 0: cost = max(1, dmg // 30)
                return current_energy >= cost

            # Fallback based on index
            return current_energy >= (attack_idx + 1)

        def needs_energy(card_obj):
            if not card_obj: return False
            name = get_card_name(card_obj).lower()
            current_energy = len(get_card_energy(card_obj))

            if "mewtwo ex" in name: return current_energy < 4
            if "charizard ex" in name: return current_energy < 4
            if "venusaur ex" in name: return current_energy < 4
            if "blastoise ex" in name: return current_energy < 3
            if "pikachu ex" in name: return current_energy < 2
            if "starmie ex" in name: return current_energy < 2
            if "marowak ex" in name: return current_energy < 2
            if "articuno ex" in name: return current_energy < 3
            if "moltres ex" in name: return current_energy < 3
            if "zapdos ex" in name: return current_energy < 3
            if "greninja" in name and "ex" not in name: return current_energy < 2

            attacks = get_attacks(name)
            max_cost = 0
            for atk in attacks:
                c = len(atk.get("cost", []))
                if c > max_cost: max_cost = c
            if max_cost == 0:
                if "ex" in name: return current_energy < 3
                return current_energy < 2
            return current_energy < max_cost

        # --- 2. Parse State ---
        me = state.current_player
        opp = 1 - me
        my_active = state.get_active_pokemon(me)
        my_bench_raw = state.get_bench_pokemon(me)
        my_bench = [b for b in my_bench_raw if b is not None]
        my_hand = state.get_hand(me)
        opp_hand = state.get_hand(opp) # Opponent hand (object ref or list, need to check length)
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

            elif aname.startswith("Retreat"):
                m = re.search(r"Retreat\((\d+)\)", aname)
                if m: acts["retreat"].append((aid, int(m.group(1))))

            elif aname.startswith("Activate"):
                m = re_activate.search(aname)
                if m: acts["activate"].append((aid, int(m.group(1))))

            elif "Stadium" in aname: acts["stadium"].append(aid)

        # --- 3. Strategic Execution ---

        # Pre-calc Lethal
        is_lethal = False
        lethal_action = None

        best_attack_dmg = -1
        best_attack_aid = None

        # 3.1 Check Active Lethal
        if acts["attack"]:
            best_attack_aid = acts["attack"][0][0] # Default
            best_attack_dmg = 0

            for aid, idx in acts["attack"]:
                d = calculate_damage(my_active, idx, my_bench, opp_active, len(opp_bench))
                if d > best_attack_dmg:
                    best_attack_dmg = d
                    best_attack_aid = aid

            if opp_active_hp > 0 and best_attack_dmg >= opp_active_hp:
                is_lethal = True
                lethal_action = best_attack_aid

        # 3.2 Check Bench Lethal (Retreat or Switch)
        if not is_lethal and opp_active_hp > 0:
            switch_item = None
            for aid, name, _ in acts["play_item"]:
                if "Switch" in name or "Escape" in name:
                    switch_item = aid
                    break

            # Check bench mons
            for i, b in enumerate(my_bench_raw):
                if b:
                    # Calculate potential damage
                    b_attacks = get_attacks(get_card_name(b))
                    max_b_dmg = 0
                    for idx_atk, _ in enumerate(b_attacks):
                        if has_enough_energy(b, idx_atk):
                            d = calculate_damage(b, idx_atk, my_bench, opp_active, len(opp_bench))
                            if d > max_b_dmg: max_b_dmg = d

                    if max_b_dmg >= opp_active_hp:
                        # Lethal found on bench!
                        # Check if we can switch to this specific mon (index i+1)
                        if switch_item:
                            lethal_action = switch_item
                            is_lethal = True
                            break

                        # Check retreat
                        for aid, target_idx in acts["retreat"]:
                            # target_idx is 1-based usually?
                            if target_idx == i + 1:
                                lethal_action = aid
                                is_lethal = True
                                break
                        if is_lethal: break

        # 0. Lethal Execution (Priority 1)
        giovanni = [a for a in acts["play_supporter"] if "Giovanni" in a[1]]

        if is_lethal and lethal_action:
            return lethal_action

        # Check if Giovanni makes it lethal (Active only for now)
        if not is_lethal and best_attack_aid and giovanni:
            if best_attack_dmg + 10 >= opp_active_hp:
                return giovanni[0][0]

        # 1. Draw (Priority 2)
        if acts["draw"]: return acts["draw"][0]

        research = [a for a in acts["play_supporter"] if "Research" in a[1]]
        # Prioritize Research unless deck out risk or hand is very full
        if research and len(my_hand) < 8: return research[0][0]

        # 2. Setup (Place/Evolve)
        if acts["evolve"]: return acts["evolve"][0][0]

        if acts["place_active"]:
            best_active = acts["place_active"][0][0]; max_score = -1000
            for aid, name in acts["place_active"]:
                score = 0; n = name.lower()
                if "pikachu ex" in n: score += 500
                if "starmie ex" in n: score += 500
                if "mewtwo ex" in n: score += 450
                if "articuno ex" in n: score += 450
                if "moltres ex" in n: score += 400
                if "zapdos ex" in n: score += 400
                if "ex" in n: score += 200
                if "pidgey" in n or "ralts" in n or "nidoran" in n: score -= 100
                if score > max_score: max_score = score; best_active = aid
            return best_active

        if acts["place_basic"]:
            bench_count = len(my_bench)
            if bench_count < 3:
                # Detect Synergies (Carry)
                carry_type = None
                if my_active:
                    aname = get_card_name(my_active).lower()
                    if "pikachu ex" in aname: carry_type = "lightning"
                    elif "mewtwo ex" in aname: carry_type = "psychic"
                    elif "starmie ex" in aname: carry_type = "water"
                    elif "marowak ex" in aname: carry_type = "fighting"

                # Check hand for Carry if not active
                if not carry_type:
                    for c in my_hand:
                        cname = get_card_name(c).lower()
                        if "pikachu ex" in cname: carry_type = "lightning"; break
                        if "mewtwo ex" in cname: carry_type = "psychic"; break

                best_bp = None; best_score = -9999
                for aid, name, _ in acts["place_basic"]:
                    score = 10; n = name.lower()
                    ctype = get_energy_type(name)

                    # Synergy Boost
                    if carry_type and ctype == carry_type: score += 100
                    if "pikachu ex" in n: score += 200 # Always good
                    if "ex" in n: score += 50

                    # Specifics
                    if "ralts" in n: score += 70
                    if "pidgey" in n: score += 60
                    if "articuno" in n or "moltres" in n or "zapdos" in n: score += 50

                    if bench_count == 0: score += 1000
                    if score > best_score: best_score = score; best_bp = aid

                if best_bp: return best_bp

        # 2b. Fill Bench (Semi-Aggressive)
        if acts["place_basic"] and len(my_bench) < 3:
             # Only fill if we have a decent option or are desperate
             # Don't fill with garbage if we have < 3 and are waiting for a specific carry
             pass

        # 3. Abilities
        if acts["ability"]:
            for aid, idx, target in acts["ability"]:
                user = my_active if idx == 0 else (my_bench_raw[idx-1] if idx-1 < len(my_bench_raw) else None)
                if user:
                    n = get_card_name(user).lower()
                    if "greninja" in n: return aid
                    if "pidgeot" in n:
                        if opp_active_hp > 60: return aid
                    if "gardevoir" in n: return aid
                    if "moltres" in n: return aid
                    if "pikachu" in n: return aid
            return acts["ability"][0][0]

        # 4. Supporters
        if acts["play_supporter"]:
            # Priority: Research
            if research and len(my_hand) < 8: return research[0][0]

            misty = [a for a in acts["play_supporter"] if "Misty" in a[1]]
            if misty:
                best_misty = None; best_score = -1
                for aid, _, target_idx in misty:
                    t_card = None
                    if target_idx == 0: t_card = my_active
                    elif target_idx > 0 and (target_idx-1) < len(my_bench_raw): t_card = my_bench_raw[target_idx-1]

                    if t_card:
                        name = get_card_name(t_card)
                        if "water" in get_energy_type(name) and needs_energy(t_card):
                            score = 100
                            if "ex" in name.lower(): score += 50
                            if target_idx == 0: score += 20
                            if score > best_score: best_score = score; best_misty = aid
                if best_misty: return best_misty

            sabrina = [a for a in acts["play_supporter"] if "Sabrina" in a[1]]
            if sabrina:
                opp_energy = len(get_card_energy(opp_active))
                if opp_energy >= 2 or opp_active_hp >= 100:
                    return sabrina[0][0]

            # Giovanni for Pressure
            if giovanni and best_attack_dmg > 0:
                return giovanni[0][0]

        # 5. Items
        if acts["play_item"]:
            # Switch Logic for Tempo (if not lethal)
            switch_item = None
            for aid, name, _ in acts["play_item"]:
                if "Switch" in name or "Escape" in name:
                    switch_item = aid
                    break

            if switch_item:
                # Calculate max damage possible from bench
                current_max_bench_dmg = 0
                for b in my_bench:
                    if b:
                        b_attacks = get_attacks(get_card_name(b))
                        for idx_atk, _ in enumerate(b_attacks):
                            if has_enough_energy(b, idx_atk):
                                d = calculate_damage(b, idx_atk, my_bench, opp_active, len(opp_bench))
                                if d > current_max_bench_dmg: current_max_bench_dmg = d

                # Switch if bench is significantly better (and active is weak)
                if current_max_bench_dmg > best_attack_dmg + 20 and best_attack_dmg < 60:
                     return switch_item

            potion = [a for a in acts["play_item"] if "Potion" in a[1]]
            if potion:
                 if my_active_hp > 0 and my_active_hp <= my_active_max_hp - 20: return potion[0][0]

            x_speed = [a for a in acts["play_item"] if "X Speed" in a[1]]
            if x_speed and my_active_hp <= 70: return x_speed[0][0]

            ball = [a for a in acts["play_item"] if "Ball" in a[1]]
            if ball: return ball[0][0]

            redcard = [a for a in acts["play_item"] if "Red Card" in a[1]]
            if redcard:
                # Discard opponent hand if they have many cards
                # Note: state.get_hand(opp) returns list.
                if len(opp_hand) >= 3:
                    return redcard[0][0]

        # 6. Attach Energy
        if acts["attach_energy"]:
            best_attach = None; max_score = -1000
            for aid, type_str, pos in acts["attach_energy"]:
                score = 0
                target = my_active if pos == 0 else (my_bench_raw[pos-1] if pos-1 < len(my_bench_raw) else None)
                if not target: continue

                t_name = get_card_name(target)
                t_type = get_energy_type(t_name)
                type_str_lower = type_str.lower()

                match = (type_str_lower == t_type) or (t_type == "colorless")
                if not match: score -= 500

                if needs_energy(target):
                    score += 100
                    if pos == 0:
                        if len(get_card_energy(target)) < 2: score += 80
                        else: score += 60
                    if "ex" in t_name.lower(): score += 80
                else:
                    score -= 50

                if score > max_score: max_score = score; best_attach = aid

            if best_attach and max_score > 0: return best_attach

        # 7. Attack
        if best_attack_aid:
            # If multiple attacks, ensure we pick the best one (already calculated)
            # If damage is 0, consider passing if we have a better switch?
            # But we already checked switch logic.
            return best_attack_aid

        # 8. Retreat
        if acts["retreat"] and my_active and my_active_hp > 0:
            best_retreat = None; max_r_score = -1

            for aid, target_idx in acts["retreat"]:
                # target_idx is 1-based index into bench?
                if target_idx - 1 < len(my_bench_raw):
                    b = my_bench_raw[target_idx - 1]
                    if b:
                        score = 0
                        # Energy/Attack Potential
                        b_attacks = get_attacks(get_card_name(b))
                        max_dmg = 0
                        has_energy = False
                        for idx_atk, _ in enumerate(b_attacks):
                            if has_enough_energy(b, idx_atk):
                                has_energy = True
                                d = calculate_damage(b, idx_atk, my_bench, opp_active, len(opp_bench))
                                if d > max_dmg: max_dmg = d

                        if has_energy: score += 500
                        score += max_dmg * 2

                        # HP
                        hp = get_card_hp(b)
                        score += hp

                        if "ex" in get_card_name(b).lower(): score += 50

                        if score > max_r_score:
                            max_r_score = score
                            best_retreat = aid

            # Condition to actually retreat
            should_retreat = False

            # Low HP Panic
            if my_active_hp <= 60 and max_r_score > 200: should_retreat = True

            # Better Damage Opportunity
            if best_retreat and max_r_score > 0:
                 bench_dmg = (max_r_score % 500) / 2 if max_r_score > 500 else 0
                 if best_attack_dmg < 40 and bench_dmg > best_attack_dmg + 20:
                     should_retreat = True

            if should_retreat and best_retreat:
                return best_retreat

        # 9. Activate (Switch)
        if acts["activate"]:
            best_act = acts["activate"][0][0]; best_score = -9999
            for aid, idx in acts["activate"]:
                if idx < len(my_bench_raw):
                     b = my_bench_raw[idx]
                     if b:
                         name = get_card_name(b).lower()
                         score = get_card_hp(b)
                         if not needs_energy(b): score += 500
                         elif len(get_card_energy(b)) > 0: score += 100
                         if "ex" in name: score += 50
                         if score > best_score: best_score = score; best_act = aid
            return best_act

        if acts["end"]: return acts["end"][0]

        return legal_actions[0]

    except Exception as e:
        logging.error(f"Error in play: {e}")
        return legal_actions[0]
