import os
import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import UploadFile, HTTPException

from backend.app.core.config import REFERENCES_DIR
from backend.app.database.models import VoiceProfile
from backend.app.schemas.profile import VoiceProfileCreate, VoiceProfileUpdate
from backend.app.audio.processor import AudioProcessor

class ProfileService:
    @staticmethod
    def create_profile(
        db: Session,
        name: str,
        audio_file: UploadFile,
        reference_transcript: Optional[str] = None,
        description: Optional[str] = None
    ) -> VoiceProfile:
        # Check name uniqueness
        existing = db.query(VoiceProfile).filter(VoiceProfile.name == name).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Voice profile with name '{name}' already exists.")

        # Save audio file to temp/raw path
        raw_filename = f"raw_{uuid.uuid4().hex[:12]}_{audio_file.filename}"
        raw_path = REFERENCES_DIR / raw_filename
        
        with open(raw_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)

        # Process reference audio: convert to mono, denoise, normalize loudness,
        # auto-transcribe with Whisper, trim to clean sentence boundary (6-10s) + trailing silence
        clean_filename = f"ref_{uuid.uuid4().hex[:10]}.wav"
        clean_path = REFERENCES_DIR / clean_filename

        try:
            processed_info = AudioProcessor.process_reference_audio(
                input_path=raw_path,
                output_path=clean_path,
                target_sr=24000,
                target_duration_range=(6.0, 10.0),
                trailing_silence_s=0.15
            )
            # Remove temporary raw file
            if raw_path.exists():
                os.remove(raw_path)
        except Exception as e:
            if raw_path.exists():
                os.remove(raw_path)
            if clean_path.exists():
                os.remove(clean_path)
            raise HTTPException(status_code=400, detail=f"Failed to process and transcribe reference audio: {str(e)}")

        final_transcript = processed_info.get("transcript", "").strip()
        if not final_transcript and reference_transcript:
            final_transcript = reference_transcript.strip()

        profile = VoiceProfile(
            name=name,
            description=description,
            reference_audio_path=str(clean_path),
            reference_audio_name=clean_filename,
            reference_transcript=final_transcript,
            duration_seconds=processed_info["duration_seconds"],
            sample_rate=processed_info["sample_rate"],
            channels=processed_info["channels"],
            audio_format="wav"
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def get_profiles(db: Session) -> List[VoiceProfile]:
        return db.query(VoiceProfile).order_by(VoiceProfile.created_at.desc()).all()

    @staticmethod
    def get_profile_by_id(db: Session, profile_id: str) -> Optional[VoiceProfile]:
        return db.query(VoiceProfile).filter(VoiceProfile.id == profile_id).first()

    @staticmethod
    def update_profile(db: Session, profile_id: str, update_data: VoiceProfileUpdate) -> VoiceProfile:
        profile = ProfileService.get_profile_by_id(db, profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
        
        if update_data.name is not None:
            conflict = db.query(VoiceProfile).filter(VoiceProfile.name == update_data.name, VoiceProfile.id != profile_id).first()
            if conflict:
                raise HTTPException(status_code=400, detail=f"Profile name '{update_data.name}' already taken")
            profile.name = update_data.name
            
        if update_data.description is not None:
            profile.description = update_data.description
        if update_data.reference_transcript is not None:
            profile.reference_transcript = update_data.reference_transcript

        db.commit()
        db.refresh(profile)
        return profile

    @staticmethod
    def delete_profile(db: Session, profile_id: str) -> bool:
        profile = ProfileService.get_profile_by_id(db, profile_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Profile not found")
            
        # Clean up file
        audio_path = Path(profile.reference_audio_path)
        if audio_path.exists():
            try:
                os.remove(audio_path)
            except Exception:
                pass
                
        db.delete(profile)
        db.commit()
        return True
