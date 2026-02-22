
import re
import random
import logging
from db_dump import CARD_DB

# Setup logging
logger = logging.getLogger("player")
if not logger.handlers:
    fh = logging.FileHandler('player.log', mode='w')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    logger.addHandler(fh)
    logger.setLevel(logging.INFO)

def play(state, game):
    """
    Advanced Pokemon TCG Pocket Player Strategy
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

        def get_db_card(card_name):
            if not card_name: return None
            return CARD_DB.get(card_name.lower())

        def get_energy_type(card_name):
            db_card = get_db_card(card_name)
            if db_card:
                return db_card.get("energy_type", "Colorless")
            # Fallback based on name if DB missing
            n = card_name.lower()
            if "pikachu" in n or "zapdos" in n or "magneton" in n: return "Lightning"
            if "mewtwo" in n or "gardevoir" in n: return "Psychic"
            if "charizard" in n or "moltres" in n: return "Fire"
            if "blastoise" in n or "starmie" in n or "articuno" in n: return "Water"
            if "venusaur" in n: return "Grass"
            if "machamp" in n or "marowak" in n: return "Fighting"
            if "weezing" in n or "muk" in n: return "Darkness"
            if "melmetal" in n: return "Metal"
            return "Colorless"

        def get_attacks(card_name):
            db_card = get_db_card(card_name)
            if db_card:
                return db_card.get("attacks", [])
            return []

        # --- 2. Parse State ---
        me = state.current_player
        opp = 1 - me

        my_active = state.get_active_pokemon(me)
        my_bench_raw = state.get_bench_pokemon(me)
        my_bench = [b for b in my_bench_raw if b is not None]
        my_hand = state.get_hand(me)

        opp_active = state.get_active_pokemon(opp)
        opp_bench_raw = state.get_bench_pokemon(opp)
        opp_bench = [b for b in opp_bench_raw if b is not None]
        opp_bench_count = len(opp_bench)
        opp_hand = state.get_hand(opp)
        opp_hand_count = len(opp_hand)

        opp_active_hp = get_card_hp(opp_active) if opp_active else 0
        opp_energy_count = len(get_card_energy(opp_active)) if opp_active else 0

        my_active_name = get_card_name(my_active)
        my_active_energy = len(get_card_energy(my_active))

        # --- 3. Damage Calculation Logic ---
        def calculate_damage(attacker_card, attack_idx, my_bench_list, opp_active_c, opp_b_count, opp_e_count):
            name = get_card_name(attacker_card)
            n_lower = name.lower()
            my_bench_len = len([b for b in my_bench_list if b])

            # Special Hardcoded Logic for scaling attacks
            if "pikachu ex" in n_lower and attack_idx == 0: # Circle Circuit
                lightning_bench = 0
                for b in my_bench_list:
                    if b:
                        b_name = get_card_name(b)
                        # Check type
                        if "lightning" in get_energy_type(b_name).lower(): lightning_bench += 1
                return 30 * lightning_bench

            if "mewtwo ex" in n_lower:
                if attack_idx == 0: return 50
                if attack_idx == 1: return 150

            if "starmie ex" in n_lower and attack_idx == 0: return 90

            if "articuno ex" in n_lower:
                if attack_idx == 0: return 40
                if attack_idx == 1: return 80 # to bench too

            if "moltres ex" in n_lower and attack_idx == 1: return 70

            if "zapdos ex" in n_lower and attack_idx == 1:
                # EV: 50 * 4 * 0.5 = 100
                return 100

            if "marowak ex" in n_lower and attack_idx == 0:
                # EV: 80 * 2 * 0.5 = 80
                return 80

            if "greninja" in n_lower and "ex" not in n_lower and attack_idx == 0: return 60

            if "cinccino" in n_lower and attack_idx == 0: return 30 * my_bench_len

            if "indeedee ex" in n_lower and attack_idx == 0: return 30 + (30 * opp_e_count)

            if "gardevoir" in n_lower and "ex" not in n_lower and attack_idx == 0: return 60 # Psyshot

            # DB Logic Fallback
            attacks = get_attacks(name)
            damage = 0
            if attack_idx < len(attacks):
                atk = attacks[attack_idx]
                damage = atk.get("dmg", 0)
                text_val = atk.get("text")
                text = text_val.lower() if text_val else ""

                # Scaling logic regex
                if "damage for each" in text:
                    multiplier = 0
                    m = re.search(r"(\d+) damage for each", text)
                    if m: multiplier = int(m.group(1))
                    else: multiplier = 20 # Fallback

                    if "benched" in text:
                        if "opponent" in text: damage += (multiplier * opp_b_count)
                        else: damage += (multiplier * my_bench_len)
                    elif "energy" in text: damage += (multiplier * opp_e_count)
                elif "more damage" in text:
                    m = re.search(r"(\d+) more damage", text)
                    if m: damage += int(m.group(1))
                    else: damage += 40 # Generic boost
                elif "coin" in text and "heads" in text:
                     m = re.search(r"(\d+) damage for each heads", text)
                     if m:
                         num_coins = atk.get("coin_flips", 1)
                         damage = int(num_coins * int(m.group(1)) * 0.5)

            return damage

        # --- 4. Needs Energy Logic ---
        def needs_energy(card_obj):
            if not card_obj: return False
            name = get_card_name(card_obj).lower()
            current_energy = len(get_card_energy(card_obj))

            # Specific thresholds
            if "mewtwo ex" in name: return current_energy < 4 # Psydrive needs 2P 2C = 4 total usually
            if "charizard ex" in name: return current_energy < 4
            if "venusaur ex" in name: return current_energy < 4
            if "blastoise ex" in name: return current_energy < 3
            if "pikachu ex" in name: return current_energy < 2 # 2 for attack, 3 is overkill.
            if "starmie ex" in name: return current_energy < 2
            if "marowak ex" in name: return current_energy < 2
            if "articuno ex" in name: return current_energy < 3
            if "moltres ex" in name: return current_energy < 3
            if "zapdos ex" in name: return current_energy < 3
            if "greninja" in name and "ex" not in name: return current_energy < 2
            if "gardevoir" in name: return current_energy < 3

            # DB Fallback
            attacks = get_attacks(name)
            max_cost = 0
            for atk in attacks:
                c = len(atk.get("cost", []))
                if c > max_cost: max_cost = c

            if max_cost == 0: return False
            return current_energy < max_cost

        # --- 5. Action Parsing & Categorization ---
        re_attack = re.compile(r"Attack\((\d+)\)")
        re_attach_energy = re.compile(r"AttachEnergy\((\d+), (.*?)\)")
        re_attach_simple = re.compile(r"Attach\((?:Some\()?(.*?)\)?, (\d+)\)")
        re_attach_tool = re.compile(r"AttachTool\((?:Some\()?(.*?)\)?, (\d+)\)")
        re_place = re.compile(r"Place\((?:Some\()?(.*?)\)?, (\d+)\)")
        re_play_pokemon = re.compile(r"PlayPokemon\((\d+), (\d+)\)")
        re_evolve = re.compile(r"Evolve\((?:Some\()?(.*?)\)?, (\d+)\)")
        re_retreat = re.compile(r"Retreat\((\d+)\)")
        re_activate = re.compile(r"Activate\((\d+)\)")
        re_heal = re.compile(r"Heal\((\d+)\)")
        re_discard = re.compile(r"DiscardOwnCard\((?:Some\()?(.*?)\)?\)")

        parsed_actions = []

        # Priority constants
        LETHAL_WIN_SCORE = 1000000
        LETHAL_KO_SCORE = 500000

        SETUP_EVOLVE_SCORE = 16000
        SETUP_PLACE_SCORE = 14000
        SETUP_ATTACH_SCORE = 13000
        SETUP_SUPPORTER_SCORE = 12000
        SETUP_ITEM_SCORE = 11000
        SETUP_ABILITY_SCORE = 10000

        ATTACK_BASE_SCORE = 5000
        RETREAT_SCORE = -5000
        END_TURN_SCORE = -10000

        for aid in legal_actions:
            aname = game.action_name(aid)
            details = {"id": aid, "name": aname, "type": "unknown", "score": 0}

            if aname == "EndTurn":
                details["type"] = "end"
                details["score"] = END_TURN_SCORE

            elif "Attack" in aname:
                m = re_attack.search(aname)
                if m:
                    idx = int(m.group(1))
                    details["type"] = "attack"
                    details["idx"] = idx
                    dmg = 0
                    if my_active:
                         dmg = calculate_damage(my_active, idx, my_bench, opp_active, opp_bench_count, opp_energy_count)
                    details["damage"] = dmg
                    details["score"] = ATTACK_BASE_SCORE + (dmg * 10)

                    # Lethal Check
                    if opp_active_hp > 0 and dmg >= opp_active_hp:
                        details["score"] += LETHAL_KO_SCORE
                        if opp_bench_count == 0:
                            details["score"] += LETHAL_WIN_SCORE
                            details["is_lethal"] = True

                    # Mewtwo ex Psydrive penalty if not lethal
                    if "mewtwo ex" in my_active_name.lower() and idx == 1:
                        if not details.get("is_lethal"):
                             # If we have index 0 attack available and it's decent, prefer that
                             # But simpler logic: penalize unless really needed (high damage)
                             # 150 damage is good, but discards energy.
                             # If opp HP is low (e.g. <= 50), this is overkill and wasteful.
                             if opp_active_hp <= 50:
                                 details["score"] -= 2000

            elif "AttachTool" in aname:
                m = re_attach_tool.search(aname)
                if m:
                    details["type"] = "tool"
                    details["card_name"] = m.group(1)
                    details["pos"] = int(m.group(2))
                    details["score"] = SETUP_ITEM_SCORE

            elif "Attach" in aname:
                 m = re_attach_energy.search(aname)
                 pos = -1
                 etype = ""
                 if m:
                     pos = int(m.group(1))
                     etype = m.group(2)
                 else:
                     m = re_attach_simple.search(aname)
                     if m:
                         obj = m.group(1)
                         pos = int(m.group(2))
                         if "Energy" in obj or any(t in obj for t in ["Lightning", "Water", "Fire", "Grass", "Fighting", "Psychic", "Darkness", "Metal"]):
                             etype = obj

                 if etype:
                     details["type"] = "attach_energy"
                     details["pos"] = pos
                     details["energy_type"] = etype
                     details["score"] = SETUP_ATTACH_SCORE

                     # Check target
                     target_card = None
                     if pos == 0: target_card = my_active
                     elif pos > 0 and pos <= len(my_bench_raw): target_card = my_bench_raw[pos-1]

                     if target_card:
                         # Prioritize Active if it needs energy
                         if pos == 0 and needs_energy(target_card):
                             details["score"] += 800
                         elif needs_energy(target_card):
                             details["score"] += 500

                         # Bonus for type match
                         cname = get_card_name(target_card)
                         ctype = get_energy_type(cname)
                         if ctype in etype or etype in ctype:
                             details["score"] += 200

                         if not needs_energy(target_card):
                             details["score"] -= 500 # Don't over-attach
                     else:
                         details["score"] -= 1000 # Invalid target?
                 else:
                     # Fallback for generic attach if regex failed or it's a tool
                     details["type"] = "tool" # assume tool
                     details["score"] = SETUP_ITEM_SCORE

            elif "Place" in aname or "PlayPokemon" in aname:
                 m = re_place.search(aname)
                 if m:
                     card_name = m.group(1)
                     pos = int(m.group(2))
                     details["type"] = "place"
                     details["card_name"] = card_name
                     details["pos"] = pos
                     details["score"] = SETUP_PLACE_SCORE

                     if len(my_bench) < 2: details["score"] += 1000
                     elif len(my_bench) < 3: details["score"] += 500

                     # Synergy bonus
                     if my_active:
                         aname = get_card_name(my_active)
                         atype = get_energy_type(aname)
                         ctype = get_energy_type(card_name)
                         if atype == ctype: details["score"] += 500
                 else:
                     m2 = re_play_pokemon.search(aname)
                     if m2:
                         details["type"] = "place"
                         details["pos"] = int(m2.group(2))
                         details["score"] = SETUP_PLACE_SCORE
                         if len(my_bench) < 3: details["score"] += 500

            elif "Evolve" in aname:
                m = re_evolve.search(aname)
                if m:
                    card_name = m.group(1)
                    pos = int(m.group(2))
                    details["type"] = "evolve"
                    details["card_name"] = card_name
                    details["pos"] = pos
                    details["score"] = SETUP_EVOLVE_SCORE
                    if pos == 0: details["score"] += 500 # Prioritize active evolution

            elif "UseSupporter" in aname or ("Play" in aname and not "Pokemon" in aname):
                is_supporter = False
                supporters = ["Research", "Professor", "Sabrina", "Giovanni", "Erika", "Misty", "Blaine", "Koga", "Lt. Surge", "Brock", "Copycat", "Lisia", "Cyrus", "Mars", "Red", "Guzma", "Judge", "Acerola", "Hau", "Bill", "Pokemon Center Lady", "Pokémon Center Lady", "Ilima"]
                sname = ""
                for s in supporters:
                    if s in aname:
                        sname = s
                        is_supporter = True
                        break

                if is_supporter:
                    details["type"] = "supporter"
                    details["supporter_name"] = sname
                    details["score"] = SETUP_SUPPORTER_SCORE

                    if "Research" in sname or "Professor" in sname:
                        # Improved Logic: Use if hand size is small (< 8). No discard in this sim.
                        if len(my_hand) < 8: details["score"] += 1000
                        else: details["score"] -= 1000 # Wasteful if hand full
                    elif "Sabrina" in sname:
                        # Good if opponent active is strong or has energy
                        if opp_active and opp_energy_count >= 2: details["score"] += 500
                    elif "Giovanni" in sname:
                        # Will be boosted if lethal in post-process
                        pass
                    elif "Misty" in sname:
                        # Check for Water pokemon needing energy.
                        needs_water = False
                        if "Water" in get_energy_type(my_active_name) and needs_energy(my_active): needs_water = True
                        for b in my_bench:
                             if "Water" in get_energy_type(get_card_name(b)) and needs_energy(b): needs_water = True

                        if needs_water: details["score"] += 800
                        else: details["score"] -= 500
                else:
                    details["type"] = "item"
                    details["score"] = SETUP_ITEM_SCORE
                    if "Potion" in aname or "Heal" in aname:
                         if my_active and get_card_hp(my_active) < get_card_max_hp(my_active):
                             details["score"] += 500
                         else:
                             details["score"] = -500
                    elif "Red Card" in aname:
                         # Improved Logic: Only use if opponent hand >= 3
                         if opp_hand_count >= 3: details["score"] += 500
                         else: details["score"] -= 10000 # Save it if opp hand is low

            elif "Retreat" in aname:
                details["type"] = "retreat"
                m = re_retreat.search(aname)
                if m:
                    target_pos = int(m.group(1))
                    details["target_pos"] = target_pos
                details["score"] = RETREAT_SCORE

            elif "Activate" in aname:
                details["type"] = "activate"
                m = re_activate.search(aname)
                if m: details["target_pos"] = int(m.group(1))
                details["score"] = LETHAL_WIN_SCORE # Must activate if no active

                # But if we have an active, this is a Switch effect (from item/supporter)
                if my_active and get_card_hp(my_active) > 0:
                     details["score"] = SETUP_ITEM_SCORE # Lower priority than lethal switch
                else:
                     # Prioritize charged pokemon
                     if details.get("target_pos") is not None:
                         t_pos = details["target_pos"]
                         if t_pos < len(my_bench_raw):
                             b = my_bench_raw[t_pos]
                             if b:
                                 e_count = len(get_card_energy(b))
                                 details["score"] += (e_count * 1000)

            elif "UseAbility" in aname:
                details["type"] = "ability"
                details["score"] = SETUP_ABILITY_SCORE

            elif "Heal" in aname:
                details["type"] = "heal"
                details["score"] = SETUP_ITEM_SCORE
                if my_active and get_card_hp(my_active) < get_card_max_hp(my_active):
                     details["score"] += 500

            elif "DiscardOwnCard" in aname:
                details["type"] = "discard"
                m = re_discard.search(aname)
                if m: details["card_name"] = m.group(1)
                details["score"] = 0

                cname = details.get("card_name", "Unknown").lower()
                if "ex" in cname: details["score"] -= 1000
                elif "research" in cname or "gio" in cname or "sabrina" in cname: details["score"] -= 500
                elif "energy" in cname: details["score"] += 100
                else: details["score"] += 200

            parsed_actions.append(details)

        # --- 6. Post-Processing & Special Heuristics ---

        # A. Lethal Retreat Check
        # If we have a retreat option, check if the target Pokemon can kill the active
        for action in parsed_actions:
            if action["type"] == "retreat" or (action["type"] == "activate" and my_active and get_card_hp(my_active) > 0):
                target_pos = action.get("target_pos", -1)
                if target_pos >= 0 and target_pos < len(my_bench_raw):
                    target_mon = my_bench_raw[target_pos]
                    if target_mon:
                        # Check its attacks
                        t_name = get_card_name(target_mon)
                        t_attacks = get_attacks(t_name)
                        t_energy = len(get_card_energy(target_mon))

                        max_dmg = 0
                        # Quick simulation of damage
                        for i in range(len(t_attacks)):
                            # Check energy cost
                            cost = len(t_attacks[i].get("cost", []))
                            # For some cards, check specific energy types if possible, but count is a good proxy
                            if t_energy >= cost:
                                d = calculate_damage(target_mon, i, my_bench, opp_active, opp_bench_count, opp_energy_count)
                                if d > max_dmg: max_dmg = d

                        if opp_active_hp > 0 and max_dmg >= opp_active_hp:
                             action["score"] = LETHAL_WIN_SCORE if opp_bench_count == 0 else LETHAL_KO_SCORE
                             action["is_lethal_switch"] = True

                        # B2. Retreat for Damage (Improvement)
                        # If active does little damage (< 20) and bench does significant damage (> 40)
                        # and bench has energy.
                        # Approximate active damage
                        active_dmg = 0
                        if my_active:
                             a_attacks = get_attacks(my_active_name)
                             for i in range(len(a_attacks)):
                                  # Simple energy check
                                  if my_active_energy >= len(a_attacks[i].get("cost", [])):
                                       d = calculate_damage(my_active, i, my_bench, opp_active, opp_bench_count, opp_energy_count)
                                       if d > active_dmg: active_dmg = d

                        if active_dmg < 20 and max_dmg >= 40:
                             # Boost to make it higher than Attack (5000) but lower than Ability (10000).
                             # Base retreat is -5000. +14000 = 9000.
                             action["score"] += 14000

        # B. Emergency Retreat
        if my_active and get_card_hp(my_active) <= 40 and opp_active and len(get_card_energy(opp_active)) > 0:
            for action in parsed_actions:
                if action["type"] == "retreat":
                    action["score"] += 30000 # Higher than setup, lower than lethal

        # C. Giovanni for Lethal
        # If we have a Giovanni action, check if using it + Attack becomes lethal
        # Current logic doesn't simulate the +10 damage state change easily.
        # But we can assume if we have an attack that is (HP - 10) <= Damage < HP, Giovanni is lethal.

        has_giovanni = False
        gio_action = None
        for a in parsed_actions:
            if a["type"] == "supporter" and "Giovanni" in a.get("supporter_name", ""):
                has_giovanni = True
                gio_action = a
                break

        if has_giovanni:
            # Check attacks
            for a in parsed_actions:
                if a["type"] == "attack":
                    dmg = a.get("damage", 0)
                    if opp_active_hp > 0 and dmg < opp_active_hp and (dmg + 10) >= opp_active_hp:
                        # Giovanni makes this lethal!
                        gio_action["score"] = LETHAL_KO_SCORE + 100 # Prioritize Giovanni
                        if opp_bench_count == 0: gio_action["score"] = LETHAL_WIN_SCORE + 100

        # D. Mewtwo ex Psydrive check vs Standard Attack
        # If we have both attacks available, and standard attack is lethal, prefer standard to save energy.
        # This requires finding the actions in parsed_actions.
        mewtwo_attacks = [a for a in parsed_actions if a["type"] == "attack" and "mewtwo ex" in my_active_name.lower()]
        psydrive = next((a for a in mewtwo_attacks if a["idx"] == 1), None)
        standard = next((a for a in mewtwo_attacks if a["idx"] == 0), None)

        if psydrive and standard and standard.get("is_lethal"):
             psydrive["score"] = -1000 # Penalize Psydrive if standard is lethal

        # --- 7. Selection ---
        best_score = -float('inf')
        best_action_id = legal_actions[0]

        for action in parsed_actions:
            if action["score"] > best_score:
                best_score = action["score"]
                best_action_id = action["id"]

        # Logging
        logger.debug(f"Turn: {state.turn if hasattr(state, 'turn') else '?'} | Player: {me}")
        for a in parsed_actions:
            if a["score"] > -5000:
                 logger.debug(f"Action: {a['name']} | Type: {a['type']} | Score: {a['score']}")
        logger.debug(f"Selected: {game.action_name(best_action_id)}")

        return best_action_id

    except Exception as e:
        logger.error(f"Error in play: {e}")
        return legal_actions[0]
