from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.database.session import get_db
from backend.app.schemas.synthesis import SynthesisRequest, SynthesisResponse
from backend.app.services.synthesis_service import SynthesisService

router = APIRouter()

@router.post("/generate", response_model=SynthesisResponse)
def generate_speech(request: SynthesisRequest, db: Session = Depends(get_db)):
    job = SynthesisService.generate_speech(db, request)
    return job

@router.get("/history", response_model=List[SynthesisResponse])
def get_history(limit: int = 50, db: Session = Depends(get_db)):
    return SynthesisService.get_history(db, limit)

@router.delete("/history/{job_id}")
def delete_generation(job_id: str, db: Session = Depends(get_db)):
    SynthesisService.delete_generation(db, job_id)
    return {"message": "Generation record deleted", "id": job_id}
