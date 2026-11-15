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
        reference_transcript: str,
        audio_file: UploadFile,
        description: Optional[str] = None
    ) -> VoiceProfile:
        # Check name uniqueness
        existing = db.query(VoiceProfile).filter(VoiceProfile.name == name).first()
        if existing:
            raise HTTPException(status_code=400, detail=f"Voice profile with name '{name}' already exists.")

        # Save audio file
        file_ext = Path(audio_file.filename).suffix.lower()
        if not file_ext:
            file_ext = ".wav"
        safe_filename = f"{uuid.uuid4().hex[:12]}_{audio_file.filename}"
        dest_path = REFERENCES_DIR / safe_filename
        
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)

        # Inspect and validate audio
        try:
            audio_info = AudioProcessor.inspect_audio(dest_path)
        except Exception as e:
            if dest_path.exists():
                os.remove(dest_path)
            raise HTTPException(status_code=400, detail=f"Invalid or corrupted audio file: {str(e)}")

        profile = VoiceProfile(
            name=name,
            description=description,
            reference_audio_path=str(dest_path),
            reference_audio_name=audio_file.filename,
            reference_transcript=reference_transcript,
            duration_seconds=audio_info["duration_seconds"],
            sample_rate=audio_info["sample_rate"],
            channels=audio_info["channels"],
            audio_format=audio_info["format"]
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
            # check conflict
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
