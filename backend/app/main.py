import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception:
    pass

from backend.app.core.config import settings, REFERENCES_DIR, OUTPUTS_DIR
from backend.app.database.session import init_db, SessionLocal
from backend.app.database.models import VoiceProfile
from backend.app.api.router import api_router

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

@app.on_event("startup")
def on_startup():
    init_db()
    
    # Initialize sample profile if empty
    db = SessionLocal()
    try:
        count = db.query(VoiceProfile).count()
        if count == 0:
            import numpy as np
            import soundfile as sf
            
            sample_file = REFERENCES_DIR / "sample_reference.wav"
            if not sample_file.exists():
                # Generate clean 3-second natural voice tone
                sr = 24000
                t = np.linspace(0, 3.0, int(3.0 * sr), endpoint=False)
                # Multi-harmonic voice sound
                audio = 0.4 * np.sin(2 * np.pi * 140 * t) + 0.25 * np.sin(2 * np.pi * 280 * t) + 0.15 * np.sin(2 * np.pi * 420 * t)
                audio = audio * np.exp(-0.2 * t)
                sf.write(str(sample_file), audio.astype(np.float32), sr)
                
            sample_profile = VoiceProfile(
                name="My Voice (English)",
                description="Default clean reference voice for testing synthesis.",
                reference_audio_path=str(sample_file),
                reference_audio_name="reference.wav",
                reference_transcript="This is a reference sentence spoken by me.",
                duration_seconds=3.0,
                sample_rate=24000,
                channels=1,
                audio_format="wav"
            )
            db.add(sample_profile)
            db.commit()
    finally:
        db.close()

@app.get("/health")
def health_check():
    return {
        "status": "online",
        "version": settings.VERSION,
        "engine": "F5-TTS v1 (English)",
        "device": "CPU"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
