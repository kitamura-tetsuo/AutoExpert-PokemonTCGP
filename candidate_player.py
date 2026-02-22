
import re
import random
import logging
import math
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
    "magnemite": {"hp": 50, "energy_type": "Lightning", "attacks": [{"dmg": 30}]},
    "pichu": {"hp": 30, "energy_type": "Lightning", "attacks": [{"dmg": 10, "scaling": True}]},
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

        # --- NEW 1-STEP LOOKAHEAD EVALUATION ---
        def evaluate_deterministic_board_internal(state_obj, my_p_id):
            score = 0
            opp_p_id = 1 - my_p_id
            
            if getattr(state_obj, "is_game_over", lambda: False)():
                if f"Win({my_p_id})" in str(getattr(state_obj, "winner", "")): return 999999
                if f"Win({opp_p_id})" in str(getattr(state_obj, "winner", "")): return -999999
                return 0
                
            def _eval_c(card, is_mine):
                if not card: return 0
                s = 0
                hp = get_card_hp(card)
                s += hp * 1
                cname = get_card_name(card)
                req_type = get_energy_type(cname).lower()
                
                energies = get_card_energy(card)
                for e in energies:
                    e_lower = e.lower()
                    if req_type in e_lower or req_type == "colorless" or "colorless" in req_type:
                        s += 50
                    else:
                        s += 20
                        
                if needs_energy(card):
                    s += 10
                    
                if "ex" in cname.lower():
                    s += 20
                    
                if not is_mine: return -s
                return s

            if hasattr(state_obj, "points"):
                score += state_obj.points[my_p_id] * 5000
                score -= state_obj.points[opp_p_id] * 5000
            
            if hasattr(state_obj, "get_active_pokemon"):
                my_active_pt = state_obj.get_active_pokemon(my_p_id)
                opp_active_pt = state_obj.get_active_pokemon(opp_p_id)
                score += _eval_c(my_active_pt, True) * 5 # Heavy weight on active
                score += _eval_c(opp_active_pt, False) * 2
                
                # Danger Detection: Can we be KO'd next turn?
                if my_active_pt and opp_active_pt:
                    my_hp = get_card_hp(my_active_pt)
                    opp_energy = len(get_card_energy(opp_active_pt))
                    # Estimate opp damage
                    opp_name = get_card_name(opp_active_pt)
                    opp_atks = get_attacks(opp_name)
                    max_opp_dmg = 0
                    for i, atk in enumerate(opp_atks):
                        cost = len(atk.get("cost", []))
                        if opp_energy >= cost or (opp_energy + 1 >= cost): # Thinking one turn ahead
                            dmg = calculate_damage(opp_active_pt, i, [], my_active_pt, 0)
                            if dmg > max_opp_dmg: max_opp_dmg = dmg
                    
                    if max_opp_dmg >= my_hp:
                        score -= 20000 # Extreme danger
            
            p_my_bench = []
            if hasattr(state_obj, "get_bench_pokemon"):
                p_my_bench = [p for p in state_obj.get_bench_pokemon(my_p_id) if p]
                for p in p_my_bench:
                    score += _eval_c(p, True)
                for p in state_obj.get_bench_pokemon(opp_p_id):
                    if p: score += _eval_c(p, False)
            
            # Bench Stability
            if not p_my_bench:
                score -= 10000 # Having no bench is very risky (Donk risk)
            else:
                score += len(p_my_bench) * 500
                    
            return score

        current_state_score = evaluate_deterministic_board_internal(state, me)
        best_action = legal_actions[0]
        best_total_score = -9999999
        
        def is_deterministic_action(aname_str, state_obj, my_p_id):
            if "DrawCard" in aname_str: return False
            if any(s in aname_str for s in ["Research", "Copycat", "Ilima", "Misty", "Red Card", "Acro Bike", "Speed"]): return False
            if "Attack" in aname_str:
                m = re_attack.search(aname_str)
                if m:
                    atk_idx = int(m.group(1))
                    my_active_pt = state_obj.get_active_pokemon(my_p_id)
                    if my_active_pt:
                        cname = get_card_name(my_active_pt).lower()
                        atks = get_attacks(cname)
                        if atk_idx < len(atks):
                            text = atks[atk_idx].get("text", "") or ""
                            if "coin" in text.lower() or "random" in text.lower() or "flip" in text.lower():
                                return False
                        if "marowak" in cname or ("zapdos" in cname and "ex" in cname) or "pidgeot" in cname:
                            return False
                        if "moltres ex" in cname and atk_idx == 0:
                            return False
                        if "articuno ex" in cname and atk_idx == 1:
                            return False
            return True

        for aid in legal_actions:
            aname = game.action_name(aid)
            
            # Base Bonus (to guide heuristics)
            action_bonus = 0
            
            if "EndTurn" in aname: action_bonus -= 1000
            elif "DrawCard" in aname: action_bonus += 300
            elif "Research" in aname:
                if len(my_hand) < 8: action_bonus += 200
                else: action_bonus -= 100
            elif "PokeBall" in aname or "Poké Ball" in aname: action_bonus += 150
            elif "Copycat" in aname or "Ilima" in aname: action_bonus += 100
            elif "Play(" in aname and not any(s in aname for s in supporters): action_bonus += 50
            elif "Misty" in aname: action_bonus += 80
            elif "Sabrina" in aname: action_bonus += 100
            elif "Giovanni" in aname: action_bonus += 50
            
            elif "Place(" in aname or "PlayPokemon" in aname:
                action_bonus += 100
                if "ex" in aname.lower(): action_bonus += 50
                if "0)" in aname: action_bonus += 100 # Active place
            elif "Evolve(" in aname: action_bonus += 150
            elif "AttachTool" in aname: action_bonus += 60
            elif "Attach(" in aname or "AttachEnergy" in aname: action_bonus += 80 
            elif "Retreat(" in aname: action_bonus -= 20
            elif "Attack(" in aname: action_bonus += 200
            
            # 1-Step Lookahead
            if is_deterministic_action(aname, state, me):
                try:
                    lookahead_env = game.clone()
                    lookahead_env.step_with_id(aid)
                    lookahead_state = lookahead_env.get_state()
                    
                    if getattr(lookahead_state, "is_game_over", lambda: False)():
                        if f"Win({me})" in str(getattr(lookahead_state, "winner", "")):
                            return aid
                            
                    board_score = evaluate_deterministic_board_internal(lookahead_state, me)
                except Exception as e:
                    logging.error(f"Error in lookahead for {aname}: {e}")
                    board_score = current_state_score
            else:
                board_score = current_state_score
                # Add expected values for non-deterministic actions
                if "Attack" in aname:
                    m = re_attack.search(aname)
                    if m:
                        d = calculate_damage(my_active, int(m.group(1)), my_bench, opp_active, len(opp_bench))
                        board_score += (d * 2)
                        if opp_active_hp > 0 and d >= opp_active_hp:
                            board_score += 10000 
                elif any(s in aname for s in ["Research", "Copycat", "Ilima", "Misty"]):
                    board_score += 150

            total_score = board_score + action_bonus
            
            if total_score > best_total_score:
                best_total_score = total_score
                best_action = aid
                
        return best_action

    except Exception as e:
        logging.error(f"Error in play: {e}")
        return legal_actions[0]

