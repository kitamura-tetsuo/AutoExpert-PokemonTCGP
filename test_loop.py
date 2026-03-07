from candidate_player import *

class DummyObj:
    def __init__(self, name, energy):
        self.name = name
        self.attached_energy = energy
        self.remaining_hp = 100
        self.total_hp = 100
        self.ability_used = False
        self.attached_tool = None
        self.status = []
        self.energy_type = "Grass"

state = GameStateWrapper.__new__(GameStateWrapper)
state.my_active = Card("Venusaur ex", DummyObj("Venusaur ex", ["Grass"] * 5))
state.opp_active = Card("Oricorio", DummyObj("Oricorio", ["Lightning"]))

target = state.my_active

is_fully_powered = True
for atk in target.attacks:
    if not can_use_attack(atk.get("cost", []), target.energy):
        is_fully_powered = False
        break
print(f"is_fully_powered: {is_fully_powered}")

allows_retreat = target.energy_count < target.retreat_cost and (target.energy_count + 1) >= target.retreat_cost
print(f"allows_retreat: {allows_retreat}")

needs_energy = target.needs_energy()
print(f"needs_energy (native): {needs_energy}")
