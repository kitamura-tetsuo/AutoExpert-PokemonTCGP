from candidate_player import *

class DummyObj:
    def __init__(self, name, energy, energy_type, status):
        self.name = name
        self.attached_energy = energy
        self.remaining_hp = 100
        self.total_hp = 100
        self.ability_used = False
        self.attached_tool = None
        self.status = status
        self.energy_type = energy_type

def run():
    state = GameStateWrapper.__new__(GameStateWrapper)
    state.my_active = Card("Venusaur ex", DummyObj("Venusaur ex", ["Grass", "Grass", "Grass", "Grass", "Grass"], "Grass", []))
    state.opp_active = Card("Oricorio", DummyObj("Oricorio", ["Lightning"], "Lightning", []))
    state.opp_active.db_entry = CARD_DB_FULL["oricorio"][1]

    state.my_bench = []
    state.opp_bench = []

    print("Energy count:", state.my_active.energy_count)
    print("Opponent active energy type:", state.opp_active.energy_type)

    for i, atk in enumerate(state.my_active.attacks):
        if can_use_attack(atk.get("cost", []), state.my_active.energy):
            dmg = calculate_damage(state.my_active, i, state)
            print(f"Attack {i} damage: {dmg} cost: {atk.get('cost')} base_dmg: {atk.get('dmg')}")
        else:
            print(f"Cannot use attack {i} cost: {atk.get('cost')} energy: {state.my_active.energy}")

run()
