from pathlib import Path
import os
def resolve_deck_path(deck: str) -> str:
    print(f"input: {deck} type: {type(deck)}")
    if not isinstance(deck, str):
        deck = str(deck)
    deck_path = Path(deck)
    print(deck_path)
    if not deck_path.exists():
        print("not exists 1")
    if not deck_path.exists():
        print("not exists 2")
    return str(deck_path)

resolve_deck_path("deckgym-core/example_decks/venusaur-exeggutor.txt")
