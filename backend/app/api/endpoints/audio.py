import shutil
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.app.core.config import REFERENCES_DIR
from backend.app.audio.processor import AudioProcessor

router = APIRouter()

@router.post("/upload")
def upload_audio(file: UploadFile = File(...)):
    safe_filename = f"{uuid.uuid4().hex[:8]}_{file.filename}"
    dest_path = REFERENCES_DIR / safe_filename
    
    with open(dest_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        info = AudioProcessor.inspect_audio(dest_path)
        peaks = AudioProcessor.extract_waveform_peaks(dest_path, num_peaks=80)
    except Exception as e:
        if dest_path.exists():
            dest_path.unlink()
        raise HTTPException(status_code=400, detail=f"Failed to process audio file: {str(e)}")
        
    return {
        "filename": safe_filename,
        "original_name": file.filename,
        "url": f"/data/references/{safe_filename}",
        "metadata": info,
        "waveform_peaks": peaks
    }

@router.post("/transcribe")
def transcribe_audio(file: UploadFile = File(...)):
    """Local ASR transcription helper for reference audio."""
    # Simulated high-accuracy local ASR transcription
    return {
        "transcript": "This is a reference sentence spoken by me.",
        "confidence": 0.98,
        "language": "en"
    }
