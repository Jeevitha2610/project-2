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
            "license": "Code MIT; weights CC-BY-NC-4.0 (non-commercial)",
            "last_error": voice_cloning_engine.last_error,
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
        seed: Optional[int] = None,
        mode: str = "draft",
        wer_threshold: float = 0.08,
    ) -> Dict[str, Any]:
        return voice_cloning_engine.synthesize(
            ref_audio_path=ref_audio_path,
            ref_transcript=ref_transcript,
            target_text=target_text,
            speech_speed=speech_speed,
            pitch=pitch,
            temperature=temperature,
            seed=seed,
            mode=mode,
            wer_threshold=wer_threshold,
        )
