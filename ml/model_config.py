from pydantic import BaseModel


class ModelSettings(BaseModel):
    # Display name shown in UI; model_id is the official F5-TTS config name
    model_name: str = "F5-TTS v1 (English)"
    model_id: str = "F5TTS_v1_Base"
    device: str = "cpu"
    sample_rate: int = 24000
    # Flow-matching ODE steps: 20 offers the optimal balance of high fidelity and fast CPU synthesis
    nfe_step: int = 20
    # Local ASR used only to verify text adherence (real WER/CER)
    asr_model_id: str = "openai/whisper-base.en"
    max_text_chars: int = 500
    default_temperature: float = 0.7
    default_speed: float = 1.0
    default_pitch: float = 0.0


default_model_config = ModelSettings()
