import re

with open("candidate_player.py", "r") as f:
    content = f.read()

# Modify candidate_player.py to increase boost to 30000 and tighten the energy penalty logic
content = content.replace('a["score"] += 15000 # Boost attaching to late-game bench targets', 'a["score"] += 35000 # Boost attaching to late-game bench targets')
content = content.replace('if "exeggutor ex" in target.name.lower() and target.energy_count >= 1:', 'if "exeggutor ex" in target.name.lower() and target.energy_count >= 1 and gs.my_active and "exeggutor ex" in gs.my_active.name.lower():')

with open("candidate_player.py", "w") as f:
    f.write(content)

print("candidate_player.py modified successfully.")
