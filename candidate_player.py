import re
import random
import logging
from typing import List, Dict, Optional, Tuple, Any

# Setup logging
logger = logging.getLogger("player")
if not logger.handlers:
    fh = logging.FileHandler('player.log', mode='w')
    fh.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    logger.addHandler(fh)
    logger.setLevel(logging.DEBUG)

try:
    from db_dump import CARD_DB
except ImportError:
    logger.warning("Could not import CARD_DB from db_dump. Using empty DB.")
    CARD_DB = {}

# --- Constants ---
# Priority Hierarchy:
# 1. Win Game (1M)
# 2. Prevent Loss (Donk) (500k)
# 3. Secure Prize (Gust Lethal) (80k)
# 4. Resource Free Setup (Misty) (78k)
# 5. Resource Commitment (Attach) (75k)
# 6. Board Development (Evolve, Place) (74k, 73k)
# 7. Item Usage (Before Discard) (72k)
# 8. Draw/Refresh (Research) (70k)
# 9. Attacks (Lethal KO > Base) (40k > 10k)

LETHAL_WIN_SCORE = 1000000
DONK_PREVENTION_SCORE = 500000

GUST_LETHAL_SCORE = 80000
MISTY_SCORE = 78000
MISTY_PREP_SCORE = 77000
ATTACH_ENERGY_SCORE = 75000
EVOLVE_SCORE = 74000
PLACE_BASIC_SCORE = 73000
ITEM_SCORE = 72000
RED_CARD_SCORE = 71000
RESEARCH_SCORE = 70000

ABILITY_SCORE = 50000
POTION_CRITICAL_SCORE = 67000

# Sub-priorities within categories
CARRY_BONUS = 2000
ACTIVE_WEAK_ATTACH_BONUS = 5000 # Boost attach if active needs retreat
LETHAL_KO_SCORE = 40000
STRATEGIC_SWITCH_SCORE = 30000
ATTACK_BASE_SCORE = 10000
RETREAT_SCORE = -5000
END_TURN_SCORE = -10000

CARRY_LIST = [
    "mewtwo ex", "pikachu ex", "charizard ex", "starmie ex", "venusaur ex",
    "blastoise ex", "dragonite", "gardevoir", "darkrai", "marowak ex",
    "weezing", "arbok", "zapdos ex", "articuno ex", "moltres ex",
    "machamp ex", "gengar ex", "wigglytuff ex", "nidoqueen", "nidoking",
    "mega altaria ex", "greninja ex", "greninja", "mega kangaskhan ex"
]

