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
    try:
        from db_dump import CARD_DB_FULL
    except ImportError:
        CARD_DB_FULL = {}
except ImportError:
    logger.warning("Could not import CARD_DB from db_dump. Using empty DB.")
    CARD_DB = {}
    CARD_DB_FULL = {}

# --- Constants ---
LETHAL_WIN_SCORE = 1000000
DONK_PREVENTION_SCORE = 500000

GUST_LETHAL_SCORE = 80000
MISTY_SCORE = 78000
MISTY_PREP_SCORE = 77000
ATTACH_ENERGY_SCORE = 75000
SEARCH_SCORE = 74500
EVOLVE_SCORE = 74000
PLACE_BASIC_SCORE = 73000
ITEM_SCORE = 72000
GIOVANNI_SCORE = 60000
GIOVANNI_NEEDED_SCORE = 90000 # Boosted above Attach and Research
RED_CARD_SCORE = 71000
RESEARCH_SCORE = 70000
DONK_SEARCH_SCORE = 500000
DONK_AVOIDANCE_SCORE = 450000

ABILITY_SCORE = 50000
POTION_CRITICAL_SCORE = 85000

CARRY_BONUS = 2000
ACTIVE_WEAK_ATTACH_BONUS = 5000
LETHAL_KO_SCORE = 50000
STRATEGIC_SWITCH_SCORE = 30000
ATTACK_BASE_SCORE = 10000
RETREAT_SCORE = -15000 # Don't retreat unless necessary
END_TURN_SCORE = -10000

CARRY_LIST = [
    "mewtwo ex", "pikachu ex", "charizard ex", "starmie ex", "venusaur ex",
    "blastoise ex", "dragonite", "gardevoir", "darkrai", "marowak ex",
    "weezing", "arbok", "zapdos ex", "articuno ex", "moltres ex",
    "machamp ex", "gengar ex", "wigglytuff ex", "nidoqueen", "nidoking",
    "mega altaria ex", "greninja ex", "greninja", "mega kangaskhan ex"
]

EVOLUTION_COST_MAP = {
    "bulbasaur": 4, "ivysaur": 4,
    "charmander": 4, "charmeleon": 4,
    "squirtle": 3, "wartortle": 3,
    "caterpie": 3, "metapod": 3,
    "weedle": 1, "kakuna": 1,
    "pidgey": 2, "pidgeotto": 2,
    "rattata": 2,
    "spearow": 2,
    "ekans": 2,
    "pikachu": 3,
    "sandshrew": 2,
    "nidoran♀": 3, "nidorina": 3, "nidoran\u2640": 3,
    "nidoran♂": 3, "nidorino": 3, "nidoran\u2642": 3,
    "clefairy": 3,
    "vulpix": 2,
    "jigglypuff": 3,
    "zubat": 2,
    "oddish": 3, "gloom": 3,
    "paras": 2,
    "venonat": 2,
    "diglett": 1,
    "meowth": 2,
    "psyduck": 2,
    "mankey": 2,
    "growlithe": 3,
    "poliwag": 3, "poliwhirl": 3,
    "abra": 3, "kadabra": 3,
    "machop": 3, "machoke": 3,
    "bellsprout": 2, "weepinbell": 2,
    "tentacool": 2,
    "geodude": 4, "graveler": 4,
    "ponyta": 1,
    "slowpoke": 3,
    "magnemite": 4,
    "farfetch'd": 2,
    "doduo": 1,
    "seel": 3,
    "grimer": 3,
    "shellder": 3,
    "gastly": 3, "haunter": 3,
    "onix": 3,
    "drowzee": 3,
    "krabby": 3,
    "voltorb": 2,
    "exeggcute": 1,
    "cubone": 2,
    "koffing": 3,
    "rhyhorn": 4,
    "horsea": 3,
    "goldeen": 1,
    "staryu": 2,
    "magikarp": 4,
    "eevee": 3,
    "omanyte": 3,
    "kabuto": 1,
    "dratini": 4, "dragonair": 4,
    "ralts": 3, "kirlia": 3,
    "froakie": 2, "frogadier": 2,
    "pawniard": 2,
    "meltan": 4,
    "blitzle": 1,
    "mareep": 3,
    "skrelp": 3,
    "goomy": 3,
    "noibat": 2,
    "axew": 3,
    "deino": 3, "zweilous": 3,
    "larvesta": 3,
    "fletchling": 1,
    "litleo": 3,
    "skiddo": 2,
    "pancham": 3,
    "furfrou": 2,
    "espurr": 2,
    "honedge": 3,
    "spritzee": 2,
    "swirlix": 2,
    "inkay": 3,
    "binacle": 3,
    "clauncher": 2,
    "helioptile": 2,
    "tyrunt": 3,
    "amaura": 3,
    "phantump": 3,
    "pumpkaboo": 3,
    "bergmite": 3,
    "rowlet": 3,
    "litten": 3,
    "popplio": 3,
    "pikipek": 3,
    "yungoos": 1,
    "grubbin": 3,
    "crabrawler": 3,
    "mareanie": 2,
    "mudbray": 3,
    "dewpider": 3,
    "fomantis": 1,
    "morelull": 2,
    "salandit": 2,
    "stufful": 3,
    "bounsweet": 3,
    "oranguru": 2,
    "passimian": 2,
    "wimpod": 3,
    "sandygast": 3,
}

