import os
import psutil
from typing import Dict, Any

class SystemMonitor:
    @staticmethod
    def get_metrics() -> Dict[str, Any]:
        """Returns current CPU, RAM, and Disk metrics."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        
        # Check disk space on workspace drive
        disk = psutil.disk_usage(os.path.abspath("."))
        
        return {
            "cpu_percent": round(cpu_percent, 1),
            "ram_used_gb": round(mem.used / (1024 ** 3), 1),
            "ram_total_gb": round(mem.total / (1024 ** 3), 1),
            "ram_percent": round(mem.percent, 1),
            "disk_free_gb": round(disk.free / (1024 ** 3), 1),
            "device": "CPU (Intel Core)",
            "model_name": "IndicF5 (English)",
            "model_status": "Loaded",
            "queue_length": 0
        }
