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
        self.points = [1, 0]
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

for aid in game.legal_actions():
    aname = game.action_name(aid)
    print(f"Action: {aname}")
    if "Attack" in aname:
        idx = int(aname.split("(")[1].split(")")[0])
        dmg = calculate_damage(gs.my_active, idx, gs, extra_damage=0)
        print(f"Damage for {aname} = {dmg}")
        is_lethal = dmg >= gs.opp_active.hp
        print(f"Is lethal = {is_lethal}")
        is_ex = "ex" in gs.opp_active.name.lower()
        points_gained = 2 if is_ex else 1
        points_needed_to_win = 3 - gs.my_points
        print(f"Points gained = {points_gained}, Points needed = {points_needed_to_win}")
