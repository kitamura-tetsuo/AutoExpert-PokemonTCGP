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
        def clean_name(raw_name):
            if not raw_name: return "Unknown"
            if raw_name.startswith("Some(") and raw_name.endswith(")"):
                raw_name = raw_name[5:-1]

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
            for k in CARD_DB:
                if k in key: return CARD_DB[k]
            return None

        def get_energy_type(card_name):
            db_card = get_db_card(card_name)
            if db_card:
                return db_card.get("energy_type", "Colorless")
            # Fallback
            n = card_name.lower()
            if "pikachu" in n or "zapdos" in n or "magneton" in n or "magnezone" in n or "oricorio" in n or "ampharos" in n or "raichu" in n or "luxray" in n or "electabuzz" in n or "electrode" in n or "jolteon" in n or "zebstrika" in n or "galvantula" in n or "heliolisk" in n or "vikavolt" in n or "pincurchin" in n or "pawmot" in n or "bellibolt" in n: return "Lightning"
            if "mewtwo" in n or "gardevoir" in n or "ralts" in n or "gengar" in n or "alakazam" in n or "hypno" in n or "jynx" in n or "mew" in n or "espeon" in n or "wobbuffet" in n or "banette" in n or "drifblim" in n or "mismagius" in n or "gallade" in n or "uxie" in n or "mesprit" in n or "azelf" in n or "cresselia" in n or "sigilyph" in n or "gothitelle" in n or "reuniclus" in n or "malamar" in n or "naganadel" in n or "gourgeist" in n or "indeedee" in n: return "Psychic"
            if "charizard" in n or "moltres" in n or "magmar" in n or "arcanine" in n or "ninetales" in n or "rapidash" in n or "flareon" in n or "typhlosion" in n or "magcargo" in n or "houndoom" in n or "entei" in n or "blaziken" in n or "camerupt" in n or "torkoal" in n or "infernape" in n or "heatran" in n or "victini" in n or "chandelure" in n or "volcarona" in n or "reshiram" in n or "delphox" in n or "pyroar" in n or "talonflame" in n or "salazzle" in n or "turtonator" in n or "blacephalon" in n or "cinderace" in n or "centiskorch" in n: return "Fire"
            if "blastoise" in n or "starmie" in n or "articuno" in n or "greninja" in n or "suicune" in n or "gyarados" in n or "lapras" in n or "vaporeon" in n or "feraligatr" in n or "politoed" in n or "kingdra" in n or "swampert" in n or "wailord" in n or "milotic" in n or "kyogre" in n or "empoleon" in n or "floatzel" in n or "lumineon" in n or "samurott" in n or "keldeo" in n or "primarina" in n or "wishiwashi" in n or "tapu fini" in n or "inteleon" in n or "drednaw" in n or "frosmoth" in n: return "Water"
            if "venusaur" in n or "bulbasaur" in n or "exeggutor" in n or "vileplume" in n or "victreebel" in n or "tangela" in n or "scyther" in n or "pinsir" in n or "meganium" in n or "bellossom" in n or "jumpluff" in n or "celebi" in n or "sceptile" in n or "shiftry" in n or "cacturne" in n or "tropius" in n or "torterra" in n or "roserade" in n or "leafeon" in n or "shaymin" in n or "serperior" in n or "virizion" in n or "chesnaught" in n or "decidueye" in n or "lurantis" in n or "tapu bulu" in n or "rillaboom" in n or "eldegoss" in n or "meowscarada" in n: return "Grass"
            if "machamp" in n or "hitmonchan" in n or "marowak" in n or "hitmonlee" in n or "kabutops" in n or "aerodactyl" in n or "sudowoodo" in n or "donphan" in n or "tyranitar" in n or "lucario" in n or "rampardos" in n or "rhyperior" in n or "gallade" in n or "terrakion" in n or "landorus" in n or "zygarde" in n or "lycanroc" in n or "buzzwole" in n or "stonjourner" in n or "coalossal" in n or "grapploct" in n or "falinks" in n or "koraidon" in n: return "Fighting"
            if "weezing" in n or "muk" in n or "arbok" in n or "gengar" in n or "umbreon" in n or "tyranitar" in n or "absol" in n or "spiritomb" in n or "darkrai" in n or "drapion" in n or "weavile" in n or "darkrai" in n or "zoroark" in n or "hydreigon" in n or "krookodile" in n or "scrafty" in n or "mandibuzz" in n or "greninja" in n or "pangoro" in n or "yveltal" in n or "incineroar" in n or "guzzlord" in n or "grimmsnarl" in n or "obstagoon" in n or "morpeko" in n: return "Darkness"
            if "dragonite" in n or "altaria" in n or "salamence" in n or "latias" in n or "latios" in n or "rayquaza" in n or "garchomp" in n or "haxorus" in n or "druddigon" in n or "hydreigon" in n or "goodra" in n or "noivern" in n or "kommo-o" in n or "drampa" in n or "naganadel" in n or "regidrago" in n or "cyclizar" in n or "tatsugiri" in n: return "Dragon"
            if "steelix" in n or "scizor" in n or "skarmory" in n or "aggron" in n or "metagross" in n or "jirachi" in n or "bronzong" in n or "lucario" in n or "magnezone" in n or "probopass" in n or "dialga" in n or "excadrill" in n or "ferrothorn" in n or "klinklang" in n or "cobalion" in n or "aegislash" in n or "klefki" in n or "solgaleo" in n or "celesteela" in n or "kartana" in n or "meltan" in n or "melmetal" in n or "corviknight" in n or "copperajah" in n: return "Metal"
            return "Colorless"

        def get_attacks(card_name):
            db_card = get_db_card(card_name)
            if db_card:
                return db_card.get("attacks", [])
            return []

        # --- 2. Parse State ---
        me = state.current_player
        opp = 1 - me

        # Points Logic
        my_points = state.points[me] if hasattr(state, 'points') else 0
        opp_points = state.points[opp] if hasattr(state, 'points') else 0

        # Desperation Mode: If Opp needs 1 more point to win (assuming 3 points to win)
        is_desperate = False
        if opp_points >= 2:
            is_desperate = True

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

        # Check if Misty is in hand
        has_misty_in_hand = any("misty" in get_card_name(c).lower() for c in my_hand)

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

            if "zapdos ex" in n_lower and attack_idx == 1: return 100 # EV

            if "marowak ex" in n_lower and attack_idx == 0: return 80 # EV

            if "greninja" in n_lower and "ex" not in n_lower and attack_idx == 0: return 60

            if "cinccino" in n_lower and attack_idx == 0: return 30 * my_bench_len

            if "indeedee ex" in n_lower and attack_idx == 0: return 30 + (30 * opp_e_count)

            if "gardevoir" in n_lower and "ex" not in n_lower and attack_idx == 0: return 60

            # DB Logic Fallback
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

        def calculate_base_damage(attacker_card, attack_idx):
            """Returns the guaranteed deterministic damage."""
            name = get_card_name(attacker_card)
            n_lower = name.lower()

            if "mewtwo ex" in n_lower:
                if attack_idx == 0: return 50
                if attack_idx == 1: return 150
            if "starmie ex" in n_lower and attack_idx == 0: return 90

            attacks = get_attacks(name)
            damage = 0
            if attack_idx < len(attacks):
                atk = attacks[attack_idx]
                damage = atk.get("dmg", 0)
                text_val = atk.get("text")
                text = text_val.lower() if text_val else ""
                if "coin" in text and "heads" in text:
                     return 0

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

            if max_cost == 0:
                # Unknown card or no attacks found. Assume it needs at least 1-2 energy.
                return current_energy < 2

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

        # STRICT PRIORITY SYSTEM
        LETHAL_WIN_SCORE = 1000000
        DONK_PREVENTION_SCORE = 30000

        SETUP_EVOLVE_SCORE = 25000
        STRATEGIC_SWITCH_SCORE = 24500 # Just below Evolve
        MISTY_PREP_PLACE_SCORE = 24200 # If Misty in hand (and Water type)
        SETUP_MISTY_SCORE = 24000

        SETUP_SEARCH_ITEM_SCORE = 23000
        SETUP_SEARCH_SUPPORTER_SCORE = 22000
        SETUP_HIGH_PRIORITY_ITEM_SCORE = 22000
        SETUP_ATTACH_SCORE = 21500

        SETUP_PLACE_SCORE = 21000
        # In deckgym, Professor's Research draws 2 cards WITHOUT discarding hand.
        # Prioritizing it allows finding better options before committing resources.
        SETUP_RESEARCH_SCORE = 22500

        SETUP_ABILITY_SCORE = 19500
        SETUP_ITEM_SCORE = 19000
        SETUP_SUPPORTER_SCORE = 14000 # Generic

        LETHAL_KO_SCORE = 15000
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
                    base_dmg = 0
                    if my_active:
                         dmg = calculate_damage(my_active, idx, my_bench, opp_active, opp_bench_count, opp_energy_count)
                         base_dmg = calculate_base_damage(my_active, idx)

                    details["damage"] = dmg
                    details["score"] = ATTACK_BASE_SCORE + (dmg * 10)

                    # Lethal Check
                    if opp_active_hp > 0:
                        if base_dmg >= opp_active_hp:
                            details["score"] += LETHAL_KO_SCORE
                            details["can_ko"] = True
                            if opp_bench_count == 0:
                                details["score"] += LETHAL_WIN_SCORE
                                details["is_lethal"] = True
                        elif dmg >= opp_active_hp:
                            details["score"] += 15000 # Probabilistic
                            details["can_ko"] = True

                    # Mewtwo ex Psydrive penalty
                    if "mewtwo ex" in my_active_name.lower() and idx == 1:
                        if not details.get("is_lethal"):
                             if opp_active_hp <= 50:
                                 details["score"] -= 2000

            elif "AttachTool" in aname:
                m = re_attach_tool.search(aname)
                if m:
                    details["type"] = "tool"
                    details["card_name"] = clean_name(m.group(1))
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

                     target_card = None
                     if pos == 0: target_card = my_active
                     elif pos > 0 and pos <= len(my_bench_raw): target_card = my_bench_raw[pos-1]

                     if target_card:
                         if pos == 0 and needs_energy(target_card):
                             details["score"] += 800
                         elif needs_energy(target_card):
                             details["score"] += 500

                         cname = get_card_name(target_card)
                         ctype = get_energy_type(cname)
                         if ctype in etype or etype in ctype:
                             details["score"] += 200

                         if not needs_energy(target_card):
                             details["score"] -= 500
                     else:
                         details["score"] -= 1000
                 else:
                     details["type"] = "tool"
                     details["score"] = SETUP_ITEM_SCORE

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
                         if hand_idx < len(my_hand):
                             card_name = get_card_name(my_hand[hand_idx])
                         else:
                             card_name = "Unknown"

                 if pos != -1:
                     details["type"] = "place"
                     details["card_name"] = card_name
                     details["pos"] = pos
                     details["score"] = SETUP_PLACE_SCORE

                     # Misty Prep: Only boost Water types!
                     if has_misty_in_hand and len(my_bench) < 3:
                         if "Water" in get_energy_type(card_name):
                             details["score"] = MISTY_PREP_PLACE_SCORE

                     # DONK PREVENTION
                     if len(my_bench) == 0:
                         details["score"] = DONK_PREVENTION_SCORE

                     if len(my_bench) < 3: details["score"] += 500

                     if my_active:
                         aname = get_card_name(my_active)
                         atype = get_energy_type(aname)
                         ctype = get_energy_type(card_name)
                         if atype == ctype: details["score"] += 1000

                     if "pikachu ex" in my_active_name.lower() and len(my_bench) < 5:
                         details["score"] += 500

            elif "Evolve" in aname:
                m = re_evolve.search(aname)
                if m:
                    card_name = clean_name(m.group(1))
                    pos = int(m.group(2))
                    details["type"] = "evolve"
                    details["card_name"] = card_name
                    details["pos"] = pos
                    details["score"] = SETUP_EVOLVE_SCORE
                    if pos == 0: details["score"] += 500

            elif "UseSupporter" in aname or ("Play" in aname and not "Pokemon" in aname):
                is_supporter = False
                supporters = ["Research", "Professor", "Sabrina", "Giovanni", "Erika", "Misty", "Blaine", "Koga", "Lt. Surge", "Brock", "Copycat", "Lisia", "Cyrus", "Mars", "Red", "Guzma", "Judge", "Acerola", "Hau", "Bill", "Pokemon Center Lady", "Pokémon Center Lady", "Ilima", "Clemont", "Sony"]
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
                        details["score"] = SETUP_RESEARCH_SCORE
                        if len(my_hand) < 8: details["score"] += 200
                        else: details["score"] -= 2000 # Penalize heavily if hand is full to prioritize playing cards first
                    elif "Clemont" in sname or "Sony" in sname:
                        details["score"] = SETUP_SEARCH_SUPPORTER_SCORE
                    elif "Sabrina" in sname:
                        if len(my_hand) >= 3:
                            if opp_active and opp_energy_count >= 3:
                                details["score"] = SETUP_EVOLVE_SCORE # Emergency
                            elif opp_active and opp_energy_count >= 2:
                                details["score"] = 17000
                        else:
                            details["score"] -= 2000

                        if opp_active_hp > 0 and opp_active_hp <= 60: details["score"] -= 8000
                    elif "Misty" in sname:
                        needs_water = False
                        if "Water" in get_energy_type(my_active_name) and needs_energy(my_active): needs_water = True
                        for b in my_bench:
                             if "Water" in get_energy_type(get_card_name(b)) and needs_energy(b): needs_water = True

                        if needs_water: details["score"] = SETUP_MISTY_SCORE
                        else: details["score"] -= 500
                else:
                    details["type"] = "item"
                    details["score"] = SETUP_ITEM_SCORE
                    if "Ball" in aname:
                        details["score"] = SETUP_SEARCH_ITEM_SCORE
                    elif "Potion" in aname or "Heal" in aname:
                         if my_active and get_card_hp(my_active) <= (get_card_max_hp(my_active) - 20):
                             details["score"] = SETUP_HIGH_PRIORITY_ITEM_SCORE
                         elif my_active and get_card_hp(my_active) < get_card_max_hp(my_active):
                             details["score"] += 500
                         else:
                             details["score"] = -500
                    elif "Switch" in aname or "Speed" in aname:
                         active_dmg = 0
                         if my_active:
                             a_attacks = get_attacks(my_active_name)
                             for i in range(len(a_attacks)):
                                  if my_active_energy >= len(a_attacks[i].get("cost", [])):
                                       d = calculate_damage(my_active, i, my_bench, opp_active, opp_bench_count, opp_energy_count)
                                       if d > active_dmg: active_dmg = d
                         if active_dmg < 40:
                             details["score"] = SETUP_HIGH_PRIORITY_ITEM_SCORE

                    elif "Red Card" in aname:
                         if opp_hand_count >= 3: details["score"] += 500
                         else: details["score"] -= 10000

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
                details["score"] = LETHAL_WIN_SCORE

                if my_active and get_card_hp(my_active) > 0:
                     details["score"] = SETUP_ABILITY_SCORE
                else:
                     if details.get("target_pos") is not None:
                         t_pos = details["target_pos"]
                         if t_pos < len(my_bench_raw):
                             b = my_bench_raw[t_pos]
                             if b:
                                 e_count = len(get_card_energy(b))
                                 details["score"] += (e_count * 1000)

            elif "ApplyDamage" in aname:
                 details["type"] = "damage_resolution"
                 details["score"] = LETHAL_WIN_SCORE

            elif "UseAbility" in aname:
                details["type"] = "ability"
                details["score"] = SETUP_ABILITY_SCORE

            elif "DiscardOwnCard" in aname:
                details["type"] = "discard"
                m = re_discard.search(aname)
                if m: details["card_name"] = clean_name(m.group(1))
                details["score"] = 0

                cname = details.get("card_name", "Unknown").lower()
                if "ex" in cname: details["score"] -= 1000
                elif "research" in cname or "gio" in cname or "sabrina" in cname: details["score"] -= 500
                elif "energy" in cname: details["score"] += 100
                else: details["score"] += 200

            parsed_actions.append(details)

        # --- 6. Post-Processing & Special Heuristics ---

        has_lethal_attack = any(a.get("is_lethal") for a in parsed_actions if a["type"] == "attack")
        has_ko_attack = any(a.get("can_ko") for a in parsed_actions if a["type"] == "attack")

        # A. Lethal Retreat & Strategic Switch
        for action in parsed_actions:
            if action["type"] == "retreat" or (action["type"] == "activate" and my_active and get_card_hp(my_active) > 0):
                target_pos = action.get("target_pos", -1)

                target_mon = None
                # Fix: Simulator uses 1-based indexing for bench targets in actions
                if action["type"] == "activate" and target_pos == 0:
                     target_mon = my_active
                elif target_pos > 0 and target_pos <= len(my_bench_raw):
                     target_mon = my_bench_raw[target_pos-1]

                if target_mon:
                    t_name = get_card_name(target_mon)
                    t_attacks = get_attacks(t_name)
                    t_energy = len(get_card_energy(target_mon))
                    max_dmg = 0
                    for i in range(len(t_attacks)):
                        cost = len(t_attacks[i].get("cost", []))
                        if t_energy >= cost:
                            d = calculate_damage(target_mon, i, my_bench, opp_active, opp_bench_count, opp_energy_count)
                            if d > max_dmg: max_dmg = d

                    if opp_active_hp > 0 and max_dmg >= opp_active_hp:
                            if opp_bench_count == 0:
                                action["score"] = LETHAL_WIN_SCORE
                            elif not has_ko_attack:
                                action["score"] = 14500
                            action["is_lethal_switch"] = True

                    # Strategic Switch / Retreat for Damage
                    active_dmg = 0
                    if my_active:
                            a_attacks = get_attacks(my_active_name)
                            for i in range(len(a_attacks)):
                                if my_active_energy >= len(a_attacks[i].get("cost", [])):
                                    d = calculate_damage(my_active, i, my_bench, opp_active, opp_bench_count, opp_energy_count)
                                    if d > active_dmg: active_dmg = d

                    # Only apply Strategic Switch if the target deals significantly more damage (60+ diff)
                    # and the Active is dealing weak damage (<30).
                    # STRICT THRESHOLD: Active < 30 AND Bench >= 60
                    if not has_lethal_attack and active_dmg < 30 and max_dmg >= 60:
                            action["score"] = STRATEGIC_SWITCH_SCORE

        # B. Emergency Retreat
        if my_active and get_card_hp(my_active) <= 40 and opp_active and len(get_card_energy(opp_active)) > 0:
            for action in parsed_actions:
                if action["type"] == "retreat":
                    # Score retreat targets based on readiness
                    base_score = 30000
                    target_pos = action.get("target_pos", -1)
                    if target_pos > 0 and target_pos <= len(my_bench_raw):
                         target_mon = my_bench_raw[target_pos-1]
                         if target_mon:
                             base_score += get_card_hp(target_mon)
                             base_score += len(get_card_energy(target_mon)) * 100

                    action["score"] = base_score

        # C. Giovanni for Lethal
        has_giovanni = False
        gio_action = None
        for a in parsed_actions:
            if a["type"] == "supporter" and "Giovanni" in a.get("supporter_name", ""):
                has_giovanni = True
                gio_action = a
                break

        if has_giovanni:
            for a in parsed_actions:
                if a["type"] == "attack":
                    dmg = a.get("damage", 0)
                    if opp_active_hp > 0 and dmg < opp_active_hp and (dmg + 10) >= opp_active_hp:
                        gio_action["score"] = 22000
                        if opp_bench_count == 0: gio_action["score"] = LETHAL_WIN_SCORE + 100

        # D. Mewtwo ex Psydrive check
        mewtwo_attacks = [a for a in parsed_actions if a["type"] == "attack" and "mewtwo ex" in my_active_name.lower()]
        psydrive = next((a for a in mewtwo_attacks if a["idx"] == 1), None)
        standard = next((a for a in mewtwo_attacks if a["idx"] == 0), None)

        if psydrive and standard:
            # If standard is enough to KO or is lethal, penalize Psydrive to save energy
            if standard.get("is_lethal") or standard.get("can_ko"):
                psydrive["score"] -= 2000

        # E. Desperation Mode
        if is_desperate:
             # Boost KO actions if not already lethal
             for a in parsed_actions:
                 if a["type"] == "attack" and a.get("can_ko"):
                     a["score"] += 5000 # Prioritize KO at all costs

        # --- 7. Selection ---
        best_score = -float('inf')
        best_action_id = legal_actions[0]

        for action in parsed_actions:
            if action["score"] > best_score:
                best_score = action["score"]
                best_action_id = action["id"]

        logger.debug(f"Turn: {state.turn if hasattr(state, 'turn') else '?'} | Player: {me}")
        for a in parsed_actions:
            if a["score"] > -5000:
                 logger.debug(f"Action: {a['name']} | Type: {a['type']} | Score: {a['score']}")
        logger.debug(f"Selected: {game.action_name(best_action_id)}")

        return best_action_id

    except Exception as e:
        logger.error(f"Error in play: {e}")
        return legal_actions[0]
