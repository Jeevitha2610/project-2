from fastapi import APIRouter
from backend.app.schemas.system import SystemMetricsResponse
from backend.app.monitoring.system import SystemMonitor

router = APIRouter()

@router.get("/", response_model=SystemMetricsResponse)
def get_system_metrics():
    return SystemMonitor.get_metrics()
