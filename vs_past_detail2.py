import sys
import subprocess

cmd = ["uv", "run", "python", "vs_past_deck.py", "--deck_a", "deckgym-core/example_decks/venusaur-exeggutor.txt", "--num_matches", "500", "--league_decks_teacher", "train_data/teacher.csv"]
subprocess.run(cmd)
