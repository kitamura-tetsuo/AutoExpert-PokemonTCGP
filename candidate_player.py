
import re
import random
import logging
from db_dump import CARD_DB

# Setup logging
logger = logging.getLogger("player")
logger.setLevel(logging.INFO)
if not logger.handlers:
    fh = logging.FileHandler('player.log', mode='w')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    logger.addHandler(fh)

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
            # Fallback
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

            # Special Logic
            if "pikachu ex" in n_lower and attack_idx == 0:
                lightning_bench = 0
                for b in my_bench_list:
                    if b:
                        b_name = get_card_name(b)
                        if "lightning" in get_energy_type(b_name).lower(): lightning_bench += 1
                return 30 * lightning_bench

            if "mewtwo ex" in n_lower:
                if attack_idx == 0: return 50
                if attack_idx == 1: return 150

            if "starmie ex" in n_lower and attack_idx == 0: return 90

            if "articuno ex" in n_lower:
                if attack_idx == 0: return 40
                if attack_idx == 1: return 80

            if "moltres ex" in n_lower and attack_idx == 1: return 70

            if "zapdos ex" in n_lower and attack_idx == 1:
                return 100 # EV: 50 * 4 * 0.5

            if "marowak ex" in n_lower and attack_idx == 0:
                return 80 # EV: 80 * 2 * 0.5

            if "greninja" in n_lower and "ex" not in n_lower and attack_idx == 0: return 60

            if "cinccino" in n_lower and attack_idx == 0: return 30 * my_bench_len

            if "indeedee ex" in n_lower and attack_idx == 0: return 30 + (30 * opp_e_count)

            if "gardevoir" in n_lower and "ex" not in n_lower and attack_idx == 0: return 60

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
                        if "opponent" in text: damage += (multiplier * opp_b_count)
                        else: damage += (multiplier * my_bench_len)
                    elif "energy" in text: damage += (multiplier * opp_e_count)
                elif "more damage" in text:
                    m = re.search(r"(\d+) more damage", text)
                    if m: damage += int(m.group(1))
                    else: damage += 40
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
            if "gardevoir" in name: return current_energy < 3

            attacks = get_attacks(name)
            max_cost = 0
            for atk in attacks:
                c = len(atk.get("cost", []))
                if c > max_cost: max_cost = c

            if max_cost == 0: return False
            return current_energy < max_cost

        # --- 5. Action Parsing ---
        # Specific Regexes for tricky actions
        re_attach_energy = re.compile(r"AttachEnergy\((\d+), (.*?)\)")

        # Robust Regex for others
        # Captures: ActionName, Argument (optional), TargetIndex (optional)
        re_action = re.compile(r"(\w+)(?:\((?:Some\()?(.*?)\)?(?:, (\d+))?\))?")

        parsed_actions = []

        # Scoring Constants
        LETHAL_WIN_SCORE = 1000000
        LETHAL_KO_SCORE = 8000 # Lower than Setup (10000+) to prioritize building board
        EMERGENCY_RETREAT_SCORE = 30000

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

            # Special Handling for AttachEnergy
            m_energy = re_attach_energy.match(aname)
            if m_energy:
                details["type"] = "attach_energy"
                details["pos"] = int(m_energy.group(1))
                etype = m_energy.group(2)
                details["score"] = SETUP_ATTACH_SCORE

                target_card = None
                if details["pos"] == 0: target_card = my_active
                elif details["pos"] > 0 and details["pos"] <= len(my_bench_raw): target_card = my_bench_raw[details["pos"]-1]

                if target_card:
                    if needs_energy(target_card):
                        details["score"] += 800 # Boost active need
                        # Type match bonus
                        cname = get_card_name(target_card)
                        ctype = get_energy_type(cname)
                        if ctype in etype or etype in ctype: details["score"] += 200
                    else:
                        details["score"] -= 1000 # Don't over-attach
                else:
                    details["score"] -= 500

                parsed_actions.append(details)
                continue

            m = re_action.match(aname)
            if m:
                action_type = m.group(1)
                arg1 = m.group(2)
                arg2 = m.group(3) # Can be None

                # Normalize arguments
                if arg1 == "None": arg1 = None

                details["raw_type"] = action_type

                if action_type == "EndTurn":
                    details["type"] = "end"
                    details["score"] = END_TURN_SCORE

                elif action_type == "Attack":
                    idx = int(arg1) if arg1 else 0
                    details["type"] = "attack"
                    details["idx"] = idx
                    dmg = 0
                    if my_active:
                        dmg = calculate_damage(my_active, idx, my_bench, opp_active, opp_bench_count, opp_energy_count)
                    details["damage"] = dmg
                    details["score"] = ATTACK_BASE_SCORE + (dmg * 10)

                    if opp_active_hp > 0 and dmg >= opp_active_hp:
                        details["score"] = LETHAL_KO_SCORE
                        details["is_lethal"] = True
                        if opp_bench_count == 0:
                            details["score"] = LETHAL_WIN_SCORE

                    # Mewtwo ex Psydrive penalty
                    if "mewtwo ex" in my_active_name.lower() and idx == 1:
                        if not details.get("is_lethal"):
                             # If opp is low HP, don't waste Psydrive
                             if opp_active_hp <= 50: details["score"] -= 2000

                elif action_type == "AttachEnergy" or (action_type == "Attach" and any(t in (arg1 or "") for t in ["Energy", "Lightning", "Water", "Fire", "Grass", "Fighting", "Psychic", "Darkness", "Metal", "Dragon"])):
                    # Fallback for generic Attach(some(Energy), pos) if re_attach_energy failed
                    pos = -1
                    etype = "Energy"

                    if arg2:
                        pos = int(arg2)
                        etype = arg1
                    elif arg1:
                        if "," in arg1:
                             parts = arg1.split(",")
                             if parts[0].strip().isdigit():
                                 pos = int(parts[0].strip())
                                 etype = parts[1].strip()
                        elif arg1.isdigit():
                             pos = int(arg1)
                        else:
                             etype = arg1

                    details["type"] = "attach_energy"
                    details["pos"] = pos
                    details["score"] = SETUP_ATTACH_SCORE

                    target_card = None
                    if pos == 0: target_card = my_active
                    elif pos > 0 and pos <= len(my_bench_raw): target_card = my_bench_raw[pos-1]

                    if target_card:
                        if needs_energy(target_card):
                            details["score"] += 800
                            # Type match bonus
                            cname = get_card_name(target_card)
                            ctype = get_energy_type(cname)
                            if ctype in etype or etype in ctype: details["score"] += 200
                        else:
                            details["score"] -= 1000 # Don't over-attach
                    else:
                        details["score"] -= 500

                elif action_type == "AttachTool" or action_type == "Attach":
                    details["type"] = "tool"
                    details["score"] = SETUP_ITEM_SCORE

                elif action_type in ["Place", "PlayPokemon"]:
                    card_name = arg1
                    pos = -1

                    if arg2:
                        pos = int(arg2)
                    elif arg1 and "," in arg1:
                        parts = arg1.split(",")
                        card_name = parts[0].strip()
                        if parts[1].strip().isdigit():
                             pos = int(parts[1].strip())
                    elif arg1 and arg1.isdigit():
                         pass

                    details["type"] = "place"
                    details["card_name"] = card_name
                    details["score"] = SETUP_PLACE_SCORE

                    # Fill Bench Logic
                    if len(my_bench) < 2: details["score"] += 1000
                    elif len(my_bench) < 3: details["score"] += 500

                    # Synergy
                    if my_active:
                         aname = get_card_name(my_active)
                         atype = get_energy_type(aname)
                         ctype = get_energy_type(card_name)
                         if atype == ctype: details["score"] += 1000

                    # Strong Pokemon Bonus
                    if "ex" in card_name.lower(): details["score"] += 500

                elif action_type == "Evolve":
                    card_name = arg1
                    pos = int(arg2) if arg2 else -1
                    details["type"] = "evolve"
                    details["score"] = SETUP_EVOLVE_SCORE
                    if pos == 0: details["score"] += 500

                elif action_type in ["UseSupporter", "Play"]:
                    # Determine if supporter or item based on name
                    name_check = (arg1 or "").lower()
                    supporters = ["research", "professor", "sabrina", "giovanni", "erika", "misty", "blaine", "koga", "surge", "brock", "copycat", "lisia", "cyrus", "mars", "red", "guzma", "judge", "acerola", "hau", "bill"]
                    is_sup = any(s in name_check for s in supporters)

                    if is_sup:
                        details["type"] = "supporter"
                        details["supporter_name"] = arg1
                        details["score"] = SETUP_SUPPORTER_SCORE

                        if "research" in name_check or "professor" in name_check:
                            if len(my_hand) < 8: details["score"] += 3500
                            else: details["score"] -= 1000
                        elif "misty" in name_check:
                            needs_water = False
                            if "Water" in get_energy_type(my_active_name) and needs_energy(my_active): needs_water = True
                            for b in my_bench:
                                if "Water" in get_energy_type(get_card_name(b)) and needs_energy(b): needs_water = True
                            if needs_water: details["score"] += 1500
                            else: details["score"] -= 500
                        elif "sabrina" in name_check:
                            if opp_active_hp > 0 and opp_active_hp <= 60: details["score"] -= 8000
                        elif "giovanni" in name_check:
                             # Check if helps lethal
                             pass

                    else:
                        details["type"] = "item"
                        details["score"] = SETUP_ITEM_SCORE
                        if "potion" in name_check or "heal" in name_check:
                            if my_active and get_card_hp(my_active) < get_card_max_hp(my_active): details["score"] += 500
                            else: details["score"] = -500
                        elif "red card" in name_check:
                            if opp_hand_count >= 3: details["score"] += 500
                            else: details["score"] -= 10000

                elif action_type == "Retreat":
                    details["type"] = "retreat"
                    details["target_pos"] = int(arg1) if arg1 else -1
                    details["score"] = RETREAT_SCORE

                elif action_type == "Activate":
                    details["type"] = "activate"
                    details["target_pos"] = int(arg1) if arg1 else -1
                    if not my_active or get_card_hp(my_active) <= 0:
                        details["score"] = LETHAL_WIN_SCORE # Must activate
                    else:
                        details["score"] = SETUP_ITEM_SCORE # Switch effect

                elif action_type == "UseAbility":
                    details["type"] = "ability"
                    details["score"] = SETUP_ABILITY_SCORE

                elif action_type == "DiscardOwnCard":
                    details["type"] = "discard"
                    details["score"] = 0
                    cname = (arg1 or "").lower()
                    if "ex" in cname: details["score"] -= 1000
                    elif "energy" in cname: details["score"] += 100
                    else: details["score"] += 200

            parsed_actions.append(details)

        # --- 6. Post-Processing & Special Heuristics ---

        has_lethal_attack = any(a.get("is_lethal") for a in parsed_actions if a["type"] == "attack")

        # A. Retreat Logic (Lethal, Damage Optimization, Emergency)
        for action in parsed_actions:
            if action["type"] == "retreat" or (action["type"] == "activate" and my_active and get_card_hp(my_active) > 0):
                target_pos = action.get("target_pos", -1)
                if target_pos >= 0 and target_pos < len(my_bench_raw):
                    target_mon = my_bench_raw[target_pos]
                    if target_mon:
                        t_name = get_card_name(target_mon)
                        t_energy = len(get_card_energy(target_mon))
                        t_hp = get_card_hp(target_mon)

                        # Calculate Bench Damage Potential
                        t_attacks = get_attacks(t_name)
                        bench_dmg = 0
                        for i in range(len(t_attacks)):
                            cost = len(t_attacks[i].get("cost", []))
                            if t_energy >= cost:
                                d = calculate_damage(target_mon, i, my_bench, opp_active, opp_bench_count, opp_energy_count)
                                if d > bench_dmg: bench_dmg = d

                        # Calculate Active Damage Potential
                        active_dmg = 0
                        if my_active:
                             a_attacks = get_attacks(my_active_name)
                             for i in range(len(a_attacks)):
                                  cost = len(a_attacks[i].get("cost", []))
                                  if my_active_energy >= cost:
                                       d = calculate_damage(my_active, i, my_bench, opp_active, opp_bench_count, opp_energy_count)
                                       if d > active_dmg: active_dmg = d

                        # 1. Lethal Switch
                        if opp_active_hp > 0 and bench_dmg >= opp_active_hp:
                            action["score"] = LETHAL_KO_SCORE + 100
                            action["is_lethal_switch"] = True
                            if opp_bench_count == 0: action["score"] = LETHAL_WIN_SCORE

                        # 2. Damage Optimization Switch (if not lethal)
                        # Switch if bench does significantly more damage (e.g. +20) and Active is weak
                        elif bench_dmg >= (active_dmg + 20):
                             # Boost score to be higher than Retreat (-5000) and Attack (5000)
                             # But lower than Setup (10000).
                             # Say 9000.
                             action["score"] = 9000

                        # 3. Emergency Retreat / Lethal Threat Assessment
                        # Check if opponent can kill us next turn
                        my_active_hp = get_card_hp(my_active) if my_active else 0
                        opp_max_dmg = 0

                        if opp_active and my_active_hp > 0:
                             o_name = get_card_name(opp_active)
                             o_attacks = get_attacks(o_name)
                             o_energy = len(get_card_energy(opp_active))
                             for i in range(len(o_attacks)):
                                  # Check energy cost
                                  cost = len(o_attacks[i].get("cost", []))
                                  if o_energy >= cost:
                                      # Calculate damage coming FROM opponent
                                      # We pass opp_bench as the attacker's bench
                                      d = calculate_damage(opp_active, i, opp_bench, my_active, len(my_bench), my_active_energy)
                                      if d > opp_max_dmg: opp_max_dmg = d

                        if my_active_hp > 0 and opp_max_dmg >= my_active_hp:
                             # Opponent has lethal on board. Retreat if we can't kill them first.
                             if not has_lethal_attack:
                                 action["score"] = EMERGENCY_RETREAT_SCORE

        # B. Giovanni Logic
        gio_action = next((a for a in parsed_actions if a["type"] == "supporter" and "Giovanni" in a.get("supporter_name", "")), None)
        if gio_action:
             for a in parsed_actions:
                 if a["type"] == "attack":
                     dmg = a.get("damage", 0)
                     if opp_active_hp > 0 and dmg < opp_active_hp and (dmg + 10) >= opp_active_hp:
                         gio_action["score"] = 20000 # High priority
                         if opp_bench_count == 0: gio_action["score"] = LETHAL_WIN_SCORE

        # C. Mewtwo vs Psydrive
        mewtwo_attacks = [a for a in parsed_actions if a["type"] == "attack" and "mewtwo ex" in my_active_name.lower()]
        psydrive = next((a for a in mewtwo_attacks if a["idx"] == 1), None)
        standard = next((a for a in mewtwo_attacks if a["idx"] == 0), None)
        if psydrive and standard and standard.get("is_lethal"):
             psydrive["score"] = -2000

        # D. Lethal Efficiency (Don't waste time if we can win NOW)
        has_game_win = any(a["score"] >= LETHAL_WIN_SCORE for a in parsed_actions)
        if has_game_win:
             # If we can win, suppress everything else
             pass
        elif has_lethal_attack:
             # If we can KO, suppress place/items to save deck/time, unless setup is crucial?
             pass

        # --- 7. Selection ---
        best_score = -float('inf')
        best_action_id = legal_actions[0]

        # Shuffle for tie-breaking
        random.shuffle(parsed_actions)

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
