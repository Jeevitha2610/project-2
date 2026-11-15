from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class VoiceProfileBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    reference_transcript: Optional[str] = ""
    model_compatibility: str = "IndicF5 (English)"

class VoiceProfileCreate(VoiceProfileBase):
    pass

class VoiceProfileUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    reference_transcript: Optional[str] = None

class VoiceProfileResponse(VoiceProfileBase):
    id: str
    reference_audio_path: str
    reference_audio_name: str
    reference_audio_url: Optional[str] = None
    duration_seconds: float
    sample_rate: int
    channels: int
    audio_format: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
