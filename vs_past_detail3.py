import subprocess
import re

cmd = ["uv", "run", "python", "vs_past_deck.py", "--deck_a", "deckgym-core/example_decks/venusaur-exeggutor.txt", "--num_matches", "50", "--league_decks_teacher", "train_data/teacher.csv"]
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
for line in iter(p.stdout.readline, ''):
    if "ERROR" in line or "Selected Action" in line or "Venusaur" in line or "Attack" in line or "Attach" in line or "turn:" in line:
        pass
    print(line, end="")
