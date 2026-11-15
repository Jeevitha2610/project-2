import os
import threading
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception:
    pass

import psutil
import torch

# Configure torch threads to physical P-cores (configurable via VOICESTUDIO_NUM_THREADS)
_configured_threads = os.environ.get("VOICESTUDIO_NUM_THREADS")
if _configured_threads and _configured_threads.isdigit():
    torch.set_num_threads(int(_configured_threads))
else:
    # Default to physical cores (P-cores)
    p_cores = psutil.cpu_count(logical=False) or 4
    torch.set_num_threads(max(1, p_cores))

from backend.app.core.config import settings, REFERENCES_DIR, OUTPUTS_DIR
from backend.app.database.session import init_db, SessionLocal
from backend.app.database.models import VoiceProfile
from backend.app.api.router import api_router
from backend.app.audio.processor import get_whisper_model
from backend.app.evaluation.metrics import get_ecapa_classifier
from ml.inference_engine import voice_cloning_engine

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="VoiceStudio: High-fidelity Local English Voice Cloning Application"
)

# Enable CORS for localhost frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static audio directories
app.mount("/data/references", StaticFiles(directory=str(REFERENCES_DIR)), name="references")
app.mount("/data/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")

# Mount API
app.include_router(api_router, prefix=settings.API_V1_STR)

def _warmup_models():
    """Warms up F5-TTS, faster-whisper, and ECAPA-TDNN models once at server startup."""
    try:
        get_whisper_model()
    except Exception as e:
        print(f"Whisper warmup warning: {e}")
    try:
        get_ecapa_classifier()
    except Exception as e:
        print(f"ECAPA warmup warning: {e}")
    try:
        voice_cloning_engine.load()
    except Exception as e:
        print(f"TTS warmup warning: {e}")

@app.on_event("startup")
def on_startup():
    init_db()
    
    # Initialize sample profile if empty
    db = SessionLocal()
    try:
        count = db.query(VoiceProfile).count()
        if count == 0:
            sample_file = REFERENCES_DIR / "sample_reference.wav"
            if sample_file.exists():
                sample_profile = VoiceProfile(
                    name="My Voice (English)",
                    description="Default clean reference voice for testing synthesis.",
                    reference_audio_path=str(sample_file),
                    reference_audio_name="sample_reference.wav",
                    reference_transcript="Where there is righteousness in the heart, there is beauty in the character.",
                    duration_seconds=4.95,
                    sample_rate=24000,
                    channels=1,
                    audio_format="wav"
                )
                db.add(sample_profile)
                db.commit()
    finally:
        db.close()

    # Warm models asynchronously so startup is responsive, keeping them resident in RAM
    threading.Thread(target=_warmup_models, daemon=True).start()

@app.get("/health")
def health_check():
    return {
        "status": "online",
        "version": settings.VERSION,
        "engine": "F5-TTS v1 (English)",
        "device": "CPU",
        "threads": torch.get_num_threads(),
        "tts_loaded": voice_cloning_engine.is_loaded
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
