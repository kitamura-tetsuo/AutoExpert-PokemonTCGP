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
    logger.setLevel(logging.DEBUG)

def play(state, game):
    """
    Advanced Pokemon TCG Pocket Player Strategy (Refactored)
    """
    legal_actions = game.legal_actions()
    if not legal_actions:
        return 0

    try:
        # --- 1. Helper Functions ---
        def clean_name(raw_name):
            if not raw_name: return "Unknown"
            if raw_name.startswith("Some(") and raw_name.endswith(")"):
                raw_name = raw_name[5:-1]

            # Handle CamelCase
            m = re.match(r"^[A-Z0-9]+([A-Z].*)", raw_name)
            if m:
                name_part = m.group(1)
            else:
                name_part = raw_name

            cleaned = re.sub(r"([a-z])([A-Z])", r"\1 \2", name_part)
            key = cleaned.lower()
            if key in CARD_DB:
                return CARD_DB[key].get("name", key.title())
            return cleaned

        def get_card_name(card_obj):
            if not card_obj: return "Unknown"
            val = getattr(card_obj, "name", "Unknown")
            return clean_name(str(val)) if val is not None else "Unknown"

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
            key = card_name.lower()
            if key in CARD_DB: return CARD_DB[key]
            # Partial match fallback
            for k in CARD_DB:
                if k in key: return CARD_DB[k]
            return None

        def get_energy_type(card_name):
            db_card = get_db_card(card_name)
            if db_card:
                return db_card.get("energy_type", "Colorless")
            # Fallback logic omitted for brevity as DB covers most, but keeping basic fallback
            n = card_name.lower()
            if "pikachu" in n or "zapdos" in n: return "Lightning"
            if "mewtwo" in n or "gardevoir" in n: return "Psychic"
            if "charizard" in n or "moltres" in n: return "Fire"
            if "blastoise" in n or "starmie" in n or "greninja" in n: return "Water"
            if "venusaur" in n: return "Grass"
            if "machamp" in n: return "Fighting"
            if "weezing" in n: return "Darkness"
            if "dragonite" in n: return "Dragon"
            if "steelix" in n: return "Metal"
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
        my_bench = [b for b in my_bench_raw if b is not None] # Only valid cards
        my_hand = state.get_hand(me)

        opp_active = state.get_active_pokemon(opp)
        opp_bench_raw = state.get_bench_pokemon(opp)
        opp_bench_count = len([b for b in opp_bench_raw if b is not None])
        opp_hand = state.get_hand(opp)
        opp_hand_count = len(opp_hand)

        opp_active_hp = get_card_hp(opp_active) if opp_active else 0
        opp_energy_count = len(get_card_energy(opp_active)) if opp_active else 0

        my_active_name = get_card_name(my_active)
        my_active_energy_count = len(get_card_energy(my_active))

        # Check for Misty
        has_misty_in_hand = any("misty" in get_card_name(c).lower() for c in my_hand)

        # --- 3. Improved Logic Helpers ---
        def needs_energy(card_obj):
            if not card_obj: return False
            name = get_card_name(card_obj).lower()
            current_energy = len(get_card_energy(card_obj))

            # Hardcoded Overrides for meta cards
            if "pikachu ex" in name: return current_energy < 3
            if "mewtwo ex" in name: return current_energy < 4
            if "charizard ex" in name: return current_energy < 4
            if "starmie ex" in name: return current_energy < 2

            attacks = get_attacks(name)
            if not attacks: return current_energy < 2

            max_cost = 0
            for atk in attacks:
                cost_len = len(atk.get("cost", []))
                if cost_len > max_cost: max_cost = cost_len

            if max_cost == 0: return False # No energy needed?
            return current_energy < max_cost

        def calculate_damage(attacker_card, attack_idx, my_bench_list, opp_active_c, opp_b_count, opp_e_count):
            name = get_card_name(attacker_card)
            n_lower = name.lower()
            my_bench_len = len([b for b in my_bench_list if b])

            # Specific Overrides
            if "pikachu ex" in n_lower and attack_idx == 0:
                lightning_bench = 0
                for b in my_bench_list:
                    if b and "lightning" in get_energy_type(get_card_name(b)).lower():
                        lightning_bench += 1
                return 30 * lightning_bench

            if "mewtwo ex" in n_lower:
                return 50 if attack_idx == 0 else 150
            if "starmie ex" in n_lower and attack_idx == 0: return 90

            # DB Based Calculation
            attacks = get_attacks(name)
            damage = 0
            if attack_idx < len(attacks):
                atk = attacks[attack_idx]
                damage = atk.get("dmg", 0)
                text = (atk.get("text") or "").lower()

                # EV for Coin Flips
                if "flip" in text and "coin" in text:
                    num_coins = atk.get("coin_flips", 0)
                    if num_coins == 0:
                         # Try to parse "flip 2 coins" etc
                         m = re.search(r"flip (\d+) coin", text)
                         if m: num_coins = int(m.group(1))
                         else: num_coins = 1

                    dmg_per_head = 0
                    m_dmg = re.search(r"(\d+) damage for each heads", text)
                    if m_dmg:
                        dmg_per_head = int(m_dmg.group(1))
                        # Base damage is 0 usually for these attacks
                        damage = int(num_coins * 0.5 * dmg_per_head)

                    else:
                        m_more = re.search(r"heads, this attack does (\d+) more damage", text)
                        if m_more:
                             damage += int(int(m_more.group(1)) * 0.5 * num_coins)

                # Scaling
                if "damage for each" in text:
                    multiplier = 0
                    m = re.search(r"(\d+) damage for each", text)
                    if m: multiplier = int(m.group(1))
                    else: multiplier = 20 # Default guess

                    if "benched" in text:
                        if "opponent" in text: damage += (multiplier * opp_b_count)
                        else: damage += (multiplier * my_bench_len)
                    elif "energy" in text:
                         # Assume active energy
                         damage += (multiplier * opp_e_count)

                if "more damage" in text and "flip" not in text:
                     # Simple conditional checks
                     if "evolved" in text and "opponent" in text:
                         # Hard to check if opponent is evolved without more state, assume False or 50%?
                         pass
                     elif "damage on it" in text and opp_active_hp < get_card_max_hp(opp_active_c):
                         m = re.search(r"(\d+) more damage", text)
                         if m: damage += int(m.group(1))

            return damage

        # --- 4. Action Parsing & Categorization ---
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

        # SCORES
        LETHAL_WIN_SCORE = 1000000
        LETHAL_KO_SCORE = 30000
        DONK_PREVENTION_SCORE = 20000

        SETUP_EVOLVE_SCORE = 26000
        SETUP_MISTY_SCORE = 24600
        STRATEGIC_SWITCH_SCORE = 24500

        SETUP_RESEARCH_SCORE = 22500
        SETUP_SEARCH_SUPPORTER_SCORE = 23000

        SETUP_ATTACH_SCORE = 21500
        SETUP_PLACE_SCORE = 21000

        SETUP_HIGH_PRIORITY_ITEM_SCORE = 22000
        SETUP_ITEM_SCORE = 19000
        SETUP_SUPPORTER_SCORE = 14000

        ATTACK_BASE_SCORE = 1000
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

                    if opp_active_hp > 0:
                         if dmg >= opp_active_hp:
                             details["score"] = LETHAL_KO_SCORE
                             details["is_ko"] = True
                             if opp_bench_count == 0:
                                 details["score"] = LETHAL_WIN_SCORE
                                 details["is_lethal"] = True

            elif "Attach" in aname and "Tool" not in aname:
                 # Check specific first
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
                     details["score"] = SETUP_ATTACH_SCORE

                     target = None
                     if pos == 0: target = my_active
                     elif pos > 0 and pos <= len(my_bench_raw): target = my_bench_raw[pos-1]

                     if target:
                         if needs_energy(target): details["score"] += 1000
                         else: details["score"] -= 2000 # Don't over-attach

                         cname = get_card_name(target)
                         ctype = get_energy_type(cname)
                         if ctype in etype or etype in ctype: details["score"] += 500

            elif "Place" in aname or "PlayPokemon" in aname:
                 m = re_place.search(aname)
                 card_name = ""
                 pos = -1
                 if m:
                     card_name = clean_name(m.group(1))
                     pos = int(m.group(2))
                 else:
                     m2 = re_play_pokemon.search(aname)
                     if m2:
                         hand_idx = int(m2.group(1))
                         pos = int(m2.group(2))
                         if hand_idx < len(my_hand): card_name = get_card_name(my_hand[hand_idx])

                 if pos != -1:
                     details["type"] = "place"
                     details["card_name"] = card_name
                     details["score"] = SETUP_PLACE_SCORE

                     if len(my_bench) == 0: details["score"] = DONK_PREVENTION_SCORE
                     elif len(my_bench) < 3: details["score"] += 500

                     # Misty Prep
                     if has_misty_in_hand and "Water" in get_energy_type(card_name):
                         details["score"] += 2000

            elif "Evolve" in aname:
                details["type"] = "evolve"
                details["score"] = SETUP_EVOLVE_SCORE

            elif "UseSupporter" in aname or ("Play" in aname and not "Pokemon" in aname):
                details["type"] = "supporter"
                details["score"] = SETUP_SUPPORTER_SCORE

                if "Research" in aname or "Professor" in aname:
                    details["score"] = SETUP_RESEARCH_SCORE
                    if len(my_hand) >= 5: details["score"] -= 5000 # Do not use if hand is full

                elif "Lisia" in aname:
                     # Use Lisia if we have space or need evos
                     if len(my_bench) < 3: details["score"] = SETUP_SEARCH_SUPPORTER_SCORE

                elif "Misty" in aname:
                     needs_water = False
                     if my_active and "Water" in get_energy_type(my_active_name) and needs_energy(my_active): needs_water = True
                     for b in my_bench:
                         if "Water" in get_energy_type(get_card_name(b)) and needs_energy(b): needs_water = True

                     if needs_water: details["score"] = SETUP_MISTY_SCORE
                     else: details["score"] -= 1000

                elif "Sabrina" in aname:
                     # Simple Gust Logic
                     if opp_active_hp > 80: details["score"] = 17000
                     else: details["score"] = 13000

            elif "Retreat" in aname:
                details["type"] = "retreat"
                m = re_retreat.search(aname)
                target_pos = -1
                if m: target_pos = int(m.group(1))
                details["target_pos"] = target_pos
                details["score"] = RETREAT_SCORE

                # BUG FIX: check empty slot
                target_card = None
                # Simulator Index: 1-based for bench.
                # 0 is active? No, Retreat(X) X is bench index.
                # Based on logs: Retreat(2) -> Bench Index 1.
                idx = target_pos - 1
                if idx >= 0 and idx < len(my_bench_raw):
                    target_card = my_bench_raw[idx]

                if not target_card or get_card_name(target_card) == "Unknown" or get_card_name(target_card) == "Empty":
                    details["score"] = -100000 # DO NOT RETREAT TO VOID

                elif target_card:
                    # Don't retreat to something with no energy unless it's a tank or we are desperate
                    e = len(get_card_energy(target_card))
                    if e == 0 and get_card_hp(target_card) < 90:
                        details["score"] -= 5000

            elif "Activate" in aname:
                details["type"] = "activate"
                details["score"] = LETHAL_WIN_SCORE # Usually forcing a switch after KO

            parsed_actions.append(details)

        # --- 5. Heuristics ---

        # Emergency Retreat
        if my_active and get_card_hp(my_active) <= 40 and opp_active_hp > 0:
             # Try to save active
             for a in parsed_actions:
                 if a["type"] == "retreat" and a["score"] > -50000:
                     a["score"] = 25000 # Priority

        # Lethal Check on Attacks (Done in loop but verify)
        # Strategic Switch
        if not any(a.get("is_lethal") for a in parsed_actions):
             # Logic to switch if bench has lethal
             pass

        # --- 6. Select Best ---
        best_action = max(parsed_actions, key=lambda x: x["score"])

        logger.debug(f"State: Hand={len(my_hand)}, Bench={len(my_bench)}")
        for a in parsed_actions:
             if a["score"] > -5000:
                 logger.debug(f"Action: {a['name']} Score: {a['score']}")

        logger.debug(f"Selected: {best_action['name']}")

        return best_action["id"]

    except Exception as e:
        logger.error(f"Error: {e}")
        return legal_actions[0]
