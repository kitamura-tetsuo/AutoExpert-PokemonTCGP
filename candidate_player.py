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

# --- Constants (Baseline Priorities) ---
LETHAL_WIN_SCORE = 1000000
LETHAL_KO_SCORE = 30000
DONK_PREVENTION_SCORE = 30000
EVOLVE_SCORE = 26000
MISTY_PREP_SCORE = 24200 # Kept this
MISTY_SCORE = 24600      # Baseline
STRATEGIC_SWITCH_SCORE = 24500 # Baseline
SEARCH_ITEM_SCORE = 23000 # Baseline
RESEARCH_SCORE = 22500    # Baseline
ATTACH_ENERGY_SCORE = 21500 # Baseline
PLACE_BASIC_SCORE = 21000 # Baseline
ABILITY_SCORE = 19500
RED_CARD_SCORE = 19500
ITEM_SCORE = 19000
ATTACK_BASE_SCORE = 1000
RETREAT_SCORE = -5000
END_TURN_SCORE = -10000

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

        m = re.match(r"^[A-Z0-9]+([A-Z].*)", raw_name)
        if m:
            name_part = m.group(1)
        else:
            name_part = raw_name

        cleaned = re.sub(r"([a-z])([A-Z])", r"\1 \2", name_part)
        key = cleaned.lower()
        if key in CARD_DB:
            return CARD_DB[key].get("name", cleaned)

        if cleaned.endswith(" Ex"):
            cleaned = cleaned[:-3] + " ex"
        return cleaned

    def _get_db_entry(self):
        key = self.name.lower()
        if key in CARD_DB: return CARD_DB[key]
        for k in CARD_DB:
            if k in key: return CARD_DB[k]
        return None

    @property
    def energy_type(self):
        if self.db_entry:
            return self.db_entry.get("energy_type", "Colorless")
        n = self.name.lower()
        if "pikachu" in n or "zapdos" in n: return "Lightning"
        if "mewtwo" in n or "gardevoir" in n: return "Psychic"
        if "charizard" in n or "moltres" in n: return "Fire"
        if "blastoise" in n or "starmie" in n or "greninja" in n: return "Water"
        if "venusaur" in n: return "Grass"
        if "machamp" in n: return "Fighting"
        return "Colorless"

    @property
    def attacks(self):
        if self.db_entry:
            return self.db_entry.get("attacks", [])
        return []

    def needs_energy(self):
        max_cost = 0
        for atk in self.attacks:
            cost = len(atk.get("cost", []))
            if cost > max_cost: max_cost = cost

        if max_cost == 0:
            if "pikachu ex" in self.name.lower(): max_cost = 2
            elif "mewtwo ex" in self.name.lower(): max_cost = 4
            elif "charizard ex" in self.name.lower(): max_cost = 4
            elif "starmie ex" in self.name.lower(): max_cost = 2
            elif "greninja" in self.name.lower(): max_cost = 2
            elif "venusaur" in self.name.lower(): max_cost = 4
            else: max_cost = 3

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

def calculate_damage(attacker: Card, attack_idx: int, state: GameStateWrapper, extra_damage=0):
    if not attacker: return 0
    attacks = attacker.attacks
    if attack_idx >= len(attacks): return 0

    atk = attacks[attack_idx]
    damage = atk.get("dmg", 0)
    text = (atk.get("text") or "").lower()

    if "flip" in text and "coin" in text:
        num_coins = atk.get("coin_flips", 0)
        if num_coins == 0:
            m = re.search(r"flip (\d+) coin", text)
            if m: num_coins = int(m.group(1))
            else: num_coins = 1

        dmg_per_head = 0
        m_dmg = re.search(r"(\d+) damage for each heads", text)
        if m_dmg:
            dmg_per_head = int(m_dmg.group(1))
            damage += (num_coins * 0.5 * dmg_per_head)
        else:
            m_more = re.search(r"heads, this attack does (\d+) more damage", text)
            if m_more:
                 damage += (num_coins * 0.5 * int(m_more.group(1)))

    if "damage for each" in text:
        multiplier = 0
        m = re.search(r"(\d+) damage for each", text)
        if m: multiplier = int(m.group(1))
        else: multiplier = 20

        if "benched" in text:
            if "opponent" in text:
                damage += (multiplier * len(state.opp_bench))
            else:
                damage += (multiplier * len(state.my_bench))
        elif "energy" in text:
            if "opponent" in text:
                if state.opp_active: damage += (multiplier * state.opp_active.energy_count)
            else:
                damage += (multiplier * attacker.energy_count)

    if "pikachu ex" in attacker.name.lower() and attack_idx == 0:
         count = 0
         for b in state.my_bench:
             if "lightning" in b.energy_type.lower(): count += 1
         damage = 30 * count

    if "mewtwo ex" in attacker.name.lower():
        if attack_idx == 1: damage = 150

    if "starmie ex" in attacker.name.lower() and attack_idx == 0:
        damage = 90

    return int(damage) + extra_damage

