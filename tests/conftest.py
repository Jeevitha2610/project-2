"""
VoiceStudio Global Pytest Fixtures and Test Harness Configuration.
"""

from __future__ import annotations

import io
import os
import shutil
import sqlite3
import tempfile
import uuid
from pathlib import Path
from typing import Callable, Generator, Tuple

import httpx
import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient

from tests.contracts import (
    SCHEMA_SQL,
    AudioProcessor,
    AudioValidator,
    DatabaseManager,
    create_test_api,
)


@pytest.fixture(scope="session")
def audio_synthesizer():
    """
    Factory fixture generating clean, short, long, noisy, clipped, corrupt
    16-bit PCM WAV buffers or arrays using numpy and soundfile/scipy.
    """
    def _generate(
        duration_sec: float = 3.5,
        sample_rate: int = 24000,
        freq_hz: float = 440.0,
        noise_level: float = 0.0,
        clip: bool = False,
        silent: bool = False,
        stereo: bool = False,
    ) -> Tuple[np.ndarray, int]:
        num_samples = int(duration_sec * sample_rate)
        if silent or num_samples <= 0:
            audio = np.zeros(max(1, num_samples), dtype=np.float32)
            if stereo:
                audio = np.stack([audio, audio], axis=-1)
            return audio, sample_rate

        t = np.linspace(0, duration_sec, num_samples, endpoint=False, dtype=np.float32)
        # 440Hz base tone with slight harmonics
        signal = 0.6 * np.sin(2 * np.pi * freq_hz * t) + 0.2 * np.sin(2 * np.pi * 2 * freq_hz * t)

        if noise_level > 0.0:
            noise = np.random.normal(0, noise_level, num_samples).astype(np.float32)
            signal = signal + noise

        if clip:
            signal = np.clip(signal * 5.0, -1.0, 1.0)
        else:
            signal = np.clip(signal, -0.98, 0.98)

        if stereo:
            signal = np.stack([signal, signal * 0.9], axis=-1)

        return signal.astype(np.float32), sample_rate

    return _generate


@pytest.fixture
def clean_wav_file(audio_synthesizer, tmp_path) -> Path:
    """Provides a valid 3.5s clean mono 24kHz 16-bit PCM WAV file."""
    audio, sr = audio_synthesizer(duration_sec=3.5, sample_rate=24000, freq_hz=440.0)
    p = tmp_path / "clean_reference.wav"
    sf.write(str(p), audio, sr, format="WAV", subtype="PCM_16")
    return p


@pytest.fixture
def short_wav_file(audio_synthesizer, tmp_path) -> Path:
    """Provides an invalid short WAV (0.4s < 1.0s limit) for boundary testing."""
    audio, sr = audio_synthesizer(duration_sec=0.4, sample_rate=24000)
    p = tmp_path / "short_audio.wav"
    sf.write(str(p), audio, sr, format="WAV", subtype="PCM_16")
    return p


@pytest.fixture
def long_wav_file(audio_synthesizer, tmp_path) -> Path:
    """Provides an audio file exceeding standard duration threshold (>30s)."""
    audio, sr = audio_synthesizer(duration_sec=35.0, sample_rate=24000)
    p = tmp_path / "long_audio.wav"
    sf.write(str(p), audio, sr, format="WAV", subtype="PCM_16")
    return p


@pytest.fixture
def noisy_wav_file(audio_synthesizer, tmp_path) -> Path:
    """Provides an audio file with low SNR (<15dB)."""
    audio, sr = audio_synthesizer(duration_sec=3.5, sample_rate=24000, noise_level=0.45)
    p = tmp_path / "noisy_audio.wav"
    sf.write(str(p), audio, sr, format="WAV", subtype="PCM_16")
    return p


@pytest.fixture
def clipped_wav_file(audio_synthesizer, tmp_path) -> Path:
    """Provides an audio file with heavy clipping."""
    audio, sr = audio_synthesizer(duration_sec=3.5, sample_rate=24000, clip=True)
    p = tmp_path / "clipped_audio.wav"
    sf.write(str(p), audio, sr, format="WAV", subtype="PCM_16")
    return p


@pytest.fixture
def silent_wav_file(audio_synthesizer, tmp_path) -> Path:
    """Provides a zero-energy silent audio file."""
    audio, sr = audio_synthesizer(duration_sec=3.5, sample_rate=24000, silent=True)
    p = tmp_path / "silent_audio.wav"
    sf.write(str(p), audio, sr, format="WAV", subtype="PCM_16")
    return p


@pytest.fixture
def corrupt_wav_file(tmp_path) -> Path:
    """Provides a file with a corrupted RIFF header."""
    p = tmp_path / "corrupt.wav"
    p.write_bytes(b"RIFF\x24\x00\x00\x00BAD_NOT_A_WAVE")
    return p


@pytest.fixture
def sample_audio_resolver(audio_synthesizer, tmp_path) -> Callable[[], Tuple[Path, str]]:
    """
    Checks for physical reference samples in `data/reference_samples/`
    with automatic fallback to high-quality synthetic speech-like WAV.
    """
    def _resolve() -> Tuple[Path, str]:
        ref_dir = Path("data/reference_samples")
        if ref_dir.exists():
            wavs = sorted(list(ref_dir.glob("*.wav")))
            if wavs:
                wav = wavs[0]
                txt_file = wav.with_suffix(".txt")
                transcript = (
                    txt_file.read_text(encoding="utf-8").strip()
                    if txt_file.exists()
                    else "Physical reference voice sample from dataset."
                )
                return wav, transcript

        # Fallback
        fallback_wav = tmp_path / "resolved_sample.wav"
        audio, sr = audio_synthesizer(duration_sec=4.0, sample_rate=24000, freq_hz=220.0)
        sf.write(str(fallback_wav), audio, sr, format="WAV", subtype="PCM_16")
        return fallback_wav, "This is a synthetic reference voice used for automated testing."

    return _resolve


@pytest.fixture
def test_db(tmp_path) -> Generator[DatabaseManager, None, None]:
    """Manages an isolated SQLite WAL temporary database with schema migrations."""
    db_file = tmp_path / f"test_{uuid.uuid4().hex[:8]}.db"
    db_manager = DatabaseManager(db_file)
    yield db_manager
    # Clean connection
    try:
        if db_file.exists():
            db_file.unlink(missing_ok=True)
    except OSError:
        pass


@pytest.fixture
def temp_storage_dir(tmp_path) -> Path:
    storage = tmp_path / "storage"
    (storage / "references").mkdir(parents=True, exist_ok=True)
    (storage / "generated").mkdir(parents=True, exist_ok=True)
    (storage / "reports").mkdir(parents=True, exist_ok=True)
    return storage


@pytest.fixture
def client(test_db, temp_storage_dir) -> Generator[TestClient, None, None]:
    """Provides a synchronous FastAPI TestClient configured with isolated db and storage."""
    app = create_test_api(test_db, temp_storage_dir)
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def async_client(test_db, temp_storage_dir):
    """Provides an httpx.AsyncClient transport for async tests."""
    app = create_test_api(test_db, temp_storage_dir)
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://testserver")
