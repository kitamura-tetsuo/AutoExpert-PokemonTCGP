from pathlib import Path
class settings:
    DECK_DIR = Path("decks")

def resolve_deck_path(deck: str) -> str:
    print(f"input: {deck} type: {type(deck)}")
    if not isinstance(deck, str):
        deck = str(deck)
    deck_path = Path(deck)
    if not deck_path.exists():
        deck_path = settings.DECK_DIR / deck
        print(f"after fallback 1: {deck_path} type: {type(deck_path)}")
    if not deck_path.exists():
        deck_path = Path("train_data") / deck
        print(f"after fallback 2: {deck_path} type: {type(deck_path)}")
    return str(deck_path)

resolve_deck_path("deckgym-core/example_decks/venusaur-exeggutor.txt")
resolve_deck_path("non_existent.txt")
