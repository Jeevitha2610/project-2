import psutil
from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool

from ml.inference_engine import ModelNotAvailableError, voice_cloning_engine
from ml.model_adapter import ModelAdapter

router = APIRouter()

ACTIVE_ID = "f5tts-v1-en"


@router.get("/")
def get_models():
    info = ModelAdapter.get_model_info()
    rss_mb = round(psutil.Process().memory_info().rss / (1024**2), 1)
    return [
        {
            "id": ACTIVE_ID,
            "name": info["name"],
            "display_name": info["name"],
            "language": "English",
            "license": info["license"],
            "device": "CPU",
            "status": "Loaded" if info["is_loaded"] else "Unloaded",
            "ram_usage_mb": rss_mb,
            "sample_rate": info["sample_rate"],
            "last_error": info.get("last_error"),
        }
    ]


@router.post("/{model_id}/load")
async def load_model(model_id: str):
    if model_id != ACTIVE_ID:
        raise HTTPException(status_code=404, detail=f"Unknown model '{model_id}'")
    try:
        await run_in_threadpool(voice_cloning_engine.load)
    except ModelNotAvailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"message": f"Model '{model_id}' loaded for CPU inference."}


from pydantic import BaseModel
from backend.app.core.config import settings

class RemoteGpuRequest(BaseModel):
    url: str

@router.post("/remote-gpu")
def set_remote_gpu(req: RemoteGpuRequest):
    cleaned = req.url.strip()
    settings.REMOTE_GPU_URL = cleaned if cleaned else None
    return {"message": "Remote GPU URL updated", "remote_gpu_url": settings.REMOTE_GPU_URL}

@router.get("/remote-gpu")
def get_remote_gpu():
    return {"remote_gpu_url": getattr(settings, "REMOTE_GPU_URL", None)}