class Card:
    def __init__(self, debug_label, obj=None):
        self.debug_label = debug_label
        self.obj = obj
        self.raw_name = str(getattr(obj, "name", "")) if obj else ""
        if not self.raw_name: self.raw_name = "Unknown"
        self.name = self._clean_name(self.raw_name)
        self.db_entry = self._get_db_entry()
        self.hp = getattr(obj, "remaining_hp", 0) if obj else 0
        self.max_hp = getattr(obj, "total_hp", 0) if obj else 0
        self.energy = [str(e) for e in getattr(obj, "attached_energy", [])] if obj else []
        self.energy_count = len(self.energy)

    @staticmethod
    def _clean_name(raw_name):
        if not raw_name or raw_name == "Unknown": return "Unknown"
        if raw_name.startswith("Some(") and raw_name.endswith(")"):
            raw_name = raw_name[5:-1]

        # Remove prefix like PA007 or B1121
        m = re.match(r"^([A-Z0-9]+)?([A-Z][a-z].*)", raw_name)
        if m and m.group(1):
             prefix = m.group(1)
             name_part = m.group(2)
             if len(prefix) <= 6:
                 raw_name = name_part

        # Split CamelCase
        cleaned = re.sub(r"([a-z])([A-Z])", r"\1 \2", raw_name)

        if cleaned.endswith(" Ex"):
            cleaned = cleaned[:-3] + " ex"

        key = cleaned.lower()
        if key in CARD_DB:
            return CARD_DB[key].get("name", cleaned)

        # Fallback check
        for k in CARD_DB:
            if k in key: return CARD_DB[k].get("name", k.title())

        return cleaned

    def _get_db_entry(self):
        key = self.name.lower()
        if key in CARD_DB: return CARD_DB[key]
        for k in CARD_DB:
             if k == key: return CARD_DB[k]
        return None

    @property
    def energy_type(self):
        if self.db_entry:
            return self.db_entry.get("energy_type", "Colorless")
        n = self.name.lower()
        if "pikachu" in n or "zapdos" in n or "magneton" in n: return "Lightning"
        if "mewtwo" in n or "gardevoir" in n or "gengar" in n: return "Psychic"
        if "charizard" in n or "moltres" in n or "arcanine" in n: return "Fire"
        if "blastoise" in n or "starmie" in n or "greninja" in n or "articuno" in n: return "Water"
        if "venusaur" in n or "pinsir" in n: return "Grass"
        if "machamp" in n or "hitmonchan" in n: return "Fighting"
        return "Colorless"

    @property
    def attacks(self):
        if self.db_entry:
            return self.db_entry.get("attacks", [])
        return []

    @property
    def retreat_cost(self):
        if self.db_entry:
            return self.db_entry.get("retreat", 1)
        return 1

    def needs_energy(self):
        if self.db_entry:
            max_cost = 0
            attacks = self.attacks
            if not attacks:
                return False

            for atk in attacks:
                cost = len(atk.get("cost", []))
                if cost > max_cost: max_cost = cost

            if max_cost == 0:
                return False

            if "pikachu ex" in self.name.lower():
                max_cost = 2

            return self.energy_count < max_cost

        # Fallback for cards NOT in DB
        max_cost = 2
        n = self.name.lower()
        if "pikachu ex" in n: max_cost = 2
        elif "mewtwo ex" in n: max_cost = 4
        elif "charizard ex" in n: max_cost = 4
        elif "starmie ex" in n: max_cost = 2
        elif "greninja" in n: max_cost = 2
        elif "venusaur" in n: max_cost = 4
        elif "mega" in n and "ex" in n: max_cost = 4
        elif "ex" in n: max_cost = 3

        return self.energy_count < max_cost

class GameStateWrapper:
    def __init__(self, state):
        self.state = state
        self.me = state.current_player
        self.opp = 1 - self.me

        self.my_active_obj = state.get_active_pokemon(self.me)
        self.my_bench_objs = state.get_bench_pokemon(self.me)
        self.my_hand_objs = state.get_hand(self.me)

        self.opp_active_obj = state.get_active_pokemon(self.opp)
        self.opp_bench_objs = state.get_bench_pokemon(self.opp)
        self.opp_hand_objs = state.get_hand(self.opp)

        self.my_active = Card("Active", self.my_active_obj) if self.my_active_obj else None
        self.my_bench = [Card(f"Bench_{i}", b) for i, b in enumerate(self.my_bench_objs) if b]
        self.my_hand = [Card(f"Hand_{i}", h) for i, h in enumerate(self.my_hand_objs)]

        self.opp_active = Card("OppActive", self.opp_active_obj) if self.opp_active_obj else None
        self.opp_bench = [Card(f"OppBench_{i}", b) for i, b in enumerate(self.opp_bench_objs) if b]
        self.opp_hand_count = len(self.opp_hand_objs)

        self.my_points = state.points[self.me]
        self.opp_points = state.points[self.opp]

    def get_card_in_hand(self, idx):
        if 0 <= idx < len(self.my_hand):
            return self.my_hand[idx]
        return None

    def find_hand_card_by_name(self, target_raw_name):
        target_clean = Card._clean_name(target_raw_name)
        for c in self.my_hand:
            if c.name == target_clean:
                return c
        return None

    def get_bench_card(self, idx):
        if 0 <= idx < len(self.my_bench):
            return self.my_bench[idx]
        return None

def can_use_attack(cost, energy_provided):
    available = list(energy_provided)
    remaining_cost = []
    for c in cost:
        if c != "Colorless":
            if c in available:
                available.remove(c)
            else:
                return False
        else:
            remaining_cost.append(c)

    if len(available) >= len(remaining_cost):
        return True
    return False

