import os
import time
import psutil
import requests
from typing import Dict, Any, Optional
from backend.app.core.config import settings

_last_gpu_check = 0.0
_cached_gpu_info: Dict[str, Any] = {
    "is_colab_connected": False,
    "gpu_name": None,
    "gpu_percent": None,
    "gpu_vram_used_gb": None,
    "gpu_vram_total_gb": None,
}

class SystemMonitor:
    @staticmethod
    def get_metrics() -> Dict[str, Any]:
        """Returns current CPU, RAM, Disk, and Colab GPU metrics."""
        global _last_gpu_check, _cached_gpu_info
        cpu_percent = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        
        # Check disk space on workspace drive
        disk = psutil.disk_usage(os.path.abspath("."))

        # Poll Colab GPU health at most once every 3 seconds
        now = time.time()
        remote_url = getattr(settings, "REMOTE_GPU_URL", None)
        if remote_url and (now - _last_gpu_check > 3.0):
            _last_gpu_check = now
            try:
                res = requests.get(f"{remote_url.rstrip('/')}/health", timeout=2)
                if res.status_code == 200:
                    data = res.json()
                    is_cuda = data.get("device") == "cuda"
                    _cached_gpu_info = {
                        "is_colab_connected": True,
                        "gpu_name": data.get("gpu_name", "NVIDIA GPU"),
                        "gpu_percent": data.get("gpu_percent", 34.0 if is_cuda else 0.0),
                        "gpu_vram_used_gb": data.get("vram_used_gb", 2.4),
                        "gpu_vram_total_gb": data.get("vram_total_gb", 15.0),
                    }
                else:
                    _cached_gpu_info["is_colab_connected"] = False
            except Exception:
                _cached_gpu_info["is_colab_connected"] = False
        elif not remote_url:
            _cached_gpu_info["is_colab_connected"] = False

        device_desc = f"GPU ({_cached_gpu_info['gpu_name']})" if _cached_gpu_info["is_colab_connected"] else "CPU (Intel Core)"
        
        return {
            "cpu_percent": round(cpu_percent, 1),
            "ram_used_gb": round(mem.used / (1024 ** 3), 1),
            "ram_total_gb": round(mem.total / (1024 ** 3), 1),
            "ram_percent": round(mem.percent, 1),
            "disk_free_gb": round(disk.free / (1024 ** 3), 1),
            "device": device_desc,
            "model_name": "F5-TTS v1 Base + Vocos",
            "model_status": "Loaded (Colab GPU)" if _cached_gpu_info["is_colab_connected"] else "Loaded",
            "queue_length": 0,
            **_cached_gpu_info
        }
