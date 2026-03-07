from candidate_player import CARD_DB_FULL

for idx, e in enumerate(CARD_DB_FULL["oricorio"]):
    print(f"Oricorio variant {idx}: HP {e.get('hp')} Type: {e.get('energy_type')} Ability: {e.get('ability')}")