WEAKNESS_MAP = {
    "Grass": ["Fire"],
    "Fire": ["Water"],
    "Water": ["Lightning"],
    "Lightning": ["Fighting"],
    "Psychic": ["Darkness"],
    "Fighting": ["Psychic"],
    "Darkness": ["Fighting", "Grass", "Fire"],
    "Metal": ["Fire"],
    "Dragon": ["Fairy"],
    "Colorless": ["Fighting"]
}

class Card:
    def __init__(self, debug_label, obj=None):
        self.debug_label = debug_label
        self.obj = obj
        self.raw_name = str(getattr(obj, "name", "")) if obj else ""
        if not self.raw_name: self.raw_name = "Unknown"
        self.name = self._clean_name(self.raw_name)
        self.hp = getattr(obj, "remaining_hp", 0) if obj else 0
        self.max_hp = getattr(obj, "total_hp", 0) if obj else 0
        if self.max_hp == 0 and obj:
             self.max_hp = getattr(obj, "hp", 0)
        self.db_entry = self._get_db_entry()
        self.energy = [str(e) for e in getattr(obj, "attached_energy", [])] if obj else []
        self.energy_count = len(self.energy)

    @staticmethod
    def _clean_name(raw_name):
        if not raw_name or raw_name == "Unknown": return "Unknown"
        if raw_name.startswith("Some(") and raw_name.endswith(")"):
            raw_name = raw_name[5:-1]

        m = re.match(r"^([A-Z0-9]+)?([A-Z][a-z].*)", raw_name)
        if m and m.group(1):
             prefix = m.group(1)
             name_part = m.group(2)
             if len(prefix) <= 6:
                 raw_name = name_part

        cleaned = re.sub(r"([a-z])([A-Z])", r"\1 \2", raw_name)

        if cleaned.endswith(" Ex"):
            cleaned = cleaned[:-3] + " ex"

        key = cleaned.lower()
        if key in CARD_DB:
            entry = CARD_DB[key]
            if isinstance(entry, list):
                return entry[0].get("name", cleaned)
            return entry.get("name", cleaned)

        for k in CARD_DB:
            if k in key:
                 entry = CARD_DB[k]
                 if isinstance(entry, list):
                     return entry[0].get("name", k.title())
                 return entry.get("name", k.title())

        return cleaned

    def _get_db_entry(self):
        key = self.name.lower()
        entries = []
        if key in CARD_DB_FULL:
            entries = CARD_DB_FULL[key]
        elif key in CARD_DB:
             entries = [CARD_DB[key]]
        else:
            for k in CARD_DB_FULL:
                 if k == key:
                     entries = CARD_DB_FULL[k]
                     break

        if not entries:
            return None

        if isinstance(entries, list):
            # Try to match by max_hp
            if self.max_hp > 0:
                for e in entries:
                    if e.get("hp") == self.max_hp:
                        return e
            # Fallback to first entry
            return entries[0]
        return entries

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
        max_cost = 0
        n_lower = self.name.lower()

        # 1. Check Evolution Cost Map first (Override for evolutions)
        if n_lower in EVOLUTION_COST_MAP:
            max_cost = EVOLUTION_COST_MAP[n_lower]

        # 2. Check DB Entry
        elif self.db_entry:
            attacks = self.attacks
            if attacks:
                for atk in attacks:
                    cost = len(atk.get("cost", []))
                    if cost > max_cost: max_cost = cost

        # 3. Fallback logic
        if max_cost == 0:
            # Fallback if DB missing or no attacks (unlikely for cards we care about)
            max_cost = 3 # Increased default
            if "pikachu ex" in n_lower: max_cost = 3 # Ensure 3 for Raichu just in case
            elif "mewtwo ex" in n_lower: max_cost = 4 # Psydrive
            elif "charizard ex" in n_lower: max_cost = 4
            elif "starmie ex" in n_lower: max_cost = 2
            elif "greninja" in n_lower: max_cost = 3
            elif "venusaur" in n_lower: max_cost = 4
            elif "mega" in n_lower and "ex" in n_lower: max_cost = 4
            elif "ex" in n_lower: max_cost = 3

        # Hard cap check
        if self.energy_count >= max_cost and max_cost > 0:
            return False

        return self.energy_count < max_cost

