import os
from pathlib import Path
import sys

def resolve_deck_path(deck: str) -> str:
    # Fix duplicate paths caused by earlier script
    if deck.startswith("train_data/train_data/"):
        deck = deck.replace("train_data/train_data/", "train_data/")

    deck_path = Path(deck)
    if not deck_path.exists():
        deck_path = Path("train_data") / deck

    # Also try just the filename in train_data/fix/
    if not deck_path.exists() and "fix" in str(deck):
        deck_path = Path("train_data/fix") / Path(deck).name

    if not deck_path.exists():
        deck_path = Path(deck).name
        if Path(deck_path).exists():
            return str(deck_path)

    # And relative to root in case we are deep
    if not Path(deck_path).exists():
         deck_path = Path("train_data") / "fix" / Path(deck).name

    # Fallback to known default deck if invalid
    if not Path(deck_path).exists():
        fallback_path = Path("deckgym-core/example_decks/venusaur-exeggutor.txt")
        if fallback_path.exists():
            return str(fallback_path)

    return str(deck_path)

print(resolve_deck_path("train_data/train_data/fix/venusaur-exeggutor-deck-6458541267731126208.txt"))