def calculate_damage(attacker: Card, attack_idx: int, state: GameStateWrapper, extra_damage=0):
    if not attacker: return 0
    attacks = attacker.attacks
    if attack_idx >= len(attacks): return 0

    atk = attacks[attack_idx]
    damage = float(atk.get("dmg", 0))
    text = (atk.get("text") or "").lower()
    name_lower = attacker.name.lower()

    # 1. Coin Flips EV
    num_coins = atk.get("coin_flips", 0)
    if num_coins == 0:
        m = re.search(r"flip (\d+) coin", text)
        if m: num_coins = int(m.group(1))
        elif "flip a coin" in text: num_coins = 1

    if num_coins > 0:
        m_each = re.search(r"(\d+) damage for each heads", text)
        if m_each:
            dmg_per_head = int(m_each.group(1))
            damage = num_coins * 0.5 * dmg_per_head
        else:
            m_more = re.search(r"heads, this attack does (\d+) more damage", text)
            if m_more:
                bonus = int(m_more.group(1))
                damage += (num_coins * 0.5 * bonus)
            elif "tails, this attack does nothing" in text:
                 damage *= 0.5

    # 2. Scaling Damage
    if "damage for each" in text and "heads" not in text:
        multiplier = 20
        m_mult = re.search(r"(\d+) damage for each", text)
        if m_mult: multiplier = int(m_mult.group(1))

        count = 0
        if "benched" in text:
            if "opponent" in text:
                count = len(state.opp_bench)
            else:
                count = len(state.my_bench)
        elif "energy" in text:
            if "opponent" in text:
                if state.opp_active: count = state.opp_active.energy_count
            else:
                count = attacker.energy_count

        if damage <= 10:
             damage = count * multiplier
        else:
             damage += (count * multiplier)

    # 3. Specific Card Overrides
    if "pikachu ex" in name_lower and attack_idx == 0:
         count = 0
         for b in state.my_bench:
             if "lightning" in b.energy_type.lower(): count += 1
         damage = 30 * count

    if "mewtwo ex" in name_lower and attack_idx == 1:
        damage = 150

    if "starmie ex" in name_lower and attack_idx == 0:
        damage = 90

    if "charizard ex" in name_lower and attack_idx == 1:
        damage = 200

    if "marowak ex" in name_lower and attack_idx == 0:
         damage = 80

    damage += extra_damage

    # Check for opponent abilities that prevent damage
    if state.opp_active and state.opp_active.db_entry:
        ability = state.opp_active.db_entry.get("ability")
        if ability:
            effect = ability.get("effect", "").lower()
            if "prevent all damage" in effect and "pokémon ex" in effect:
                if "ex" in attacker.name.lower():
                    damage = 0

    return int(damage)

