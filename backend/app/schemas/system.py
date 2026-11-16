from typing import Optional
from pydantic import BaseModel

class SystemMetricsResponse(BaseModel):
    cpu_percent: float
    ram_used_gb: float
    ram_total_gb: float
    ram_percent: float
    disk_free_gb: float
    device: str
    model_name: str
    model_status: str
    queue_length: int
    gpu_name: Optional[str] = None
    gpu_percent: Optional[float] = None
    gpu_vram_used_gb: Optional[float] = None
    gpu_vram_total_gb: Optional[float] = None
    is_colab_connected: Optional[bool] = False
