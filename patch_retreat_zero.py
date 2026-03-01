import re

with open("candidate_player.py", "r") as f:
    content = f.read()

pattern = r"""                    # If active is lethal, don't switch unless bench is somehow better \(e\.g\. EX vs non-EX\?\)
                    # Generally, if we can KO, we take it.
                    if not active_is_lethal:
                        if target_dmg > active_dmg \+ 30:
                             should_retreat = True
                             new_score = ATTACK_BASE_SCORE \+ \(target_dmg \* 100\) \+ 5000
                             action\["score"\] = max\(action\["score"\], new_score\)
                        elif target_dmg > active_dmg and gs.my_active and target.hp > \(gs.my_active.hp \+ 40\):
                             # Switch to tank if damage is comparable"""

replacement = r"""                    # If active is lethal, don't switch unless bench is somehow better (e.g. EX vs non-EX?)
                    # Generally, if we can KO, we take it.
                    if not active_is_lethal:
                        # STRATEGIC SWITCH RULES:
                        # 1. Active is useless (0 dmg) and bench can attack
                        # 2. Bench does significantly more damage (+30)
                        if (active_dmg == 0 and target_dmg > 0) or (target_dmg > active_dmg + 30):
                             should_retreat = True
                             new_score = ATTACK_BASE_SCORE + (target_dmg * 100) + 5000
                             action["score"] = max(action["score"], new_score)
                        elif target_dmg > active_dmg and gs.my_active and target.hp > (gs.my_active.hp + 40):
                             # Switch to tank if damage is comparable"""

content = re.sub(pattern, replacement, content)

with open("candidate_player.py", "w") as f:
    f.write(content)
