import re

with open("candidate_player.py", "r") as f:
    content = f.read()

# Fix 1: Stall Breaker - if deck is empty, stop retreating to save Pokemon! Fight to the death to break stalls!
pattern = r"""                    if \(is_valuable and bench_is_safer\):
                        action\["score"\] = DONK_SURVIVAL_SCORE \+ 1000"""

replacement = r"""                    if (is_valuable and bench_is_safer):
                        # Stall breaker: If deck is empty, don't run away. We need to take prizes NOW.
                        if gs.my_deck_count > 0:
                            action["score"] = DONK_SURVIVAL_SCORE + 1000
                        else:
                            action["score"] -= 50000"""

content = re.sub(pattern, replacement, content)

# Fix 2: If we have an attack that does ANY damage, and our deck is empty, boost it above passing or retreating!
pattern2 = r"""                if gs.opp_active:
                    dmg_with_giovanni = action\["damage"\] \+ 10"""

replacement2 = r"""                if gs.opp_active:
                    dmg_with_giovanni = action["damage"] + 10

                    # Stall breaker: If we are out of cards, any attack is better than passing/retreating
                    if gs.my_deck_count == 0 and action["damage"] > 0:
                        action["score"] += 300000
"""
content = re.sub(pattern2, replacement2, content)

with open("candidate_player.py", "w") as f:
    f.write(content)