def play(state, game):
    legal_actions = game.legal_actions()
    if not legal_actions:
        return 0

    try:
        gs = GameStateWrapper(state)
        actions = []

        has_giovanni = any("giovanni" in c.name.lower() for c in gs.my_hand)
        extra_damage = 10 if has_giovanni else 0
        has_misty = any("misty" in c.name.lower() for c in gs.my_hand)

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
                    action["damage"] = calculate_damage(gs.my_active, idx, gs)
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
                     if "Energy" in obj or any(t in obj for t in ["Lightning", "Water", "Fire", "Grass", "Fighting", "Psychic", "Darkness", "Metal"]):
                         action["type"] = "attach_energy"
                         action["pos"] = int(m.group(2))
                         action["energy_type"] = obj
                         action["score"] = ATTACH_ENERGY_SCORE

            elif "Place" in aname or "PlayPokemon" in aname:
                m = re.search(r"(?:Place|PlayPokemon)\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
                if m:
                    card_name_raw = m.group(1)
                    pos = int(m.group(2))
                    action["type"] = "place"
                    action["pos"] = pos
                    action["score"] = PLACE_BASIC_SCORE

                    if has_misty:
                        clean_name = Card._clean_name(card_name_raw)
                        key = clean_name.lower()
                        etype = "Colorless"
                        if key in CARD_DB: etype = CARD_DB[key].get("energy_type", "Colorless")
                        elif "starmie" in key or "greninja" in key or "lapras" in key or "blastoise" in key or "articuno" in key:
                            etype = "Water"

                        if "Water" in etype:
                            action["score"] = MISTY_PREP_SCORE

            elif "Evolve" in aname:
                action["type"] = "evolve"
                action["score"] = EVOLVE_SCORE

            elif "UseSupporter" in aname or "Play" in aname:
                if "research" in aname_lower or "professor" in aname_lower:
                    action["type"] = "research"
                    action["score"] = RESEARCH_SCORE
                elif "misty" in aname_lower:
                    action["type"] = "misty"
                    action["score"] = MISTY_SCORE
                elif "sabrina" in aname_lower or "boss" in aname_lower:
                    action["type"] = "gust"
                    action["score"] = ABILITY_SCORE
                elif "giovanni" in aname_lower:
                    action["type"] = "giovanni"
                    action["score"] = ITEM_SCORE
                elif "red card" in aname_lower:
                    action["type"] = "red_card"
                    action["score"] = RED_CARD_SCORE
                elif "ball" in aname_lower or "search" in aname_lower:
                    action["type"] = "search_item"
                    action["score"] = SEARCH_ITEM_SCORE
                elif "speed" in aname_lower:
                    action["type"] = "x_speed"
                    action["score"] = ITEM_SCORE
                elif "potion" in aname_lower or "heal" in aname_lower:
                    action["type"] = "potion"
                    action["score"] = ITEM_SCORE
                else:
                    action["type"] = "item"
                    action["score"] = ITEM_SCORE

            elif "Retreat" in aname:
                m = re.search(r"Retreat\((\d+)\)", aname)
                if m:
                    action["type"] = "retreat"
                    action["target_idx"] = int(m.group(1)) - 1
                    action["score"] = RETREAT_SCORE

            elif "Activate" in aname:
                action["type"] = "activate"
                action["score"] = LETHAL_WIN_SCORE

            elif "UseItem" in aname:
                 action["type"] = "item"
                 action["score"] = ITEM_SCORE
                 if "ball" in aname_lower or "search" in aname_lower:
                     action["score"] = SEARCH_ITEM_SCORE
                 elif "potion" in aname_lower or "heal" in aname_lower:
                     action["type"] = "potion"
                     action["score"] = ITEM_SCORE

            elif "UseAbility" in aname:
                action["type"] = "ability"
                action["score"] = ABILITY_SCORE

            actions.append(action)

        # --- Heuristics Application ---

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
                    if 0 <= bench_idx < len(gs.my_bench):
                         target = gs.my_bench[bench_idx]

                if target:
                    if target.needs_energy():
                        a["score"] += 2000
                        if target.energy_type in a["energy_type"] or a["energy_type"] in target.energy_type:
                            a["score"] += 1000
                        elif "Colorless" in target.energy_type:
                             a["score"] += 500
                    else:
                        a["score"] -= 5000
                else:
                    a["score"] -= 10000

        for a in actions:
            if a["type"] == "research":
                if len(gs.my_hand) >= 5:
                    a["score"] -= 5000
            elif a["type"] == "misty":
                needs_water = False
                if gs.my_active and "Water" in gs.my_active.energy_type and gs.my_active.needs_energy(): needs_water = True
                for b in gs.my_bench:
                    if "Water" in b.energy_type and b.needs_energy(): needs_water = True

                if needs_water: a["score"] += 1000
                else: a["score"] -= 2000
            elif a["type"] == "red_card":
                if gs.opp_hand_count >= 3:
                    a["score"] += 2000
                else:
                    a["score"] -= 2000
            elif a["type"] == "potion":
                if gs.my_active and gs.my_active.hp < gs.my_active.max_hp:
                    a["score"] += 2000
                else:
                    a["score"] -= 2000
            elif a["type"] == "gust":
                if gs.opp_active and gs.opp_active.hp > 80:
                    a["score"] += 2000
                else:
                    a["score"] -= 5000
            elif a["type"] == "giovanni":
                best_atk_dmg = 0
                for atk in actions:
                    if atk["type"] == "attack":
                        if atk["damage"] > best_atk_dmg: best_atk_dmg = atk["damage"]

                if gs.opp_active and best_atk_dmg < gs.opp_active.hp and (best_atk_dmg + 10) >= gs.opp_active.hp:
                    a["score"] = LETHAL_KO_SCORE + 500

        active_hp = gs.my_active.hp if gs.my_active else 0
        retreat_score_max = RETREAT_SCORE

        for a in actions:
            if a["type"] == "retreat":
                should_retreat = False
                target = gs.get_bench_card(a["target_idx"])
                if not target:
                    a["score"] = -100000
                    continue

                if active_hp <= 40 and active_hp > 0:
                     should_retreat = True

                if should_retreat:
                    if target.energy_count >= 1:
                        a["score"] = STRATEGIC_SWITCH_SCORE
                    else:
                        a["score"] = RETREAT_SCORE + 1000

                if a["score"] > retreat_score_max: retreat_score_max = a["score"]

        for a in actions:
            if a["type"] == "x_speed":
                if retreat_score_max > 0:
                     a["score"] = retreat_score_max + 100
                     a["score"] += 2000

        mewtwo_attacks = [a for a in actions if a["type"] == "attack" and gs.my_active and "mewtwo ex" in gs.my_active.name.lower()]
        if len(mewtwo_attacks) > 1:
            lethal_attacks = [a for a in mewtwo_attacks if a.get("is_ko")]
            if len(lethal_attacks) > 1:
                 lethal_attacks.sort(key=lambda x: x["damage"])
                 best_lethal = lethal_attacks[0]

                 for a in mewtwo_attacks:
                     if a["id"] == best_lethal["id"]:
                         a["score"] += 500
                     elif a.get("is_ko"):
                         a["score"] -= 500

        if actions:
            actions.sort(key=lambda x: x["score"], reverse=True)
            best_action = actions[0]

            logger.debug(f"Turn: Hand={len(gs.my_hand)}, Bench={len(gs.my_bench)}")
            for a in actions[:5]:
                 logger.debug(f"Action: {a['name']} Type: {a['type']} Score: {a['score']}")

            return best_action["id"]

        return legal_actions[0]

    except Exception as e:
        logger.error(f"Error in play: {e}", exc_info=True)
        return legal_actions[0]
