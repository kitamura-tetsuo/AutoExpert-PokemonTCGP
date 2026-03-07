import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DECK_DIR: str = "train_data"

settings = Settings()

def resolve_deck_path(deck: str) -> str:
    if not isinstance(deck, str):
        deck = str(deck)
    deck_path = Path(deck)
    if not deck_path.exists():
        deck_path = Path(settings.DECK_DIR) / deck
    if not getattr(deck_path, "exists", lambda: False)():
        deck_path = Path("train_data") / deck
    return str(deck_path)

resolve_deck_path("unknown.txt")
