import re

with open("candidate_player.py", "r") as f:
    content = f.read()

pattern = r"""                    # Prioritize pokemon that already have energy, to finish powering them up!
                    # A pokemon with 2 energy should get its 3rd before a 0 energy gets its 1st.
                    a\["score"\] \+= \(target.energy_count \* 500\)"""

replacement = r"""                    # Prioritize pokemon that already have energy, to finish powering them up!
                    # A pokemon with 2 energy should get its 3rd before a 0 energy gets its 1st.
                    # HOWEVER, if it's already fully powered for its best attack, don't hog energy!
                    is_ready_to_attack = False
                    if target.attacks:
                        # Check if we can use the most expensive attack
                        best_atk = target.attacks[-1]
                        if can_use_attack(best_atk.get("cost", []), target.energy):
                            is_ready_to_attack = True

                    if not is_ready_to_attack:
                        a["score"] += (target.energy_count * 2000) # Increased priority to finish building
                    else:
                        a["score"] -= 5000 # Penalize attaching excess energy if it can already attack"""

content = re.sub(pattern, replacement, content)

with open("candidate_player.py", "w") as f:
    f.write(content)
