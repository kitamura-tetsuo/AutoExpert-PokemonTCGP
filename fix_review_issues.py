import re

with open("candidate_player.py", "r") as f:
    code = f.read()

# 1. Remove hardcoded names ("arbok", "weezing") and instead rely on retreat cost checking and poison status.
# Wait, "energy_count" is actually a valid attribute of the `Card` wrapper class: `self.energy_count = len(self.energy)`.
# Let's fix the hardcoded names to rely on attacks having "retreat" in text, or just general evasion if poisoned.

# Let's replace the Arbok/Weezing evasion logic with something more general:
# If poisoned, we already handled HP <= 60 logic in wants_to_retreat. We can just keep that in retreat scoring.
# For Arbok, it has an attack with "retreat" in text.

search_block = '''                    # Evasion: If facing Arbok which locks retreat, and our active is weak/poisoned
                    if gs.opp_active and "arbok" in gs.opp_active.name.lower() and gs.opp_active.energy_count >= 1:
                        if target_dmg > active_dmg or (gs.my_active and gs.my_active.hp <= 70):
                            should_retreat = True
                            new_score = ATTACK_BASE_SCORE + (target_dmg * 100) + 10000
                            action["score"] = max(action["score"], new_score)

                    # Evasion: If facing Weezing with poison and active HP <= 60
                    if gs.opp_active and "weezing" in gs.opp_active.name.lower():
                        if gs.my_active and any("poison" in str(s).lower() for s in gs.my_active.status) and gs.my_active.hp <= 60:
                            should_retreat = True
                            new_score = ATTACK_BASE_SCORE + (target_dmg * 100) + 15000
                            action["score"] = max(action["score"], new_score)

                    active_is_lethal = False
                    if gs.opp_active and active_dmg >= gs.opp_active.hp:
                        active_is_lethal = True'''

replace_block = '''                    # Evasion: If opponent can lock retreat, and our active is weak or setup pokemon
                    if gs.opp_active:
                        can_lock = False
                        for atk in gs.opp_active.attacks:
                            if "can't retreat" in (atk.get("effect", "") or "").lower() or "can't retreat" in (atk.get("text", "") or "").lower():
                                # Check if they have energy to use it or are close
                                if gs.opp_active.energy_count >= len(atk.get("cost", [])) - 1:
                                    can_lock = True
                                    break
                        if can_lock and (target_dmg > active_dmg or (gs.my_active and gs.my_active.hp <= 70)):
                            should_retreat = True
                            new_score = ATTACK_BASE_SCORE + (target_dmg * 100) + 10000
                            action["score"] = max(action["score"], new_score)

                    # Evasion: If active is critically poisoned
                    if gs.my_active and any("poison" in str(s).lower() for s in gs.my_active.status) and gs.my_active.hp <= 60:
                        should_retreat = True
                        new_score = ATTACK_BASE_SCORE + (target_dmg * 100) + 15000
                        action["score"] = max(action["score"], new_score)'''

if search_block in code:
    code = code.replace(search_block, replace_block)
    print("Replaced Arbok/Weezing hardcodes with general game logic")
else:
    print("Block not found!")

with open("candidate_player.py", "w") as f:
    f.write(code)
