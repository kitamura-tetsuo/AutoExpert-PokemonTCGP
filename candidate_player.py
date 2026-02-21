
import re
import random
import sys
import logging

# Setup logging
logging.basicConfig(filename='player.log', level=logging.INFO, filemode='w', format='%(asctime)s - %(message)s')

# --- Card Database (Simplified & Normalized) ---
# All keys lowercase
CARD_DB = {
    # Extracted from database.json
    "pikachu ex": {"hp": 120, "energy_type": "lightning", "retreat": 1, "attacks": [{"name": "Circle Circuit", "cost": ["Lightning", "Lightning"], "dmg": 30, "bench_scale": True}]},
    "mewtwo ex": {"hp": 150, "energy_type": "psychic", "retreat": 2, "attacks": [{"name": "Psychic Sphere", "cost": ["Psychic", "Colorless"], "dmg": 50}, {"name": "Psydrive", "cost": ["Psychic", "Psychic", "Colorless", "Colorless"], "dmg": 150, "discard": 2}]},
    "charizard ex": {"hp": 180, "energy_type": "fire", "retreat": 2, "attacks": [{"name": "Slash", "cost": ["Fire", "Colorless"], "dmg": 60}, {"name": "Crimson Storm", "cost": ["Fire", "Fire", "Colorless", "Colorless"], "dmg": 200, "discard": 2}]},
    "starmie ex": {"hp": 130, "energy_type": "water", "retreat": 0, "attacks": [{"name": "Hydro Splash", "cost": ["Water", "Water"], "dmg": 90}]},
    "articuno ex": {"hp": 140, "energy_type": "water", "retreat": 2, "attacks": [{"name": "Ice Wing", "cost": ["Water", "Colorless"], "dmg": 40}, {"name": "Blizzard", "cost": ["Water", "Water", "Water"], "dmg": 80, "bench_dmg": 10}]},
    "venusaur ex": {"hp": 190, "energy_type": "grass", "retreat": 3, "attacks": [{"name": "Razor Leaf", "cost": ["Grass", "Colorless", "Colorless"], "dmg": 60}, {"name": "Giant Bloom", "cost": ["Grass", "Grass", "Colorless", "Colorless"], "dmg": 100, "heal": 30}]},
    "blastoise ex": {"hp": 180, "energy_type": "water", "retreat": 3, "attacks": [{"name": "Surf", "cost": ["Water", "Colorless"], "dmg": 40}, {"name": "Hydro Bazooka", "cost": ["Water", "Water", "Colorless"], "dmg": 100, "extra_energy_dmg": 60}]},
    "machamp ex": {"hp": 180, "energy_type": "fighting", "retreat": 3, "attacks": [{"name": "Mega Punch", "cost": ["Fighting", "Fighting", "Fighting"], "dmg": 120}]},
    "zapdos ex": {"hp": 130, "energy_type": "lightning", "retreat": 1, "attacks": [{"name": "Peck", "cost": ["Lightning"], "dmg": 20}, {"name": "Thundering Hurricane", "cost": ["Lightning", "Lightning", "Lightning"], "dmg": 50, "coin_flips": 4}]},
    "moltres ex": {"hp": 140, "energy_type": "fire", "retreat": 2, "attacks": [{"name": "Inferno Dance", "cost": ["Fire"], "dmg": 0, "effect": "accelerate"}, {"name": "Heat Blast", "cost": ["Fire", "Colorless", "Colorless"], "dmg": 70}]},
    "marowak ex": {"hp": 140, "energy_type": "fighting", "retreat": 1, "attacks": [{"name": "Bonemerang", "cost": ["Fighting", "Fighting"], "dmg": 80, "coin_flips": 2}]},
    "gengar ex": {"hp": 170, "energy_type": "psychic", "retreat": 2, "attacks": [{"name": "Spooky Shot", "cost": ["Psychic", "Psychic", "Psychic"], "dmg": 100}]},
    "wigglytuff ex": {"hp": 140, "energy_type": "colorless", "retreat": 2, "attacks": [{"name": "Sleepy Song", "cost": ["Colorless", "Colorless", "Colorless"], "dmg": 80, "status": "Sleep"}]},
    "greninja": {"hp": 120, "energy_type": "water", "retreat": 1, "attacks": [{"name": "Mist Slash", "cost": ["Water", "Colorless"], "dmg": 60}]},
    "gardevoir": {"hp": 110, "energy_type": "psychic", "retreat": 2, "attacks": [{"name": "Psyshot", "cost": ["Psychic", "Psychic", "Colorless"], "dmg": 60}]},
    "dragonite": {"hp": 160, "energy_type": "dragon", "retreat": 3, "attacks": [{"name": "Draco Meteor", "cost": ["Water", "Lightning", "Colorless", "Colorless"], "dmg": 50, "random_target": 4}]},

    "kangaskhan": {"hp": 100, "retreat": 3, "energy_type": "colorless"},
    "farfetch'd": {"hp": 60, "retreat": 1, "energy_type": "colorless"},
    "tauros": {"hp": 100, "retreat": 2, "energy_type": "colorless"},
    "snorlax": {"hp": 150, "retreat": 4, "energy_type": "colorless"},
    "mewtwo": {"hp": 120, "retreat": 2, "energy_type": "psychic"},
    "articuno": {"hp": 100, "retreat": 1, "energy_type": "water"},
    "zapdos": {"hp": 100, "retreat": 1, "energy_type": "lightning"},
    "moltres": {"hp": 100, "retreat": 1, "energy_type": "fire"},
    "ralts": {"hp": 60, "retreat": 1, "energy_type": "psychic"},
    "gastly": {"hp": 60, "retreat": 1, "energy_type": "psychic"},
    "abra": {"hp": 60, "retreat": 1, "energy_type": "psychic"},
    "pikachu": {"hp": 60, "retreat": 1, "energy_type": "lightning"},
    "staryu": {"hp": 50, "retreat": 1, "energy_type": "water"},
    "charmander": {"hp": 60, "retreat": 1, "energy_type": "fire"},
    "squirtle": {"hp": 60, "retreat": 1, "energy_type": "water"},
    "bulbasaur": {"hp": 70, "retreat": 1, "energy_type": "grass"},
}

