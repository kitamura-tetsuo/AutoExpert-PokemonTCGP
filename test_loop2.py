from candidate_player import *

action = {"type": "attach_energy", "pos": 0, "energy_type": "Grass", "score": 75000}

# Code snippet from candidate_player
target = Card("Venusaur ex", None)
target.energy = ["Grass"] * 5
target.energy_count = 5
target.db_entry = CARD_DB_FULL["venusaur ex"][0]
target.name = "Venusaur ex"

if target.energy_count >= 5:
    action["score"] = -200000

print(action["score"])

# wait, if target.energy_count is 35 as seen in the logs
target.energy_count = 35
action["score"] = 75000
if target.energy_count >= 5:
    action["score"] = -200000

print(action["score"])
