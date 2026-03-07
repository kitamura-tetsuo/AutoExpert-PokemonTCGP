from candidate_player import *

action = {"type": "attach_energy", "pos": 0, "energy_type": "Grass", "score": 75000}

# Let's say action is an attach action in `actions`
actions = [action, {"type": "end_turn", "score": -10000}, {"type": "attack", "score": -200000}]

for a in actions:
    if a["type"] == "attach_energy":
        target = Card("Venusaur ex", None)
        target.energy = ["Grass"] * 5
        target.energy_count = 5
        target.db_entry = CARD_DB_FULL["venusaur ex"][0]
        target.name = "Venusaur ex"

        if target.energy_count >= 5:
            a["score"] = -200000
            continue

        print("This shouldn't print")

actions.sort(key=lambda x: x["score"], reverse=True)
print(actions[0])
