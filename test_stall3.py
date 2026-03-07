actions = [
    {"type": "attach_energy", "score": -200000, "name": "AttachEnergy(0, Grass)"},
    {"type": "attack", "score": -200000, "name": "Attack(0)"},
    {"type": "end_turn", "score": -10000, "name": "EndTurn"}
]
actions.sort(key=lambda x: x["score"], reverse=True)
print(actions[0])
