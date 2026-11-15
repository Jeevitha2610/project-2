from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class SynthesisRequest(BaseModel):
    profile_id: Optional[str] = None
    profile_name: Optional[str] = None
    reference_audio_name: Optional[str] = None
    reference_transcript: Optional[str] = None
    
    target_text: str = Field(..., min_length=1, max_length=5000)
    speech_speed: float = Field(1.0, ge=0.5, le=2.0)
    pitch: float = Field(0.0, ge=-10.0, le=10.0)
    temperature: float = Field(0.7, ge=0.1, le=1.5)
    seed: Optional[int] = None
    output_format: str = Field("WAV (Lossless)")
    mode: Optional[str] = Field("draft", description="draft (8-10 steps) or final (16-20 steps)")
    wer_threshold: Optional[float] = Field(0.08, ge=0.0, le=1.0)
    consent_given: Optional[bool] = Field(True, description="Safety consent confirmed before cloning")

class SynthesisResponse(BaseModel):
    id: str
    profile_id: Optional[str] = None
    profile_name: str
    target_text: str
    status: str
    output_audio_url: Optional[str] = None
    duration_seconds: float
    sample_rate: int
    channels: int
    
    # Evaluation
    wer: float
    cer: float
    speaker_similarity: float
    recognized_transcript: Optional[str] = None
    rtf: Optional[float] = 0.0
    
    # Completeness gate
    chunk_metrics: Optional[List[Dict[str, Any]]] = None
    total_retries: Optional[int] = 0
    
    # Resources
    inference_time_seconds: float
    cpu_peak: float
    ram_peak_mb: float
    created_at: datetime

    class Config:
        from_attributes = True