def play(state, game):
    """
    Advanced Pokemon TCG Pocket Player (v4 - Added Items)
    """
    legal_actions = game.legal_actions()
    if not legal_actions:
        return 0

    try:
        # --- 1. Helper Functions ---

        def get_card_name(card_obj):
            if not card_obj: return None
            return getattr(card_obj, "name", "Unknown")

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

            if any(x in n for x in ["pikachu", "zapdos", "raichu", "magneton", "electrode"]): return "lightning"
            if any(x in n for x in ["mewtwo", "ralts", "kirlia", "gardevoir", "gengar"]): return "psychic"
            if any(x in n for x in ["starmie", "articuno", "blastoise", "greninja"]): return "water"
            if any(x in n for x in ["charizard", "moltres", "arcanine"]): return "fire"
            if any(x in n for x in ["venusaur", "exeggutor"]): return "grass"
            if any(x in n for x in ["machamp", "marowak", "golem"]): return "fighting"
            if any(x in n for x in ["dragonite"]): return "dragon"
            if any(x in n for x in ["melmetal"]): return "metal"
            if any(x in n for x in ["weavile", "muk"]): return "darkness"
            return "colorless"

        def calculate_damage(attacker_card, attack_idx, my_bench_len, opp_active_hp):
            name = get_card_name(attacker_card)
            if not name: return 0
            n_lower = name.lower()

            if n_lower in CARD_DB and "attacks" in CARD_DB[n_lower]:
                attacks_db = CARD_DB[n_lower]["attacks"]
                if attack_idx < len(attacks_db):
                    atk = attacks_db[attack_idx]
                    base = atk.get("dmg", 0)

                    if atk.get("bench_scale"):
                        return 30 * my_bench_len

                    if "coin_flips" in atk:
                        return base * 0.5 * atk["coin_flips"]

                    if "extra_energy_dmg" in atk:
                        energies = get_card_energy(attacker_card)
                        if len(energies) >= len(atk["cost"]) + 2:
                            return base + atk["extra_energy_dmg"]
                        return base

                    if base > 0:
                        return base

            attacks_obj = getattr(attacker_card, "attacks", [])
            if attack_idx < len(attacks_obj):
                atk_obj = attacks_obj[attack_idx]
                fixed = getattr(atk_obj, "fixed_damage", 0)
                if fixed > 0:
                    return fixed

            return 0

        def needs_energy(card_obj):
            name = get_card_name(card_obj)
            if not name: return False
            n_lower = name.lower()
            current_energy = get_card_energy(card_obj)

            if n_lower in CARD_DB and "attacks" in CARD_DB[n_lower]:
                attacks = CARD_DB[n_lower]["attacks"]
                max_cost = 0
                for atk in attacks:
                    cost = atk.get("cost", [])
                    if len(cost) > max_cost:
                        max_cost = len(cost)
                return len(current_energy) < max_cost

            if "ex" in n_lower: return len(current_energy) < 3
            return len(current_energy) < 2

        # --- 2. Parse State ---
        me = state.current_player
        opp = 1 - me

        my_active = state.get_active_pokemon(me)
        my_bench = [b for b in state.get_bench_pokemon(me) if b is not None]
        my_hand = state.get_hand(me)

        opp_active = state.get_active_pokemon(opp)
        opp_bench = [b for b in state.get_bench_pokemon(opp) if b is not None]

        my_active_name = get_card_name(my_active)
        my_active_hp = get_card_hp(my_active)
        opp_active_hp = get_card_hp(opp_active) if opp_active else 0

        # Categorize Actions
        acts = {
            "attack": [], "attach_energy": [], "attach_tool": [],
            "evolve": [], "place_basic": [], "place_active": [], "play_supporter": [],
            "play_item": [], "ability": [], "retreat": [],
            "activate": [], "end": []
        }

        for aid in legal_actions:
            aname = game.action_name(aid)

            if aname == "EndTurn": acts["end"].append(aid)
            elif aname.startswith("Attack("):
                m = re.search(r"Attack\((\d+)\)", aname)
                if m: acts["attack"].append((aid, int(m.group(1))))
            elif aname.startswith("AttachTool"):
                m = re.search(r"AttachTool\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
                if m: acts["attach_tool"].append((aid, m.group(1).replace(")", ""), int(m.group(2))))
            elif aname.startswith("Attach"):
                if "Tool" in aname: continue
                m = re.search(r"Attach\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
                if m: acts["attach_energy"].append((aid, m.group(1).replace(")", ""), int(m.group(2))))
                else:
                    m = re.search(r"AttachEnergy\((\d+), (.*?)\)", aname)
                    if m: acts["attach_energy"].append((aid, m.group(2), int(m.group(1))))
            elif aname.startswith("Evolve"):
                m = re.search(r"Evolve\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
                if m: acts["evolve"].append((aid, m.group(1).replace(")", ""), int(m.group(2))))
            elif aname.startswith("Place") or aname.startswith("PlayPokemon"):
                 m = re.search(r"Place\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
                 if m:
                     if int(m.group(2)) == 0: acts["place_active"].append((aid, m.group(1).replace(")", "")))
                     else: acts["place_basic"].append((aid, m.group(1).replace(")", ""), int(m.group(2))))
                 elif "PlayPokemon" in aname:
                     if ", 0)" in aname: acts["place_active"].append((aid, "Unknown"))
                     else: acts["place_basic"].append((aid, "Unknown", -1))
            elif aname.startswith("Play") or aname.startswith("UseItem") or aname.startswith("UseSupporter"):
                target = -1
                m_t = re.search(r", (\d+)\)", aname)
                if m_t: target = int(m_t.group(1))
                m_n = re.search(r"Some\((.*?)\)", aname)
                if m_n: card_name = m_n.group(1).replace(")", "")
                else: card_name = aname

                supporters = ["Research", "Sabrina", "Giovanni", "Erika", "Misty", "Blaine", "Koga", "Lt. Surge", "Brock", "Copycat", "Lisia", "Cyrus", "Mars", "Red", "Guzma", "Judge", "Acerola", "Hau", "Bill"]
                if any(s in card_name for s in supporters):
                    acts["play_supporter"].append((aid, card_name, target))
                else:
                    acts["play_item"].append((aid, card_name, target))
            elif aname.startswith("UseAbility"):
                m = re.search(r"UseAbility\((\d+)\)", aname)
                if m: acts["ability"].append((aid, int(m.group(1))))
            elif aname.startswith("Retreat"):
                acts["retreat"].append(aid)
            elif aname.startswith("Activate"):
                m = re.search(r"Activate\((\d+)\)", aname)
                if m: acts["activate"].append((aid, int(m.group(1))))

        # --- 3. Strategy ---
        logging.info(f"Turn: {state.turn_count}, P{me} (HP: {my_active_hp}) vs P{opp} (HP: {opp_active_hp})")

        # A. Win Condition (Lethal)
        if acts["attack"] and opp_active:
            giovanni = [a for a in acts["play_supporter"] if "Giovanni" in a[1]]

            for aid, idx in acts["attack"]:
                dmg = calculate_damage(my_active, idx, len(my_bench), opp_active_hp)

                if dmg >= opp_active_hp:
                    logging.info(f"Lethal found: Attack {idx} ({dmg} dmg) >= HP {opp_active_hp}")
                    return aid

                if giovanni and (dmg + 10) >= opp_active_hp:
                    logging.info("Lethal with Giovanni found")
                    return giovanni[0][0]

        # B. Forced Switch (Activate)
        if acts["activate"]:
            if not my_active or my_active_hp == 0:
                best_cand = acts["activate"][0][0]
                max_score = -2000

                for aid, idx in acts["activate"]:
                    if idx >= len(my_bench): continue
                    c = my_bench[idx]
                    if not c: continue
                    name = get_card_name(c)

                    score = 0
                    is_ex = "ex" in name.lower()
                    energy_count = len(get_card_energy(c))

                    if not needs_energy(c): score += 500
                    elif energy_count > 0: score += 100 * energy_count

                    if is_ex: score += 50
                    else: score -= 50

                    if "mewtwo" in name.lower(): score += 10
                    if "pikachu" in name.lower(): score += 10

                    if score > max_score:
                        max_score = score
                        best_cand = aid
                return best_cand
            else:
                return acts["activate"][0][0]

        # C. Place Active (Start of Game)
        if acts["place_active"]:
            best_active = acts["place_active"][0][0]
            max_score = -1000
            for aid, name in acts["place_active"]:
                score = 0
                n = name.lower()

                if n in CARD_DB:
                    hp = CARD_DB[n].get("hp", 60)
                    ret = CARD_DB[n].get("retreat", 1)
                    score += hp
                    score -= (ret * 10)

                if "ex" in n: score += 50
                if "pikachu" in n: score += 40
                if "articuno" in n: score += 40
                if "kangaskhan" in n: score += 60

                if score > max_score:
                    max_score = score
                    best_active = aid
            return best_active

        # D. Setup Phase

        # 1. Evolve
        if acts["evolve"]:
            return acts["evolve"][0][0]

        # 2. Abilities
        if acts["ability"]:
            for aid, idx in acts["ability"]:
                user = my_active if idx == 0 else (my_bench[idx-1] if idx-1 < len(my_bench) else None)
                if user:
                    n = get_card_name(user).lower()
                    if "gardevoir" in n: return aid
                    if "greninja" in n: return aid
                    if "pidgeot" in n: return aid
            return acts["ability"][0][0]

        # 3. Bench Placement
        if acts["place_basic"]:
            if len(my_bench) < 3:
                best_bp = None
                best_score = -100

                for aid, name, _ in acts["place_basic"]:
                    score = 0
                    n = name.lower()
                    if "ex" in n: score += 100
                    if "pikachu" in n: score += 80
                    if "ralts" in n: score += 60
                    if "froakie" in n: score += 60
                    if "articuno" in n: score += 70

                    if score > best_score:
                        best_score = score
                        best_bp = aid

                if best_bp and best_score > 0:
                    return best_bp

        # 4. Supporters
        if acts["play_supporter"]:
            # Misty
            misty = [a for a in acts["play_supporter"] if "Misty" in a[1]]
            if misty:
                if my_active and "water" in get_energy_type(my_active_name) and needs_energy(my_active):
                    for aid, _, target in misty:
                        if target == 0: return aid
                for i, b in enumerate(my_bench):
                    if b and "water" in get_energy_type(get_card_name(b)) and needs_energy(b):
                         for aid, _, target in misty:
                             if target == i + 1: return aid

            # Research
            research = [a for a in acts["play_supporter"] if "Research" in a[1]]
            if research:
                if len(my_hand) <= 5: return research[0][0]

            # Sabrina
            sabrina = [a for a in acts["play_supporter"] if "Sabrina" in a[1]]
            if sabrina and opp_bench:
                can_kill_active = False
                max_dmg = 0
                if acts["attack"]:
                     for _, idx in acts["attack"]:
                         d = calculate_damage(my_active, idx, len(my_bench), opp_active_hp)
                         max_dmg = max(max_dmg, d)
                if max_dmg >= opp_active_hp: can_kill_active = True

                if not can_kill_active and opp_active_hp > 60:
                    return sabrina[0][0]

        # 5. Attach Energy
        if acts["attach_energy"]:
            best_attach = None
            max_score = -1000

            for aid, type_str, pos in acts["attach_energy"]:
                score = 0
                target = my_active if pos == 0 else (my_bench[pos-1] if pos-1 < len(my_bench) else None)
                if not target: continue

                t_name = get_card_name(target)
                t_type = get_energy_type(t_name)
                type_str_lower = type_str.lower()

                match = (type_str_lower == t_type) or (t_type == "colorless")

                if needs_energy(target):
                    score += 100
                    if pos == 0: score += 50
                    if match: score += 20
                    if "ex" in t_name.lower(): score += 30
                    if "mewtwo" in t_name.lower() and "psychic" in type_str_lower: score += 40
                    if "pikachu" in t_name.lower() and "lightning" in type_str_lower: score += 40
                else:
                    score -= 50

                if score > max_score:
                    max_score = score
                    best_attach = aid

            if best_attach and max_score > 0:
                return best_attach

        # 6. Items (New)
        if acts["play_item"]:
            # Potion
            potion = [a for a in acts["play_item"] if "Potion" in a[1]]
            if potion and my_active and my_active_hp > 0 and my_active_hp < get_card_max_hp(my_active):
                return potion[0][0]

            # Poke Ball
            pokeball = [a for a in acts["play_item"] if "Ball" in a[1]]
            if pokeball and len(my_bench) < 3:
                return pokeball[0][0]

            # Red Card
            redcard = [a for a in acts["play_item"] if "Red Card" in a[1]]
            if redcard:
                # Use if we are behind or just to disrupt?
                # Simple logic: use it
                return redcard[0][0]

            # Any other item
            return acts["play_item"][0][0]

        # 7. Retreat
        if acts["retreat"] and my_active:
            if my_active_hp <= 40 and my_bench:
                 has_better = False
                 for b in my_bench:
                     if b and not needs_energy(b) and get_card_hp(b) > 50:
                         has_better = True
                         break
                 if has_better:
                     return acts["retreat"][0]

        # 8. Attack
        if acts["attack"]:
            best_atk = acts["attack"][0][0]
            max_dmg = -1

            for aid, idx in acts["attack"]:
                d = calculate_damage(my_active, idx, len(my_bench), opp_active_hp)
                if d > max_dmg:
                    max_dmg = d
                    best_atk = aid

            return best_atk

        # 9. End Turn
        if acts["end"]:
            return acts["end"][0]

        return legal_actions[0]

    except Exception as e:
        logging.error(f"Error in play: {e}")
        return legal_actions[0]
