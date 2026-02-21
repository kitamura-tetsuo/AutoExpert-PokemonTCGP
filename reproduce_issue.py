
import re
from candidate_player import play

class MockGame:
    def __init__(self, actions):
        self.actions = actions
    def legal_actions(self):
        return list(range(len(self.actions)))
    def action_name(self, aid):
        return self.actions[aid]

class MockCard:
    def __init__(self, name, energy):
        self.name = name
        self.attached_energy = energy
        self.remaining_hp = 60
        self.total_hp = 60

class MockState:
    def __init__(self):
        self.current_player = 0
        self.points = (0, 0)
    def get_active_pokemon(self, p):
        return MockCard("Charmander", [])
    def get_bench_pokemon(self, p):
        return [None, None, None]
    def get_hand(self, p):
        return []

def test_energy_match():
    # Setup state where we have Charmander (Fire) and Fire Energy in hand
    state = MockState()

    # Action: Attach Fire Energy to Active (0)
    # Action: End Turn
    actions = ["Attach(Fire Energy, 0)", "EndTurn"]
    game = MockGame(actions)

    selected_action_id = play(state, game)
    selected_name = game.action_name(selected_action_id)

    print(f"Selected Action: {selected_name}")

    # We expect it to select Attach because Charmander needs energy
    if "Attach" in selected_name:
        print("SUCCESS: Selected Attach")
    else:
        print("FAILURE: Did not select Attach (likely due to type mismatch logic)")

if __name__ == "__main__":
    test_energy_match()
