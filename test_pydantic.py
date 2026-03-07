from pydantic_settings import BaseSettings
from pathlib import Path
import os
os.environ["DECK_DIR"] = "/tmp/mocked_dir"
class Settings(BaseSettings):
    DECK_DIR: Path = Path("/default")
s = Settings()
print(type(s.DECK_DIR))