class GameStateWrapper:
    def __init__(self, state, perspective_player=None):
        self.state = state
        self.me = state.current_player if perspective_player is None else perspective_player
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

    # 2. Fixed Damage in Text
    m_fixed = re.search(r"this attack does (\d+) damage", text)
    if m_fixed:
        damage = int(m_fixed.group(1))

    # 3. Scaling Damage
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
                if "pikachu ex" in name_lower and "lightning" in text:
                     # Pikachu ex counts lightning bench
                     count = 0
                     for b in state.my_bench:
                         if "Lightning" in b.energy_type: count += 1
        elif "energy" in text:
            if "opponent" in text:
                if state.opp_active: count = state.opp_active.energy_count
            else:
                count = attacker.energy_count

        calculated_bonus = count * multiplier
        if damage <= 10:
             damage = calculated_bonus
        else:
             damage += calculated_bonus

    # 4. Specific Card Overrides (Fallback)
    if "pikachu ex" in name_lower and attack_idx == 0 and damage < 30:
         count = 0
         for b in state.my_bench:
             if "Lightning" in b.energy_type: count += 1
         damage = 30 * count

    if "mewtwo ex" in name_lower and attack_idx == 1 and damage < 150:
        damage = 150

    if "starmie ex" in name_lower and attack_idx == 0 and damage < 90:
        damage = 90

    if "charizard ex" in name_lower and attack_idx == 1 and damage < 200:
        damage = 200

    if "marowak ex" in name_lower and attack_idx == 0:
         damage = 80 # EV is 80 (2 * 0.5 * 80)

    damage += extra_damage

    if state.opp_active and state.opp_active.db_entry:
        ability = state.opp_active.db_entry.get("ability")
        if ability:
            effect = ability.get("effect", "").lower()
            if "prevent all damage" in effect and "pokémon ex" in effect:
                if "ex" in attacker.name.lower():
                    damage = 0

    # 5. Weakness Logic
    if state.opp_active:
        opp_type = state.opp_active.energy_type
        attacker_type = attacker.energy_type

        # Check if opponent is weak to attacker
        if opp_type in WEAKNESS_MAP:
            weaknesses = WEAKNESS_MAP[opp_type]
            if attacker_type in weaknesses:
                damage *= 2

    return int(damage)

def get_opponent_max_damage(gs: GameStateWrapper):
    if not gs.opp_active:
        return 0

    # Create a view from opponent's perspective
    opp_gs = GameStateWrapper(gs.state, perspective_player=gs.opp)

    max_dmg = 0
    attacker = opp_gs.my_active

    if attacker:
        current_energy = attacker.energy

        attacks = attacker.attacks
        for i, atk in enumerate(attacks):
            cost = atk.get("cost", [])
            # Check if they can use it
            if can_use_attack(cost, current_energy):
                 dmg = calculate_damage(attacker, i, opp_gs, extra_damage=0)
                 if dmg > max_dmg: max_dmg = dmg
            else:
                pass

    return max_dmg

