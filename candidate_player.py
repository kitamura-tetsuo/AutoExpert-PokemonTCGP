
import re
import random
import logging
import math
from db_dump import CARD_DB

# Setup logging
# logging.basicConfig(filename='player.log', level=logging.INFO, filemode='w', format='%(asctime)s - %(message)s')
logger = logging.getLogger("player")
if not logger.handlers:
    fh = logging.FileHandler('player.log', mode='w')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    logger.addHandler(fh)
    logger.setLevel(logging.INFO)

def play(state, game):
    """
    Advanced Pokemon TCG Pocket Player
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
            return "Colorless"

        def get_attacks(card_name):
            db_card = get_db_card(card_name)
            if db_card:
                return db_card.get("attacks", [])
            return []

        def calculate_damage(attacker_card, attack_idx, my_bench, opp_active_card, opp_bench_count, opp_energy_count):
            name = get_card_name(attacker_card)
            n_lower = name.lower()
            my_bench_len = len([b for b in my_bench if b])

            # Special Hardcoded Logic for scaling attacks
            if "pikachu ex" in n_lower and attack_idx == 0:
                lightning_bench = 0
                for b in my_bench:
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

            if "zapdos ex" in n_lower and attack_idx == 1: return 100 # EV: 50 * 4 * 0.5 = 100

            if "marowak ex" in n_lower and attack_idx == 0: return 80 # EV: 80 * 2 * 0.5 = 80

            if "greninja" in n_lower and "ex" not in n_lower and attack_idx == 0: return 60

            if "cinccino" in n_lower and attack_idx == 0: return 30 * my_bench_len

            if "indeedee ex" in n_lower and attack_idx == 0: return 30 + (30 * opp_energy_count)

            # DB Logic
            attacks = get_attacks(name)
            damage = 0
            if attack_idx < len(attacks):
                atk = attacks[attack_idx]
                damage = atk.get("dmg", 0)
                text_val = atk.get("text")
                text = text_val.lower() if text_val else ""

                # Simple scaling logic
                if "damage for each" in text:
                    multiplier = 0
                    m = re.search(r"(\d+) damage for each", text)
                    if m: multiplier = int(m.group(1))
                    else: multiplier = 20 # Fallback

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
                         # Use EV: damage * coins * 0.5
                         damage = int(num_coins * int(m.group(1)) * 0.5)

            return damage

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

            # Fallback based on DB
            attacks = get_attacks(name)
            max_cost = 0
            for atk in attacks:
                c = len(atk.get("cost", []))
                if c > max_cost: max_cost = c

            if max_cost == 0: return current_energy < 2 # Default fallback
            return current_energy < max_cost

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

        opp_active_hp = get_card_hp(opp_active) if opp_active else 0
        opp_energy_count = len(get_card_energy(opp_active)) if opp_active else 0

        # Pre-calculate legal action details
        # Regexes
        re_attack = re.compile(r"Attack\((\d+)\)")
        re_attach_energy = re.compile(r"AttachEnergy\((\d+), (.*?)\)") # AttachEnergy(pos, type)
        re_attach_simple = re.compile(r"Attach\((?:Some\()?(.*?)\)?, (\d+)\)") # Attach(Type/Card, pos)
        re_attach_tool = re.compile(r"AttachTool\((?:Some\()?(.*?)\)?, (\d+)\)")

        re_place = re.compile(r"Place\((?:Some\()?(.*?)\)?, (\d+)\)")
        re_evolve = re.compile(r"Evolve\((?:Some\()?(.*?)\)?, (\d+)\)")

        parsed_actions = []
        for aid in legal_actions:
            aname = game.action_name(aid)
            details = {"id": aid, "name": aname, "type": "unknown", "score": 0}

            # --- PRIORITY CONSTANTS ---
            # Highest: Lethal (Win or KO)
            # High: Activate (Mandatory/Critical)
            # High: Setup (Attach, Evolve, Place, Supporter, Item) -> These should generally be done BEFORE non-lethal attacking
            # Medium: Non-lethal Attack
            # Low: Retreat (Costly)
            # Lowest: EndTurn

            if aname == "EndTurn":
                details["type"] = "end"
                details["score"] = -10000

            elif "Attack" in aname:
                m = re_attack.search(aname)
                if m:
                    idx = int(m.group(1))
                    details["type"] = "attack"
                    details["idx"] = idx
                    if my_active:
                        dmg = calculate_damage(my_active, idx, my_bench, opp_active, opp_bench_count, opp_energy_count)
                        details["damage"] = dmg

            elif "AttachTool" in aname:
                m = re_attach_tool.search(aname)
                if m:
                    details["type"] = "item" # Tools are items
                    details["card_name"] = m.group(1)
                    details["pos"] = int(m.group(2))

            elif "Attach" in aname:
                 # Check format: AttachEnergy(pos, type) OR Attach(Type/Card, pos)
                 m = re_attach_energy.search(aname)
                 if m:
                     pos = int(m.group(1))
                     etype = m.group(2)
                     details["type"] = "attach_energy"
                     details["pos"] = pos
                     details["energy_type"] = etype
                 else:
                     m = re_attach_simple.search(aname)
                     if m:
                         obj = m.group(1)
                         pos = int(m.group(2))
                         # Check if obj is energy type
                         energy_types = ["Lightning", "Water", "Fire", "Grass", "Fighting", "Psychic", "Darkness", "Metal", "Colorless"]
                         if any(t in obj for t in energy_types) and "Energy" not in obj and len(obj) < 15:
                             details["type"] = "attach_energy"
                             details["pos"] = pos
                             details["energy_type"] = obj
                         elif "Energy" in obj:
                             details["type"] = "attach_energy"
                             details["pos"] = pos
                             details["energy_type"] = obj
                         else:
                             details["type"] = "item" # Tool?

            elif "Place" in aname or "PlayPokemon" in aname:
                 m = re_place.search(aname)
                 if m:
                     card_name = m.group(1)
                     pos = int(m.group(2))
                     details["type"] = "place"
                     details["card_name"] = card_name
                     details["pos"] = pos
                 elif "PlayPokemon" in aname:
                     m = re.search(r"PlayPokemon\((\d+), (\d+)\)", aname)
                     if m:
                         details["type"] = "place"
                         details["pos"] = int(m.group(2))

            elif "Evolve" in aname:
                m = re_evolve.search(aname)
                if m:
                    card_name = m.group(1)
                    pos = int(m.group(2))
                    details["type"] = "evolve"
                    details["card_name"] = card_name
                    details["pos"] = pos

            elif "UseSupporter" in aname or ("Play" in aname and not "Pokemon" in aname):
                is_supporter = False
                supporters = ["Research", "Professor", "Sabrina", "Giovanni", "Erika", "Misty", "Blaine", "Koga", "Lt. Surge", "Brock", "Copycat", "Lisia", "Cyrus", "Mars", "Red", "Guzma", "Judge", "Acerola", "Hau", "Bill", "Pokemon Center Lady", "Pokémon Center Lady", "Ilima"]
                for s in supporters:
                    if s in aname:
                        details["type"] = "supporter"
                        details["supporter_name"] = s
                        is_supporter = True
                        break
                if not is_supporter:
                    details["type"] = "item"

            elif "Retreat" in aname:
                details["type"] = "retreat"
                m = re.search(r"Retreat\((\d+)\)", aname)
                if m: details["target_pos"] = int(m.group(1))

            elif "Activate" in aname:
                details["type"] = "activate"
                m = re.search(r"Activate\((\d+)\)", aname)
                if m: details["target_pos"] = int(m.group(1))

            elif "UseAbility" in aname:
                details["type"] = "ability"

            elif "Heal" in aname:
                details["type"] = "heal"
                m = re.search(r"Heal\((\d+)\)", aname)
                if m: details["pos"] = int(m.group(1))

            elif "DiscardOwnCard" in aname:
                details["type"] = "discard"
                m = re.search(r"DiscardOwnCard\((?:Some\()?(.*?)\)?\)", aname)
                if m: details["card_name"] = m.group(1)

            parsed_actions.append(details)

        # --- 3. Evaluate Actions ---

        # Scoring Configuration
        LETHAL_WIN_SCORE = 1000000
        LETHAL_KO_SCORE = 500000
        ACTIVATE_SCORE = 100000

        SETUP_BASE_SCORE = 10000
        EVOLVE_SCORE = SETUP_BASE_SCORE + 500
        PLACE_BASIC_SCORE = SETUP_BASE_SCORE + 400
        ATTACH_ENERGY_NEEDED_SCORE = SETUP_BASE_SCORE + 300
        ATTACH_ENERGY_BENCH_SCORE = SETUP_BASE_SCORE + 100
        SUPPORTER_SCORE = SETUP_BASE_SCORE + 200
        ITEM_SCORE = SETUP_BASE_SCORE + 150
        ABILITY_SCORE = SETUP_BASE_SCORE + 100

        ATTACK_BASE_SCORE = 1000
        ATTACK_DAMAGE_SCORE_MULTIPLIER = 10

        RETREAT_SCORE = -20000 # Default negative, lower than EndTurn
        END_TURN_SCORE = -10000

        best_score = -float('inf')
        best_action = legal_actions[0]

        can_win = False

        for action in parsed_actions:
            score = 0
            
            if action["type"] == "attack":
                score += ATTACK_BASE_SCORE
                dmg = action.get("damage", 0)
                score += dmg * ATTACK_DAMAGE_SCORE_MULTIPLIER
                
                # Check lethal
                if opp_active_hp > 0 and dmg >= opp_active_hp:
                    score += LETHAL_KO_SCORE
                    if opp_bench_count == 0:
                        score += LETHAL_WIN_SCORE
                        can_win = True

            elif action["type"] == "attach_energy":
                # Check target
                pos = action.get("pos", -1)
                target_card = None
                if pos == 0: target_card = my_active
                elif pos > 0 and pos <= len(my_bench_raw): target_card = my_bench_raw[pos-1]
                
                if target_card:
                    if needs_energy(target_card):
                        score += ATTACH_ENERGY_NEEDED_SCORE
                        if pos == 0: score += 50 # Priority to active
                    else:
                        # On bench it's okay (setup for later)
                        if pos > 0: score += ATTACH_ENERGY_BENCH_SCORE
                        else: score += 10 # Wasted on active
                else:
                    score += 10
            
            elif action["type"] == "evolve":
                score += EVOLVE_SCORE
                pos = action.get("pos", -1)
                if pos == 0: score += 50
            
            elif action["type"] == "place":
                score += PLACE_BASIC_SCORE
                if len(my_bench) < 3:
                     score += 50
            
            elif action["type"] == "supporter":
                sname = action.get("supporter_name", "")
                if "Research" in sname:
                    if len(my_hand) < 5: score += SUPPORTER_SCORE + 100
                    else: score -= (SUPPORTER_SCORE + 50)
                elif "Sabrina" in sname:
                    score += SUPPORTER_SCORE
                elif "Giovanni" in sname:
                    score += SUPPORTER_SCORE
                else:
                    score += SUPPORTER_SCORE
            
            elif action["type"] == "item":
                score += ITEM_SCORE
                if "Potion" in action["name"] or "Heal" in action["name"]:
                     if my_active and get_card_hp(my_active) < get_card_max_hp(my_active):
                         score += 100
                     else:
                         score = -100 # Waste
            
            elif action["type"] == "ability":
                score += ABILITY_SCORE
            
            elif action["type"] == "retreat":
                score += RETREAT_SCORE
                # Retreat if active is in danger or useless
                target_pos = action.get("target_pos", -1)
                target_pokemon = None
                if target_pos >= 0 and target_pos < len(my_bench_raw):
                    target_pokemon = my_bench_raw[target_pos]

                if my_active and opp_active and target_pokemon:
                     active_hp = get_card_hp(my_active)
                     target_hp = get_card_hp(target_pokemon)

                     # Tighter emergency threshold
                     is_emergency = active_hp <= 40 and len(get_card_energy(opp_active)) >= 1

                     # Check if target is better
                     if is_emergency:
                         if target_hp > 40:
                             score += 25000 # Switch to healthier -> Result 5000
                         elif target_hp > active_hp:
                             score += 22000 # Switch to slightly better -> Result 2000

                     # Also if active has no energy but target has energy
                     if len(get_card_energy(my_active)) == 0 and len(get_card_energy(target_pokemon)) > 0:
                         score += 23000 # -> Result 3000
            
            elif action["type"] == "activate":
                score += ACTIVATE_SCORE
                target_pos = action.get("target_pos", -1)
                if target_pos >= 0 and target_pos < len(my_bench_raw):
                    b = my_bench_raw[target_pos]
                    if b:
                        e_count = len(get_card_energy(b))
                        score += 50 + (e_count * 100) # Prioritize charged pokemon significantly
                        hp = get_card_hp(b)
                        score += hp

            elif action["type"] == "heal":
                if my_active and get_card_hp(my_active) < get_card_max_hp(my_active):
                     score += ITEM_SCORE + 100
                else:
                     score += ITEM_SCORE - 200
            
            elif action["type"] == "discard":
                # We want to discard the LEAST valuable card.
                # Score should be higher for less valuable cards.
                # Base score 0.
                cname = action.get("card_name", "Unknown").lower()

                # Priority to discard:
                # 1. Weak Basics / excess Energy (if we have enough)
                # 2. Situational Items
                # 3. Supporters
                # 4. EX Pokemon / Key Cards
                
                if "ex" in cname:
                    score -= 1000 # Don't discard EX
                elif any(s.lower() in cname for s in ["research", "gio", "sabrina"]):
                    score -= 500 # Keep supporters
                elif "energy" in cname:
                    # If we have many energies in hand, okay to discard.
                    # Hard to check hand count here accurately without re-parsing state.
                    score += 100
                else:
                    score += 200 # Discard random pokemon/items

            elif action["type"] == "end":
                score += action["score"] # Use the base score set earlier

            action["score"] = score
            if score > best_score:
                best_score = score
                best_action = action["id"]

        logger.info(f"Turn: {state.turn if hasattr(state, 'turn') else '?'} | Player: {me}")
        logger.info(f"Legal Actions: {len(legal_actions)}")
        for a in parsed_actions:
            logger.info(f"  Action: {a['name']} | Type: {a['type']} | Score: {a['score']}")
        logger.info(f"Selected: {game.action_name(best_action)}")

        # Tie-breaking with random
        candidates = [a for a in parsed_actions if a["score"] == best_score]
        if candidates:
            return random.choice(candidates)["id"]

        return best_action

    except Exception as e:
        logging.error(f"Error in play: {e}")
        return legal_actions[0]
