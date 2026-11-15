import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.database.session import Base

class VoiceProfile(Base):
    __tablename__ = "voice_profiles"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255), nullable=True)
    reference_audio_path = Column(String(500), nullable=False)
    reference_audio_name = Column(String(255), nullable=False)
    reference_transcript = Column(Text, nullable=False)
    duration_seconds = Column(Float, default=0.0)
    sample_rate = Column(Integer, default=24000)
    channels = Column(Integer, default=1)
    audio_format = Column(String(20), default="wav")
    model_compatibility = Column(String(100), default="IndicF5 (English)")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    generations = relationship("GenerationJob", back_populates="profile", cascade="all, delete-orphan")


class GenerationJob(Base):
    __tablename__ = "generation_jobs"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    profile_id = Column(String(36), ForeignKey("voice_profiles.id", ondelete="SET NULL"), nullable=True)
    profile_name = Column(String(100), nullable=False)
    target_text = Column(Text, nullable=False)
    speech_speed = Column(Float, default=1.0)
    pitch = Column(Float, default=0.0)
    temperature = Column(Float, default=0.7)
    seed = Column(Integer, nullable=True)
    output_format = Column(String(20), default="WAV (Lossless)")
    status = Column(String(30), default="pending")  # pending, processing, completed, failed
    
    # Generated Audio Properties
    output_audio_path = Column(String(500), nullable=True)
    output_audio_url = Column(String(500), nullable=True)
    duration_seconds = Column(Float, default=0.0)
    sample_rate = Column(Integer, default=24000)
    channels = Column(Integer, default=1)
    peak_amplitude = Column(Float, default=0.0)
    snr_estimate = Column(Float, default=0.0)
    clipping_detected = Column(Boolean, default=False)
    silence_ratio = Column(Float, default=0.0)
    
    # Independent Evaluation Metrics
    wer = Column(Float, default=0.0)
    cer = Column(Float, default=0.0)
    speaker_similarity = Column(Float, default=0.0)
    recognized_transcript = Column(Text, nullable=True)
    rtf = Column(Float, default=0.0)  # Real-Time Factor: inference_time / duration
    
    # Completeness Gate & Chunking
    chunk_metrics = Column(JSON, nullable=True)
    total_retries = Column(Integer, default=0)
    
    # Performance & System Resource Metrics
    inference_time_seconds = Column(Float, default=0.0)
    cpu_peak = Column(Float, default=0.0)
    ram_peak_mb = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    profile = relationship("VoiceProfile", back_populates="generations")


class AuditRecord(Base):
    __tablename__ = "audit_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime, default=datetime.utcnow)
    ref_audio_hash = Column(String(64), nullable=False)
    target_text_hash = Column(String(64), nullable=False)
    profile_name = Column(String(100), nullable=True)
    consent_given = Column(Boolean, default=True)


class ModelRecord(Base):
    __tablename__ = "model_records"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    display_name = Column(String(100), nullable=False)
    language = Column(String(50), default="English")
    license = Column(String(100), default="Apache-2.0 / MIT")
    is_loaded = Column(Boolean, default=True)
    device = Column(String(50), default="CPU")
    ram_usage_mb = Column(Float, default=1250.0)
    status = Column(String(50), default="Loaded")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
