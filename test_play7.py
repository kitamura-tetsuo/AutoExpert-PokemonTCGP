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

# Let's see what the score of each action is in play
def play_with_scores(state, game):
    legal_actions = game.legal_actions()
    gs = GameStateWrapper(state)

    # Simplified part of play to see scores
    actions = []
    points_needed_to_win = 3 - gs.my_points
    opp_max_dmg = 60 # Arbok's damage
    threat_lethal = True

    for aid in legal_actions:
        aname = game.action_name(aid)
        action = {"id": aid, "name": aname, "score": 0, "type": "unknown"}

        if "Attack" in aname:
            idx = int(aname.split("(")[1].split(")")[0])
            action["type"] = "attack"
            action["idx"] = idx
            action["damage"] = calculate_damage(gs.my_active, idx, gs, extra_damage=0, mode="ev")

            effective_damage = min(action["damage"], gs.opp_active.hp + 10)
            action["score"] = 10000 + (effective_damage * 100)

            is_ko = False
            if action["damage"] >= gs.opp_active.hp:
                is_ko = True

            if is_ko:
                action["score"] = 50000
                action["is_ko"] = True

                is_ex = "ex" in gs.opp_active.name.lower()
                points_gained = 2 if is_ex else 1

                if points_gained >= points_needed_to_win or len(gs.opp_bench) == 0:
                    action["score"] = 1000000
                    action["is_lethal"] = True

            if threat_lethal and is_ko:
                action["score"] += 20000
                is_my_ex = gs.my_active and "ex" in gs.my_active.name.lower()
                is_opp_ex = "ex" in gs.opp_active.name.lower()
                points_gained = 2 if is_opp_ex else 1
                points_lost = 2 if is_my_ex else 1

                if points_gained >= points_lost:
                     action["score"] = 50000 + 500000 # LETHAL_KO_SCORE + AGGRESSIVE_DEFENSE_BONUS

            # Status Effect / Heal Bonus
            if not is_ko and gs.my_active and idx < len(gs.my_active.attacks):
                pass

        actions.append(action)

    return actions

actions = play_with_scores(state, game)
for a in actions:
    print(f"Action: {a['name']}, Score: {a['score']}")
