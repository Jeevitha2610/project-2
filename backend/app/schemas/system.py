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
