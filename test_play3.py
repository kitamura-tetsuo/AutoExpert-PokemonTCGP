import sys
import json
from candidate_player import play, GameStateWrapper, calculate_damage, Card, can_use_attack

class MockActive:
    def __init__(self, name, hp, energy, max_hp):
        self.name = name
        self.remaining_hp = hp
        self.total_hp = max_hp
        self.attached_energy = energy
        self.ability_used = False
        self.attached_tool = None
        self.status = []

class MockState:
    def __init__(self):
        self.current_player = 0
        self.points = [2, 0]
        self.active = [MockActive("Venusaur ex", 30, ["Grass"]*6, 190), MockActive("Arbok", 100, ["Darkness"]*2, 100)]
        self.bench = [[], []]
        self.hand = [[], []]
    def get_active_pokemon(self, p): return self.active[p]
    def get_bench_pokemon(self, p): return self.bench[p]
    def get_hand(self, p): return self.hand[p]

class MockGame:
    def __init__(self):
        pass
    def legal_actions(self):
        return [0, 1, 2]
    def action_name(self, aid):
        if aid == 0: return "EndTurn"
        if aid == 1: return "Attack(0)"
        if aid == 2: return "Attack(1)"
        return "Unknown"
    def encode_observation(self, p):
        return [-1.0] * 300

state = MockState()
game = MockGame()

gs = GameStateWrapper(state)

print(gs.my_active.attacks)
print(f"Attack 0 cost: {gs.my_active.attacks[0].get('cost')} can use: {can_use_attack(gs.my_active.attacks[0].get('cost', []), gs.my_active.energy)}")
print(f"Attack 1 cost: {gs.my_active.attacks[1].get('cost')} can use: {can_use_attack(gs.my_active.attacks[1].get('cost', []), gs.my_active.energy)}")
