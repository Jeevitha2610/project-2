from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.schemas.profile import VoiceProfileResponse, VoiceProfileUpdate
from backend.app.services.profile_service import ProfileService

router = APIRouter()

@router.post("/", response_model=VoiceProfileResponse)
def create_profile(
    name: str = Form(...),
    audio_file: UploadFile = File(...),
    reference_transcript: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    profile = ProfileService.create_profile(
        db=db,
        name=name,
        audio_file=audio_file,
        reference_transcript=reference_transcript,
        description=description
    )
    profile.reference_audio_url = f"/data/references/{Path(profile.reference_audio_path).name}"
    return profile

@router.get("/progress")
def get_upload_processing_progress():
    from backend.app.audio.processor import get_processing_state
    return get_processing_state()

@router.get("/", response_model=List[VoiceProfileResponse])
def get_profiles(db: Session = Depends(get_db)):
    profiles = ProfileService.get_profiles(db)
    for p in profiles:
        from pathlib import Path
        filename = Path(p.reference_audio_path).name
        p.reference_audio_url = f"/data/references/{filename}"
    return profiles

@router.get("/{profile_id}", response_model=VoiceProfileResponse)
def get_profile(profile_id: str, db: Session = Depends(get_db)):
    profile = ProfileService.get_profile_by_id(db, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    from pathlib import Path
    filename = Path(profile.reference_audio_path).name
    profile.reference_audio_url = f"/data/references/{filename}"
    return profile

@router.put("/{profile_id}", response_model=VoiceProfileResponse)
def update_profile(profile_id: str, update_data: VoiceProfileUpdate, db: Session = Depends(get_db)):
    profile = ProfileService.update_profile(db, profile_id, update_data)
    from pathlib import Path
    filename = Path(profile.reference_audio_path).name
    profile.reference_audio_url = f"/data/references/{filename}"
    return profile

@router.delete("/{profile_id}")
def delete_profile(profile_id: str, db: Session = Depends(get_db)):
    ProfileService.delete_profile(db, profile_id)
    return {"message": "Profile successfully deleted", "id": profile_id}
