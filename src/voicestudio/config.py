"""
VoiceStudio Configuration & Environment Settings.

Defines global application defaults, paths, audio processing parameters,
quality gate thresholds, and server security policies.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class AudioConfig:
    """Audio DSP and quality gate configuration constants."""
    target_sample_rate: int = 24000
    asr_sample_rate: int = 16000
    min_duration_sec: float = 3.0
    max_duration_sec: float = 30.0
    min_snr_db: float = 15.0
    max_clipping_ratio: float = 0.001
    target_lufs: float = -23.0
    true_peak_limit_dbtp: float = -1.0
    highpass_cutoff_hz: float = 50.0
    highpass_order: int = 4
    num_rms_peaks: int = 200
    silence_threshold_db: float = -40.0
    min_silence_ms: float = 200.0


@dataclass(frozen=True)
class PathConfig:
    """Project filesystem paths."""
    base_dir: Path = field(default_factory=lambda: Path(__file__).resolve().parent.parent.parent)

    @property
    def data_dir(self) -> Path:
        return self.base_dir / "data"

    @property
    def reference_samples_dir(self) -> Path:
        return self.data_dir / "reference_samples"

    @property
    def references_dir(self) -> Path:
        return self.data_dir / "references"

    @property
    def generated_dir(self) -> Path:
        return self.data_dir / "generated"

    @property
    def reports_dir(self) -> Path:
        return self.base_dir / "reports"

    @property
    def db_path(self) -> Path:
        return self.data_dir / "studio.db"


@dataclass(frozen=True)
class ServerConfig:
    """Localhost HTTP server configuration."""
    host: str = "127.0.0.1"
    port: int = 3900
    watchdog_timeout_sec: int = 120
    is_localhost_only: bool = True


# Global Singleton Configuration Instances
AUDIO_CONFIG = AudioConfig()
PATH_CONFIG = PathConfig()
SERVER_CONFIG = ServerConfig()
