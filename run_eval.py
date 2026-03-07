import re

with open("candidate_player.py", "r") as f:
    content = f.read()

# Make the bench boost more robust, perhaps slightly lower to avoid overriding critical plays but still prioritize bench over everything else
content = content.replace('a["score"] += 35000 # Boost attaching to late-game bench targets', 'a["score"] += 20000 # Boost attaching to late-game bench targets')

with open("candidate_player.py", "w") as f:
    f.write(content)

print("candidate_player.py modified successfully.")
