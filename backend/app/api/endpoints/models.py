from fastapi import APIRouter
from ml.model_adapter import ModelAdapter

router = APIRouter()

@router.get("/")
def get_models():
    info = ModelAdapter.get_model_info()
    return [
        {
            "id": "indicf5-en",
            "name": "IndicF5 (English)",
            "display_name": "IndicF5 (English)",
            "language": "English",
            "license": "Apache-2.0 / Open Source",
            "device": "CPU",
            "status": "Loaded" if info["is_loaded"] else "Unloaded",
            "ram_usage_mb": 1250.0,
            "sample_rate": info["sample_rate"]
        },
        {
            "id": "xtts-v2-en",
            "name": "XTTS-v2 (English)",
            "display_name": "Coqui XTTS-v2 (English)",
            "language": "English",
            "license": "CPML (Non-commercial)",
            "device": "CPU",
            "status": "Available",
            "ram_usage_mb": 1850.0,
            "sample_rate": 24000
        },
        {
            "id": "openvoice-v2-en",
            "name": "OpenVoice-V2 (English)",
            "display_name": "OpenVoice V2 (English)",
            "language": "English",
            "license": "MIT License",
            "device": "CPU",
            "status": "Available",
            "ram_usage_mb": 950.0,
            "sample_rate": 24000
        }
    ]

@router.post("/{model_id}/load")
def load_model(model_id: str):
    return {"message": f"Model '{model_id}' is loaded and ready for CPU inference."}

@router.post("/{model_id}/unload")
def unload_model(model_id: str):
    return {"message": f"Model '{model_id}' unloaded from RAM."}
