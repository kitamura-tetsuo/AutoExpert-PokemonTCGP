import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    JULES_API_KEY: str = os.getenv("JULES_API_KEY", "")
    JULES_API_URL: str = "https://jules.googleapis.com/v1alpha"
    
    # Simulation settings
    NUM_SIMULATIONS: int = 100
    MAX_ITERATIONS: int = 50
    MAX_RETRIES_PER_GOAL: int = 3
    
    # Paths
    BASE_DIR: Path = Path(__file__).parent.parent
    SKILL_LIBRARY_DIR: Path = BASE_DIR / "skill_library"
    CHECKPOINT_DIR: Path = BASE_DIR / "checkpoints"
    DECK_DIR: Path = BASE_DIR / "deckgym-core" / "example_decks"
    
    # LLM Settings
    DEFAULT_MODEL: str = "jules"  # We'll use Jules API

settings = Settings()