def play(state, game):
    legal_actions = game.legal_actions()
    if not legal_actions:
        return 0

    gs = GameStateWrapper(state)
    actions = []

    has_giovanni = any("giovanni" in c.name.lower() for c in gs.my_hand)
    extra_damage = 10 if has_giovanni else 0
    has_misty = any("misty" in c.name.lower() for c in gs.my_hand)

    has_lethal_on_board = False
    if gs.my_active and gs.opp_active:
        for idx in range(len(gs.my_active.attacks)):
            dmg = calculate_damage(gs.my_active, idx, gs, extra_damage)
            if dmg >= gs.opp_active.hp:
                has_lethal_on_board = True
                break

    can_win_on_bench = False
    can_ko_on_bench = False
    if gs.my_active:
        points_needed = 3 - gs.my_points
        for b in gs.opp_bench:
             for idx in range(len(gs.my_active.attacks)):
                 dmg = calculate_damage(gs.my_active, idx, gs, extra_damage)
                 if dmg >= b.hp:
                     can_ko_on_bench = True
                     is_ex = "ex" in b.name.lower()
                     points_gained = 2 if is_ex else 1
                     if points_gained >= points_needed:
                        can_win_on_bench = True
                     break
             if can_win_on_bench:
                 break

    for aid in legal_actions:
        aname = game.action_name(aid)
        action = {"id": aid, "name": aname, "score": 0, "type": "unknown"}
        aname_lower = aname.lower()

        if aname == "EndTurn":
            action["type"] = "end_turn"
            action["score"] = END_TURN_SCORE

        elif "Attack" in aname:
            m = re.search(r"Attack\((\d+)\)", aname)
            if m:
                idx = int(m.group(1))
                action["type"] = "attack"
                action["idx"] = idx
                action["damage"] = calculate_damage(gs.my_active, idx, gs, extra_damage=0)
                action["score"] = ATTACK_BASE_SCORE + action["damage"]

                if gs.opp_active:
                    if action["damage"] >= gs.opp_active.hp:
                        action["score"] = LETHAL_KO_SCORE
                        action["is_ko"] = True

                        points_needed = 3 - gs.my_points
                        is_ex = "ex" in gs.opp_active.name.lower()
                        points_gained = 2 if is_ex else 1

                        if points_gained >= points_needed or len(gs.opp_bench) == 0:
                            action["score"] = LETHAL_WIN_SCORE
                            action["is_lethal"] = True

                    elif has_giovanni and (action["damage"] + 10) >= gs.opp_active.hp:
                         action["can_be_lethal_with_giovanni"] = True

        elif "AttachEnergy" in aname:
            m = re.search(r"AttachEnergy\((\d+), (.*?)\)", aname)
            if m:
                action["type"] = "attach_energy"
                action["pos"] = int(m.group(1))
                action["energy_type"] = m.group(2)
                action["score"] = ATTACH_ENERGY_SCORE

        elif "Attach" in aname and "Tool" not in aname:
             m = re.search(r"Attach\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
             if m:
                 obj = m.group(1)
                 # Explicitly check for energy types to distinguish from Tools
                 if "Energy" in obj or any(t in obj for t in ["Lightning", "Water", "Fire", "Grass", "Fighting", "Psychic", "Darkness", "Metal"]):
                     action["type"] = "attach_energy"
                     action["pos"] = int(m.group(2))
                     action["energy_type"] = obj
                     action["score"] = ATTACH_ENERGY_SCORE
                 else:
                     action["type"] = "attach_tool"
                     action["score"] = ITEM_SCORE

        elif "Place" in aname or "PlayPokemon" in aname:
            m = re.search(r"(?:Place|PlayPokemon)\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
            if m:
                card_name_raw = m.group(1)
                pos = int(m.group(2))
                action["type"] = "place"
                action["pos"] = pos
                action["score"] = PLACE_BASIC_SCORE
                action["card_name"] = Card._clean_name(card_name_raw)

        elif "Evolve" in aname:
            action["type"] = "evolve"
            action["score"] = EVOLVE_SCORE

        elif "UseSupporter" in aname or "Play" in aname:
            if "research" in aname_lower or "professor" in aname_lower:
                action["type"] = "research"
                action["score"] = RESEARCH_SCORE
            elif "copycat" in aname_lower:
                action["type"] = "copycat"
                action["score"] = RESEARCH_SCORE
            elif "misty" in aname_lower:
                action["type"] = "misty"
                action["score"] = MISTY_SCORE
            elif "sabrina" in aname_lower or "boss" in aname_lower:
                action["type"] = "gust"
                action["score"] = ITEM_SCORE # Default, adjusted later
            elif "giovanni" in aname_lower:
                action["type"] = "giovanni"
                action["score"] = ITEM_SCORE
            elif "red card" in aname_lower:
                action["type"] = "red_card"
                action["score"] = RED_CARD_SCORE
            elif "ball" in aname_lower or "search" in aname_lower:
                action["type"] = "search_item"
                action["score"] = ITEM_SCORE # Boosted later
            elif "speed" in aname_lower:
                action["type"] = "x_speed"
                action["score"] = ITEM_SCORE
            elif "potion" in aname_lower or "heal" in aname_lower:
                action["type"] = "potion"
                action["score"] = ITEM_SCORE
            elif "brock" in aname_lower:
                action["type"] = "energy_retrieval"
                action["score"] = ITEM_SCORE
            else:
                action["type"] = "item"
                action["score"] = ITEM_SCORE

        elif "Retreat" in aname:
            m = re.search(r"Retreat\((\d+)\)", aname)
            if m:
                action["type"] = "retreat"
                bench_idx = int(m.group(1)) - 1
                action["target_idx"] = bench_idx
                action["score"] = RETREAT_SCORE

                target = gs.get_bench_card(bench_idx)
                if not target or target.name == "Unknown":
                    action["score"] = -100000

        elif "Activate" in aname:
            m = re.search(r"Activate\((\d+)\)", aname)
            if m:
                action["type"] = "activate"
                target_idx = int(m.group(1)) - 1

                # Check if we are activating for opponent (My active is alive)
                activating_for_opp = False
                if gs.my_active and gs.my_active.hp > 0:
                    activating_for_opp = True

                action["score"] = LETHAL_WIN_SCORE

                if activating_for_opp:
                    # We are choosing for OPPONENT. Pick the weakest/least dangerous.
                    # Assuming target_idx maps to gs.opp_bench list order
                    target = None
                    if target_idx < len(gs.opp_bench):
                        target = gs.opp_bench[target_idx]

                    if target:
                        # Penalize HP (we want low HP)
                        action["score"] -= target.hp * 10

                        # Penalize Energy (we want no energy)
                        action["score"] -= target.energy_count * 5000

                        # Penalize Ready (we want unready)
                        if not target.needs_energy():
                            action["score"] -= 20000

                        # Bonus for Retreat Cost (trap them)
                        action["score"] += target.retreat_cost * 1000

                        # Bonus if we can KO them easily
                        if target.hp <= 50:
                            action["score"] += 10000

                        # Avoid bringing out their carry unless we can kill it
                        if target.name.lower() in CARRY_LIST and target.hp > 100:
                             action["score"] -= 5000

                else:
                    # Activating for SELF
                    target = gs.get_bench_card(target_idx)
                    if target:
                        action["score"] += target.hp
                        if not target.needs_energy():
                             action["score"] += 5000
                        if "ex" in target.name.lower():
                            action["score"] += 1000
                        if target.hp < 60:
                             action["score"] -= 500

        elif "UseItem" in aname:
             action["type"] = "item"
             action["score"] = ITEM_SCORE
             if "ball" in aname_lower or "search" in aname_lower:
                 action["score"] = ITEM_SCORE # Boosted later
             elif "potion" in aname_lower or "heal" in aname_lower or "ice pop" in aname_lower:
                 action["type"] = "potion"
                 action["score"] = ITEM_SCORE
             elif "red card" in aname_lower:
                 action["type"] = "red_card"
                 action["score"] = RED_CARD_SCORE

        elif "UseAbility" in aname:
            action["type"] = "ability"
            action["score"] = ABILITY_SCORE
            m = re.search(r"UseAbility\((\d+)\)", aname)
            if m:
                idx = int(m.group(1))
                target = None
                if idx == 0:
                    target = gs.my_active
                else:
                    target = gs.get_bench_card(idx - 1)

                if target:
                    n_lower = target.name.lower()
                    if "gardevoir" in n_lower:
                        if gs.my_active and "Psychic" in gs.my_active.energy_type:
                            action["score"] += 4000
                            if gs.my_active.needs_energy():
                                action["score"] += 2000

                    elif "kirlia" in n_lower or "cinccino" in n_lower or "liepard" in n_lower:
                        action["score"] += 3000

                    elif "greninja" in n_lower:
                        action["score"] += 1000
                        if gs.opp_bench:
                            min_hp = 1000
                            for b in gs.opp_bench:
                                if b.hp < min_hp and b.hp > 0:
                                    min_hp = b.hp
                            if min_hp <= 20:
                                 action["score"] = LETHAL_KO_SCORE

                    elif "pidgeot" in n_lower:
                        action["score"] += 2000

        actions.append(action)

    if not gs.my_bench:
        for a in actions:
            if a["type"] == "place":
                a["score"] = DONK_PREVENTION_SCORE

    for a in actions:
        if a["type"] == "attach_energy":
            target = None
            if a["pos"] == 0: target = gs.my_active
            elif a["pos"] > 0:
                bench_idx = a["pos"] - 1
                target = gs.get_bench_card(bench_idx)

            if not target:
                a["score"] -= 10000
                continue

            if target.needs_energy():
                is_compatible = False
                if target.energy_type == "Colorless": is_compatible = True
                elif a["energy_type"] == target.energy_type: is_compatible = True

                if not is_compatible and target.db_entry:
                    for atk in target.attacks:
                        if a["energy_type"] in atk.get("cost", []):
                            is_compatible = True
                            break

                if is_compatible:
                    a["score"] += 2000
                    if "ex" in target.name.lower():
                        a["score"] += 1000
                    if target.name.lower() in CARRY_LIST:
                        a["score"] += CARRY_BONUS

                    if a["pos"] == 0:
                         a["score"] += 1000

                         retreat_cost = target.retreat_cost
                         if target.energy_count < retreat_cost:
                             active_weak = target.hp < 60
                             active_threatened = False
                             if gs.opp_active:
                                 opp_dmg = 0
                                 if gs.opp_active.db_entry:
                                     for idx in range(len(gs.opp_active.attacks)):
                                         d = calculate_damage(gs.opp_active, idx, gs)
                                         if d > opp_dmg: opp_dmg = d
                                 else:
                                     if "ex" in gs.opp_active.name.lower(): opp_dmg = 60
                                     else: opp_dmg = 30

                                 if opp_dmg >= target.hp:
                                     active_threatened = True

                             bench_strong = False
                             for b in gs.my_bench:
                                 if not b.needs_energy():
                                     dmg = 0
                                     if b.db_entry:
                                         dmg = calculate_damage(b, 0, gs)
                                     elif "ex" in b.name.lower():
                                         dmg = 90
                                     else:
                                         dmg = 40

                                     active_dmg = 0
                                     if target.db_entry:
                                          active_dmg = calculate_damage(target, 0, gs)

                                     if dmg > active_dmg + 20:
                                         bench_strong = True
                                         break

                             if (active_weak or active_threatened) and bench_strong:
                                  a["score"] += ACTIVE_WEAK_ATTACH_BONUS

                         if target and target.db_entry:
                             current_max_dmg = 0
                             potential_max_dmg = 0
                             new_energy = target.energy + [a["energy_type"]]

                             for i, atk in enumerate(target.attacks):
                                 if can_use_attack(atk.get("cost", []), target.energy):
                                     d = calculate_damage(target, i, gs, extra_damage)
                                     if d > current_max_dmg: current_max_dmg = d

                                 if can_use_attack(atk.get("cost", []), new_energy):
                                     d = calculate_damage(target, i, gs, extra_damage)
                                     if d > potential_max_dmg: potential_max_dmg = d

                             diff = potential_max_dmg - current_max_dmg
                             if diff >= 40:
                                 a["score"] += 5000
                             elif diff > 0:
                                 a["score"] += 2000

                             if gs.opp_active:
                                 if potential_max_dmg >= gs.opp_active.hp and current_max_dmg < gs.opp_active.hp:
                                     a["score"] += 10000
                else:
                     a["score"] -= 1000
            else:
                a["score"] -= 5000

    for a in actions:
        if a["type"] == "place":
            n_lower = a.get("card_name", "").lower()

            # Penalize placing weak Pokemon if bench is getting full (unless needed)
            if len(gs.my_bench) >= 2:
                if n_lower not in CARRY_LIST and "ex" not in n_lower:
                    a["score"] -= 1000

            if "ex" in n_lower or n_lower in CARRY_LIST:
                a["score"] += CARRY_BONUS

            if has_misty:
                 is_water = False
                 key = n_lower
                 if key in CARD_DB:
                     if "Water" in CARD_DB[key].get("energy_type", "Colorless"): is_water = True
                 elif any(x in n_lower for x in ["starmie", "greninja", "lapras", "blastoise", "articuno", "squirtle", "psyduck"]):
                     is_water = True

                 if is_water:
                     a["score"] = MISTY_PREP_SCORE

    for a in actions:
        if a["type"] == "research":
            if len(gs.my_hand) >= 5:
                has_energy = any("Energy" in c.name for c in gs.my_hand)
                has_basic = any(c.name != "Unknown" for c in gs.my_hand if "ex" in c.name.lower() or "Basic" in str(c.db_entry))
                if has_energy and has_basic:
                    a["score"] -= 5000
                else:
                    a["score"] += 1000
            elif len(gs.my_hand) < 5:
                a["score"] += 5000 # Boost if hand low
        elif a["type"] == "copycat":
            if gs.opp_hand_count > len(gs.my_hand):
                 a["score"] += 1000
            elif gs.opp_hand_count <= len(gs.my_hand):
                 a["score"] -= 5000
        elif a["type"] == "misty":
            a["score"] = MISTY_SCORE
            needs_water = False
            targets = []
            if gs.my_active and "Water" in gs.my_active.energy_type and gs.my_active.needs_energy(): targets.append(gs.my_active)
            for b in gs.my_bench:
                if "Water" in b.energy_type and b.needs_energy(): targets.append(b)
            if targets:
                 a["score"] += 2000
            else:
                 a["score"] -= 5000
        elif a["type"] == "red_card":
            if gs.opp_hand_count >= 4:
                a["score"] += 2000
            else:
                a["score"] -= 2000
        elif a["type"] == "potion":
            damaged_mons = 0
            active_critical = False
            if gs.my_active and gs.my_active.hp < gs.my_active.max_hp:
                damaged_mons += 1
                if gs.my_active.hp <= 60:
                    active_critical = True

            for b in gs.my_bench:
                 if b.hp < b.max_hp: damaged_mons += 1

            if active_critical:
                a["score"] = POTION_CRITICAL_SCORE
            elif damaged_mons > 0:
                a["score"] += 2000
            else:
                a["score"] -= 5000
        elif a["type"] == "gust":
            if can_win_on_bench:
                a["score"] = LETHAL_WIN_SCORE
            elif has_lethal_on_board:
                a["score"] -= 50000
            elif can_ko_on_bench:
                a["score"] = GUST_LETHAL_SCORE
            elif gs.opp_active and gs.opp_active.hp > 80:
                a["score"] += 2000
            else:
                a["score"] -= 5000
        elif a["type"] == "giovanni":
            needed = False
            for atk in actions:
                if atk["type"] == "attack" and atk.get("can_be_lethal_with_giovanni"):
                    needed = True
                    break

            if needed:
                a["score"] = LETHAL_KO_SCORE + 500
            else:
                is_attacking = any(x["type"] == "attack" for x in actions)
                if is_attacking: a["score"] += 500
                else: a["score"] -= 1000

    active_hp = gs.my_active.hp if gs.my_active else 0
    active_dmg = 0
    if gs.my_active:
         for i in range(len(gs.my_active.attacks)):
             d = calculate_damage(gs.my_active, i, gs)
             if d > active_dmg: active_dmg = d

    for a in actions:
        if a["type"] == "retreat":
            should_retreat = False

            if has_lethal_on_board:
                is_game_win = False
                for action in actions:
                     if action.get("is_lethal"):
                         is_game_win = True
                         break

                if is_game_win:
                    a["score"] = -100000
                    continue

            target = gs.get_bench_card(a.get("target_idx", -1))
            if not target or target.name == "Unknown":
                a["score"] = -100000
                continue

            if active_hp <= 40 and active_hp > 0:
                 should_retreat = True
                 a["score"] += 1000

            if not target.needs_energy():
                 target_dmg = 0
                 for i in range(len(target.attacks)):
                     d = calculate_damage(target, i, gs)
                     if d > target_dmg: target_dmg = d

                 if target_dmg > active_dmg + 10 and active_hp < 60:
                     should_retreat = True
                     a["score"] = STRATEGIC_SWITCH_SCORE + 500
                 elif target_dmg > active_dmg + 20:
                     a["score"] += 500

            if gs.my_active:
                a["score"] -= (gs.my_active.retreat_cost * 1000)

            if should_retreat:
                if not target.needs_energy():
                     if a["score"] < STRATEGIC_SWITCH_SCORE:
                         a["score"] = STRATEGIC_SWITCH_SCORE
                else:
                    if a["score"] < RETREAT_SCORE + 1000:
                         a["score"] = RETREAT_SCORE + 1000

    for a in actions:
        if a["type"] == "x_speed":
            best_retreat = -100000
            for r in actions:
                if r["type"] == "retreat" and r["score"] > best_retreat:
                    best_retreat = r["score"]

            if best_retreat > 0:
                 a["score"] = best_retreat + 100
                 a["score"] += 2000

    mewtwo_attacks = [a for a in actions if a["type"] == "attack" and gs.my_active and "mewtwo ex" in gs.my_active.name.lower()]
    if len(mewtwo_attacks) > 1:
        lethal_attacks = [a for a in mewtwo_attacks if a.get("is_ko")]
        if len(lethal_attacks) > 1:
             standard_lethal = None
             psydrive_lethal = None

             for atk in lethal_attacks:
                 if atk["damage"] == 50: standard_lethal = atk
                 elif atk["damage"] == 150: psydrive_lethal = atk

             if standard_lethal and psydrive_lethal:
                 for a in mewtwo_attacks:
                     if a["id"] == psydrive_lethal["id"]:
                         a["score"] -= 2000
                     elif a["id"] == standard_lethal["id"]:
                         a["score"] += 500

    if actions:
        actions.sort(key=lambda x: x["score"], reverse=True)
        best_action = actions[0]

        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"Turn: Hand={len(gs.my_hand)}, Bench={len(gs.my_bench)}")
            for a in actions[:5]:
                 logger.debug(f"Action: {a['name']} Type: {a['type']} Score: {a['score']} Dmg: {a.get('damage', 0)}")

        return best_action["id"]

    return legal_actions[0]