def play(state, game):
    legal_actions = game.legal_actions()
    if not legal_actions:
        return 0

    gs = GameStateWrapper(state)
    actions = []

    has_giovanni = any("giovanni" in c.name.lower() for c in gs.my_hand)
    # Don't apply extra damage here blindly, check per action

    # Check for lethal on board
    has_lethal_on_board = False
    if gs.my_active and gs.opp_active:
        for idx in range(len(gs.my_active.attacks)):
            # Check if we can USE the attack first!
            atk = gs.my_active.attacks[idx]
            if not can_use_attack(atk.get("cost", []), gs.my_active.energy):
                continue

            dmg = calculate_damage(gs.my_active, idx, gs, extra_damage=0)
            if dmg >= gs.opp_active.hp:
                has_lethal_on_board = True
                break
            # Check Giovanni
            if has_giovanni and (dmg + 10) >= gs.opp_active.hp:
                has_lethal_on_board = True # Potential lethal
                break

    can_win_on_bench = False
    can_ko_on_bench = False
    points_needed_to_win = 3 - gs.my_points

    if gs.my_active:
        for b in gs.opp_bench:
             for idx in range(len(gs.my_active.attacks)):
                 # Check usability
                 atk = gs.my_active.attacks[idx]
                 if not can_use_attack(atk.get("cost", []), gs.my_active.energy):
                     continue

                 dmg = calculate_damage(gs.my_active, idx, gs, extra_damage=10 if has_giovanni else 0)
                 if dmg >= b.hp:
                     can_ko_on_bench = True
                     is_ex = "ex" in b.name.lower()
                     points_gained = 2 if is_ex else 1
                     if points_gained >= points_needed_to_win:
                        can_win_on_bench = True
                     break
             if can_win_on_bench:
                 break

    # Opponent Lethal Check
    opp_max_dmg = get_opponent_max_damage(gs)
    threat_lethal = False
    if gs.my_active and opp_max_dmg >= gs.my_active.hp:
        threat_lethal = True

    active_hp = gs.my_active.hp if gs.my_active else 0
    active_dmg = 0
    if gs.my_active:
         for i in range(len(gs.my_active.attacks)):
             d = calculate_damage(gs.my_active, i, gs)
             if d > active_dmg: active_dmg = d

    for aid in legal_actions:
        aname = game.action_name(aid)
        action = {"id": aid, "name": aname, "score": 0, "type": "unknown"}
        aname_lower = aname.lower()

        if aname == "EndTurn":
            action["type"] = "end_turn"
            action["score"] = END_TURN_SCORE
            if len(gs.my_bench) == 0 and gs.my_active and gs.my_active.hp <= 60:
                 action["score"] -= 100000

        elif "Attack" in aname:
            m = re.search(r"Attack\((\d+)\)", aname)
            if m:
                idx = int(m.group(1))
                action["type"] = "attack"
                action["idx"] = idx
                action["damage"] = calculate_damage(gs.my_active, idx, gs, extra_damage=0)
                action["score"] = ATTACK_BASE_SCORE + action["damage"]

                if gs.opp_active:
                    dmg_with_giovanni = action["damage"] + 10

                    is_ko = False
                    if action["damage"] >= gs.opp_active.hp:
                        is_ko = True

                    can_be_lethal_with_giovanni = False
                    if not is_ko and has_giovanni and dmg_with_giovanni >= gs.opp_active.hp:
                        can_be_lethal_with_giovanni = True
                        action["can_be_lethal_with_giovanni"] = True

                    if is_ko:
                        action["score"] = LETHAL_KO_SCORE
                        action["is_ko"] = True

                        is_ex = "ex" in gs.opp_active.name.lower()
                        points_gained = 2 if is_ex else 1

                        if points_gained >= points_needed_to_win or len(gs.opp_bench) == 0:
                            action["score"] = LETHAL_WIN_SCORE
                            action["is_lethal"] = True

                    # If threatened, boost attack if it kills the threat
                    if threat_lethal and is_ko:
                        action["score"] += 20000

                # Donk Avoidance for Attack
                if len(gs.my_bench) == 0 and not action.get("is_lethal") and not action.get("is_ko"):
                     action["score"] = 5000

        elif "AttachEnergy" in aname:
            m = re.search(r"AttachEnergy\((\d+), (.*?)\)", aname)
            if m:
                action["type"] = "attach_energy"
                action["pos"] = int(m.group(1))
                action["energy_type"] = m.group(2)
                action["score"] = ATTACH_ENERGY_SCORE

        elif "AttachTool" in aname:
             m = re.search(r"AttachTool\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
             if m:
                 action["type"] = "attach_tool"
                 action["score"] = ITEM_SCORE
                 action["pos"] = int(m.group(2))

        elif "Attach" in aname:
             m = re.search(r"Attach\((?:Some\()?(.*?)\)?, (\d+)\)", aname)
             if m:
                 obj = m.group(1)
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

        elif "UseSupporter" in aname or "Play" in aname or "UseItem" in aname:
            risk_of_donk = (len(gs.my_bench) == 0)

            if "research" in aname_lower or "professor" in aname_lower:
                action["type"] = "research"
                action["score"] = RESEARCH_SCORE
                if risk_of_donk:
                    action["score"] = DONK_SEARCH_SCORE

            elif "copycat" in aname_lower:
                action["type"] = "copycat"
                action["score"] = RESEARCH_SCORE
            elif "misty" in aname_lower:
                action["type"] = "misty"
                action["score"] = MISTY_SCORE
            elif "sabrina" in aname_lower or "boss" in aname_lower or "catcher" in aname_lower:
                action["type"] = "gust"
                action["score"] = ITEM_SCORE
            elif "giovanni" in aname_lower:
                action["type"] = "giovanni"
                action["score"] = GIOVANNI_SCORE
            elif "red card" in aname_lower:
                action["type"] = "red_card"
                action["score"] = RED_CARD_SCORE
            elif "ball" in aname_lower or "search" in aname_lower:
                action["type"] = "search_item"
                action["score"] = SEARCH_SCORE
                if risk_of_donk:
                    action["score"] = DONK_SEARCH_SCORE
                if len(gs.my_bench) == 0:
                     action["score"] = DONK_SEARCH_SCORE

            elif "speed" in aname_lower:
                action["type"] = "x_speed"
                action["score"] = ITEM_SCORE
            elif "potion" in aname_lower or "heal" in aname_lower or "ice pop" in aname_lower or "icepop" in aname_lower:
                action["type"] = "potion"
                action["score"] = ITEM_SCORE
                if threat_lethal:
                    # Check if Potion saves us
                    if gs.my_active and (gs.my_active.hp + 20) > opp_max_dmg:
                        action["score"] += 30000

            elif "brock" in aname_lower:
                action["type"] = "energy_retrieval"
                action["score"] = ITEM_SCORE
            else:
                action["type"] = "item"
                action["score"] = ITEM_SCORE

        elif "Retreat" in aname:
            should_retreat = False
            m = re.search(r"Retreat\((\d+)\)", aname)
            if m:
                action["type"] = "retreat"
                bench_idx = int(m.group(1)) - 1
                action["target_idx"] = bench_idx
                action["score"] = RETREAT_SCORE

                target = gs.get_bench_card(bench_idx)
                if not target or target.name == "Unknown":
                    action["score"] = -100000
                    continue

                if has_lethal_on_board:
                    # If we have lethal, don't retreat unless we can't kill them?
                    # But has_lethal_on_board checks we can use the attack and it is lethal.
                    # So we should generally NOT retreat.
                    action["score"] = -100000
                    continue

                if threat_lethal:
                    # Only retreat if bench is ready OR we are saving a valuable card (EX or loaded)
                    # AND the bench card isn't going to die immediately either
                    is_valuable = False
                    if gs.my_active:
                        is_valuable = "ex" in gs.my_active.name.lower() or gs.my_active.energy_count >= 2

                    bench_is_safer = target and target.hp > opp_max_dmg
                    bench_can_attack = target and target.energy_count >= 1 # Soft check

                    # Increased boost to prioritize saving prizes
                    if (is_valuable and bench_is_safer):
                        action["score"] += 35000

                    if bench_can_attack:
                         action["score"] += 15000

            if active_hp <= 40 and active_hp > 0:
                 should_retreat = True
                 action["score"] += 1000

            if not target.needs_energy():
                 target_dmg = 0
                 for i in range(len(target.attacks)):
                     d = calculate_damage(target, i, gs)
                     if d > target_dmg: target_dmg = d

                 if target_dmg > active_dmg + 10 and active_hp < 60:
                     should_retreat = True
                     action["score"] = STRATEGIC_SWITCH_SCORE + 500
                 elif target_dmg > active_dmg + 20:
                     action["score"] += 500

            if gs.my_active:
                action["score"] -= (gs.my_active.retreat_cost * 1000)

            if should_retreat:
                if not target.needs_energy():
                     if action["score"] < STRATEGIC_SWITCH_SCORE:
                         action["score"] = STRATEGIC_SWITCH_SCORE
                else:
                    if action["score"] < RETREAT_SCORE + 1000:
                         action["score"] = RETREAT_SCORE + 1000

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
                 # Prefer standard lethal to save energy? Psydrive discards energy.
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
