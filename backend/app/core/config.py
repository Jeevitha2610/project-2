import os
from pathlib import Path
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = BASE_DIR / "data"
PROFILES_DIR = DATA_DIR / "profiles"
REFERENCES_DIR = DATA_DIR / "references"
OUTPUTS_DIR = DATA_DIR / "outputs"
CACHE_DIR = DATA_DIR / "cache"
DB_DIR = DATA_DIR / "database"

# Ensure directories exist
for directory in [PROFILES_DIR, REFERENCES_DIR, OUTPUTS_DIR, CACHE_DIR, DB_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

class Settings(BaseModel):
    PROJECT_NAME: str = "VoiceStudio"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    DATABASE_URL: str = f"sqlite:///{DB_DIR / 'voicestudio.db'}"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    MAX_UPLOAD_SIZE_BYTES: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_AUDIO_EXTENSIONS: list[str] = [".wav", ".mp3", ".flac", ".ogg", ".m4a"]
    DEFAULT_SAMPLE_RATE: int = 24000
    REMOTE_GPU_URL: str | None = os.environ.get("VOICESTUDIO_REMOTE_GPU_URL", "https://earlier-beast-marina-blank.trycloudflare.com")

settings = Settings()
