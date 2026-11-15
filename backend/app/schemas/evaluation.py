from typing import Optional
from pydantic import BaseModel

class EvaluationMetrics(BaseModel):
    wer: float  # Word Error Rate (0.0 to 1.0 or percentage)
    cer: float  # Character Error Rate
    insertions: int
    deletions: int
    substitutions: int
    recognized_transcript: str
    target_text: str
    speaker_similarity: float  # Cosine similarity on acoustic speaker embeddings
    peak_amplitude: float
    clipping_detected: bool
    silence_ratio: float
    snr_estimate: float
    duration_seconds: float
    sample_rate: int
    channels: int