def evaluate_deterministic_board(state, my_p_id):
    # Base score
    score = 0
    opp_p_id = 1 - my_p_id
    
    # Game Over
    if getattr(state, "is_game_over", lambda: False)():
        if f"Win({my_p_id})" in str(getattr(state, "winner", "")): return 999999
        if f"Win({opp_p_id})" in str(getattr(state, "winner", "")): return -999999
        return 0 # Tie
        
    def _eval_card(card, is_mine):
        if not card: return 0
        s = 0
        hp = getattr(card, "remaining_hp", 0)
        s += hp * 1
        energy = getattr(card, "attached_energy", [])
        s += len(energy) * 50
        if not is_mine: return -s
        return s

    # Points
    if hasattr(state, "points"):
        score += state.points[my_p_id] * 5000
        score -= state.points[opp_p_id] * 5000
    
    # Active
    if hasattr(state, "get_active_pokemon"):
        my_active = state.get_active_pokemon(my_p_id)
        opp_active = state.get_active_pokemon(opp_p_id)
        score += _eval_card(my_active, True) * 2
        score += _eval_card(opp_active, False) * 2
        
    # Bench
    if hasattr(state, "get_bench_pokemon"):
        for p in state.get_bench_pokemon(my_p_id):
            if p: score += _eval_card(p, True)
        for p in state.get_bench_pokemon(opp_p_id):
            if p: score += _eval_card(p, False)
            
    return score
