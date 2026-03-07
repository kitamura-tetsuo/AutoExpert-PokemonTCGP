import subprocess
import re

cmd = ["uv", "run", "python", "vs_past_deck.py", "--deck_a", "deckgym-core/example_decks/venusaur-exeggutor.txt", "--num_matches", "100", "--league_decks_teacher", "train_data/teacher.csv"]
res = subprocess.run(cmd, capture_output=True, text=True)
print(res.stdout)
print(res.stderr)
