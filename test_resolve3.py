from pathlib import Path

class Settings:
    DECK_DIR = 'train_data'

settings = Settings()

def resolve_deck_path(deck: str) -> str:
    if not isinstance(deck, str):
        deck = str(deck)
    deck_path = Path(deck)
    if not deck_path.exists():
        # wait what if settings.DECK_DIR / deck returns a string?
        deck_path = f"{settings.DECK_DIR}/{deck}"
    if not deck_path.exists(): # This will throw AttributeError if deck_path is a string
        deck_path = Path("train_data") / deck
    return str(deck_path)

try:
    resolve_deck_path("nonexistent.txt")
except Exception as e:
    print(repr(e))
