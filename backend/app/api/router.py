from fastapi import APIRouter
from backend.app.api.endpoints import profiles, synthesis, models, monitoring, audio

api_router = APIRouter()

api_router.include_router(profiles.router, prefix="/profiles", tags=["Profiles"])
api_router.include_router(synthesis.router, prefix="/synthesis", tags=["Synthesis"])
api_router.include_router(models.router, prefix="/models", tags=["Models"])
api_router.include_router(monitoring.router, prefix="/monitoring", tags=["Monitoring"])
api_router.include_router(audio.router, prefix="/audio", tags=["Audio"])
