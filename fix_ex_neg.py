import re

with open("candidate_player.py", "r") as f:
    content = f.read()

# Fix remaining negative checks
content = content.replace('"ex" not in b.name.lower()', 'not b.name.lower().endswith(" ex")')

with open("candidate_player.py", "w") as f:
    f.write(content)