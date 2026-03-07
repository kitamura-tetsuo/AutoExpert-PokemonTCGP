from candidate_player import *

class DummyObj:
    def __init__(self, name):
        self.name = name

state = GameStateWrapper.__new__(GameStateWrapper)
state.my_active = Card("Venusaur ex", DummyObj("Venusaur ex"))
state.opp_active = Card("Oricorio", DummyObj("Oricorio"))
state.opp_active.db_entry = CARD_DB_FULL["oricorio"][1]

print("Energy type:", state.opp_active.energy_type)
