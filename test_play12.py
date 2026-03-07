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
        self.status = ["NoRetreat"]

class MockState:
    def __init__(self):
        self.current_player = 0
        self.points = [1, 0]
        self.active = [MockActive('Venusaur ex', 90, ['Grass'], 190), MockActive('Arbok', 40, ['Darkness']*2, 100)]
        self.bench = [[MockActive('Empty', 0, [], 0)], [MockActive('Ekans', 60, ['Darkness'], 60)]]
        self.hand = [[], []]
    def get_active_pokemon(self, p): return self.active[p]
    def get_bench_pokemon(self, p): return self.bench[p]
    def get_hand(self, p): return self.hand[p]

class MockGame:
    def __init__(self):
        pass
    def legal_actions(self):
        return [0, 1, 3] # No attack 1 since only 1 grass energy
    def action_name(self, aid):
        if aid == 0: return 'EndTurn'
        if aid == 1: return 'Attack(0)'
        if aid == 3: return 'AttachEnergy(0, Grass)' # Correct name
        return 'Unknown'
    def encode_observation(self, p):
        return [-1.0] * 300

state = MockState()
game = MockGame()

aid = play(state, game)
print(f'Selected action: {aid} - {game.action_name(aid)}')
