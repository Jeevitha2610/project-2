"""Reference Audio and Mel Spectrogram Cache.

Caches processed mono/denoised/normalized reference audio and its mel spectrogram
so F5-TTS does not recompute or reprocess the reference per request.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import numpy as np
import soundfile as sf
import torch


class ReferenceCache:
    def __init__(self) -> None:
        self._cache: Dict[str, Dict[str, Any]] = {}

    def _get_key(self, audio_path: str | Path) -> str:
        p = Path(audio_path).resolve()
        if not p.exists():
            return str(p)
        mtime = p.stat().st_mtime
        return f"{p}:{mtime}"

    def get(self, audio_path: str | Path) -> Optional[Dict[str, Any]]:
        key = self._get_key(audio_path)
        return self._cache.get(key)

    def set(
        self,
        audio_path: str | Path,
        cleaned_path: str | Path,
        transcript: str,
        audio_tensor: Optional[torch.Tensor] = None,
        mel_spec: Optional[torch.Tensor] = None,
    ) -> None:
        key = self._get_key(audio_path)
        self._cache[key] = {
            "cleaned_path": str(cleaned_path),
            "transcript": transcript,
            "audio_tensor": audio_tensor,
            "mel_spec": mel_spec,
        }

    def clear(self) -> None:
        self._cache.clear()


# Global singleton instance
reference_cache = ReferenceCache()
