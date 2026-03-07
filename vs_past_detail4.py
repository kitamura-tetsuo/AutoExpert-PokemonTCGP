import sys
import subprocess

cmd = ["uv", "run", "python", "vs_past_deck.py", "--deck_a", "deckgym-core/example_decks/venusaur-exeggutor.txt", "--num_matches", "1", "--league_decks_teacher", "train_data/teacher.csv"]
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
for line in iter(p.stdout.readline, ''):
    if "is not iterable" in line:
        print("FOUND ERROR:", line)
        break
