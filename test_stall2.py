from candidate_player import *
class DummyObj:
    def __init__(self, name):
        self.name = name

state = GameStateWrapper.__new__(GameStateWrapper)
state.my_active = Card("Venusaur ex", DummyObj("Venusaur ex"))
state.opp_active = Card("Oricorio", DummyObj("Oricorio"))
state.opp_active.db_entry = CARD_DB_FULL["oricorio"][1]

action = {"damage": 0, "score": 10000}
atk_text = state.my_active.attacks[1].get("text", "")
if atk_text is None: atk_text = ""
atk_text = atk_text.lower()
base_dmg = float(state.my_active.attacks[1].get("dmg", 0))
state.my_active.hp = 190
state.my_active.max_hp = 190

is_setup_attack = False
if not is_setup_attack:
    if not atk_text and base_dmg == 0:
        action["score"] = -500000
    elif "heal" in atk_text:
        if state.my_active.hp < state.my_active.max_hp:
            action["score"] += 2000
        elif base_dmg > 0 and action["damage"] == 0:
            action["score"] = -200000
    elif base_dmg > 0 and action["damage"] == 0:
        # It's an attack that SHOULD do damage, but currently does 0 (e.g., due to safeguard)
        action["score"] = -200000
    elif base_dmg == 0 and action["damage"] == 0 and not atk_text:
        action["score"] = -200000

print("Final score:", action["score"])
