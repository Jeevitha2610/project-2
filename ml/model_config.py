from pydantic import BaseModel

class ModelSettings(BaseModel):
    model_name: str = "IndicF5 (English)"
    device: str = "cpu"
    sample_rate: int = 24000
    n_fft: int = 1024
    hop_length: int = 256
    max_text_chars: int = 500
    default_temperature: float = 0.7
    default_speed: float = 1.0
    default_pitch: float = 0.0

default_model_config = ModelSettings()
