import re

with open("candidate_player.py", "r") as f:
    content = f.read()

pattern = r"""PLACE_BASIC_SCORE = 74000"""
replacement = r"""PLACE_BASIC_SCORE = 76000 # Boosted above ATTACH_ENERGY (75k) so we can attach to the new basic if it's better"""

content = re.sub(pattern, replacement, content)

with open("candidate_player.py", "w") as f:
    f.write(content)
