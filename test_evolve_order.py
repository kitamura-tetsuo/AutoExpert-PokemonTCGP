import re

with open("candidate_player.py", "r") as f:
    content = f.read()

# Let's ensure Evolve prioritizes correctly when threatened
pattern = r"""                if threat_lethal:
                    action\["score"\] \+= 2000"""

replacement = r"""                if threat_lethal:
                    action["score"] += 2000
                    # If this evolution gets us OUT of lethal range, boost it more
                    if evol_hp > opp_max_dmg and (gs.my_active and gs.my_active.hp <= opp_max_dmg):
                        action["score"] += 15000"""

content = re.sub(pattern, replacement, content)

with open("candidate_player.py", "w") as f:
    f.write(content)
