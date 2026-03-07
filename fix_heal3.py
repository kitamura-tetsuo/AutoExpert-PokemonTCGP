import re

with open("candidate_player.py", "r") as f:
    content = f.read()

# Make sure Potions/Heal strictly apply LETHAL bonuses only to ACTIVE Pokemon to prevent incorrect overrides of setup
content = content.replace(
'''                    if target.hp <= 60 or threat_lethal or (target.hp <= opp_max_dmg + poison_dmg):
                        action["score"] = POTION_CRITICAL_SCORE
                    # If it puts us out of lethal range
                    if threat_lethal and (target.hp + heal_amount) > (opp_max_dmg + poison_dmg):''',
'''                    if target == gs.my_active and (target.hp <= 60 or threat_lethal or (target.hp <= opp_max_dmg + poison_dmg)):
                        action["score"] = POTION_CRITICAL_SCORE
                    # If it puts us out of lethal range
                    if target == gs.my_active and threat_lethal and (target.hp + heal_amount) > (opp_max_dmg + poison_dmg):'''
)

with open("candidate_player.py", "w") as f:
    f.write(content)