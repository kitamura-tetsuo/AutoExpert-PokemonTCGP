import subprocess

def run_eval():
    result = subprocess.run([
        "uv", "run", "python", "vs_past_deck.py",
        "--deck_a", "deckgym-core/example_decks/venusaur-exeggutor.txt",
        "--matches", "1000",
        "--league_decks_teacher", "train_data/teacher.csv"
    ], capture_output=True, text=True)
    print(result.stdout)
    print(result.stderr)
run_eval()
