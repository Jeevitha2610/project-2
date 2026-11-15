from typing import Dict, Any, Optional
from ml.inference_engine import voice_cloning_engine

class ModelAdapter:
    @staticmethod
    def get_model_info() -> Dict[str, Any]:
        return {
            "name": voice_cloning_engine.model_name,
            "device": voice_cloning_engine.device,
            "is_loaded": voice_cloning_engine.is_loaded,
            "sample_rate": voice_cloning_engine.sample_rate,
            "license": "Apache-2.0 / Open Research",
            "supported_languages": ["English"]
        }

    @staticmethod
    def synthesize_speech(
        ref_audio_path: str,
        ref_transcript: str,
        target_text: str,
        speech_speed: float = 1.0,
        pitch: float = 0.0,
        temperature: float = 0.7,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        return voice_cloning_engine.synthesize(
            ref_audio_path=ref_audio_path,
            ref_transcript=ref_transcript,
            target_text=target_text,
            speech_speed=speech_speed,
            pitch=pitch,
            temperature=temperature,
            seed=seed
        )
