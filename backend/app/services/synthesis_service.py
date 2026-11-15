import os
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException

from backend.app.database.models import GenerationJob, VoiceProfile
from backend.app.schemas.synthesis import SynthesisRequest
from backend.app.services.profile_service import ProfileService
from ml.model_adapter import ModelAdapter

class SynthesisService:
    @staticmethod
    def generate_speech(db: Session, request: SynthesisRequest) -> GenerationJob:
        ref_path = None
        ref_transcript = None
        profile_name = "Default Voice"

        if request.profile_id:
            profile = ProfileService.get_profile_by_id(db, request.profile_id)
            if not profile:
                raise HTTPException(status_code=404, detail="Specified voice profile does not exist.")
            ref_path = profile.reference_audio_path
            ref_transcript = profile.reference_transcript
            profile_name = profile.name
        elif request.reference_audio_name:
            from backend.app.core.config import REFERENCES_DIR
            potential_file = REFERENCES_DIR / request.reference_audio_name
            if potential_file.exists():
                ref_path = str(potential_file)
                ref_transcript = request.reference_transcript or "Reference sentence"
                profile_name = request.profile_name or "Custom Voice"

        # Fallback to first profile if none given
        if not ref_path:
            first_profile = db.query(VoiceProfile).first()
            if first_profile:
                ref_path = first_profile.reference_audio_path
                ref_transcript = first_profile.reference_transcript
                profile_name = first_profile.name
            else:
                raise HTTPException(
                    status_code=400,
                    detail="No reference voice available. Upload a human voice recording (5-15 s) with its exact transcript first.",
                )

        # Execute synthesis through ML Model Adapter (real neural cloning)
        from ml.inference_engine import ModelNotAvailableError
        try:
            result = ModelAdapter.synthesize_speech(
                ref_audio_path=ref_path,
                ref_transcript=ref_transcript,
                target_text=request.target_text,
                speech_speed=request.speech_speed,
                pitch=request.pitch,
                temperature=request.temperature,
                seed=request.seed
            )
        except ModelNotAvailableError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        # Record Generation Job in Database
        job = GenerationJob(
            profile_id=request.profile_id,
            profile_name=profile_name,
            target_text=request.target_text,
            speech_speed=request.speech_speed,
            pitch=request.pitch,
            temperature=request.temperature,
            seed=request.seed,
            output_format=request.output_format,
            status="completed",
            output_audio_path=result["output_path"],
            output_audio_url=result["output_url"],
            duration_seconds=result["duration_seconds"],
            sample_rate=result["sample_rate"],
            channels=result["channels"],
            peak_amplitude=result["peak_amplitude"],
            snr_estimate=result["snr_estimate"],
            clipping_detected=result["clipping_detected"],
            silence_ratio=result["silence_ratio"],
            wer=result["wer"],
            cer=result["cer"],
            speaker_similarity=result["speaker_similarity"],
            recognized_transcript=result["recognized_transcript"],
            inference_time_seconds=result["inference_time_seconds"],
            cpu_peak=result["cpu_peak"],
            ram_peak_mb=result["ram_peak_mb"]
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    @staticmethod
    def get_history(db: Session, limit: int = 50) -> List[GenerationJob]:
        return db.query(GenerationJob).order_by(GenerationJob.created_at.desc()).limit(limit).all()

    @staticmethod
    def delete_generation(db: Session, job_id: str) -> bool:
        job = db.query(GenerationJob).filter(GenerationJob.id == job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Generation record not found")
        if job.output_audio_path and os.path.exists(job.output_audio_path):
            try:
                os.remove(job.output_audio_path)
            except Exception:
                pass
        db.delete(job)
        db.commit()
        return True
