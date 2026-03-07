import subprocess
import os
for i in range(5):
    res = subprocess.run(["uv", "run", "python", "vs_past_deck.py", "--deck_a", "deckgym-core/example_decks/venusaur-exeggutor.txt", "--num_matches", "500", "--league_decks_teacher", "train_data/teacher.csv", "--threshold", "0.01"], capture_output=True, text=True)
    if "CI check passed" in res.stdout:
        print(f"Run {i+1}: PASSED")
    else:
        for line in res.stdout.split('\n'):
             if "New AI  wins" in line or "Old AI  wins" in line or "Improvement" in line:
                 print(line)
        print(f"Run {i+1}: FAILED")
