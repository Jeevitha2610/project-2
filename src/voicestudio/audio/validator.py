"""
VoiceStudio Audio Quality Validator.

Provides format inspection, container validation, duration bounds checking,
clipping detection, silence/energy ratio verification, and blind SNR estimation
for reference audio recordings.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Union

import numpy as np
import soundfile as sf


# ============================================================================
# Typed Audio Quality & Format Exceptions
# ============================================================================

class AudioValidationError(Exception):
    """Base exception for audio quality and validation failures."""
    pass


class InvalidAudioFormatError(AudioValidationError):
    """Raised when audio container header is corrupt, missing, or unsupported."""
    pass


class AudioTooShortError(AudioValidationError):
    """Raised when audio duration is below the minimum threshold."""
    pass


class AudioTooLongError(AudioValidationError):
    """Raised when audio duration exceeds the maximum allowed threshold."""
    pass


class AudioClippingError(AudioValidationError):
    """Raised when audio contains excessive digital clipping."""
    pass


class AudioSilentError(AudioValidationError):
    """Raised when audio is silent or lacks audible voice energy."""
    pass


class ExcessiveNoiseError(AudioValidationError):
    """Raised when estimated SNR is below the acceptable quality threshold."""
    pass


# ============================================================================
# Result Containers
# ============================================================================

@dataclass
class AudioFormatResult:
    """Format and container metadata extraction result."""
    is_valid: bool
    format: str                     # e.g., 'WAV', 'FLAC', 'OGG', 'MP3'
    sample_rate: int                # e.g., 24000, 44100, 16000
    channels: int                   # e.g., 1 (mono), 2 (stereo)
    bit_depth: int                  # e.g., 16, 24, 32
    duration_sec: float             # Duration in seconds
    reasons: List[str] = field(default_factory=list)


@dataclass
class QualityValidationResult:
    """Audio quality metrics and validation gate result."""
    is_valid: bool
    duration_sec: float
    snr_db: float
    clipping_ratio: float
    is_silent: bool
    reasons: List[str] = field(default_factory=list)


# ============================================================================
# AudioValidator Implementation
# ============================================================================

class AudioValidator:
    """
    Enforces quality gates on voice cloning reference recordings.

    Gates:
    1. Container validity (WAV, FLAC, OGG, MP3) and header integrity.
    2. Duration bounds: 3.0s minimum to 30.0s maximum.
    3. Clipping ratio: <= 0.001 (0.1%) samples with |x| >= 0.999.
    4. Silence / energy: RMS >= 1e-4 and active speech frame ratio >= 10%.
    5. SNR: Blind SNR >= 15.0 dB (Quartile or WADA-SNR).
    """

    # WADA-SNR precomputed mapping table (Gamma shape = 0.4)
    _WADA_DB_VALS = np.arange(-20, 101)
    _WADA_G_VALS = np.array([
        0.40974774, 0.40986926, 0.40998566, 0.40969089, 0.40986186, 0.40999006,
        0.41027138, 0.41052627, 0.41101024, 0.41143264, 0.41231718, 0.41337272,
        0.41526426, 0.41781920, 0.42077252, 0.42452799, 0.42918886, 0.43510373,
        0.44234195, 0.45161485, 0.46221153, 0.47491647, 0.48883809, 0.50509236,
        0.52353709, 0.54372088, 0.56532427, 0.58847532, 0.61346212, 0.63954496,
        0.66750818, 0.69583724, 0.72454762, 0.75414799, 0.78323148, 0.81240985,
        0.84219775, 0.87166406, 0.90030504, 0.92880418, 0.95655449, 0.98353490,
        1.01047155, 1.03620950, 1.06136425, 1.08579312, 1.10948190, 1.13277995,
        1.15472826, 1.17627308, 1.19703503, 1.21671694, 1.23535898, 1.25364313,
        1.27103891, 1.28718029, 1.30302865, 1.31839527, 1.33294817, 1.34700935,
        1.36057270, 1.37345513, 1.38577122, 1.39733504, 1.40856397, 1.41959619,
        1.42983624, 1.43958467, 1.44902176, 1.45804831, 1.46669568, 1.47486938,
        1.48269965, 1.49034339, 1.49748214, 1.50435106, 1.51076426, 1.51698915,
        1.52290970, 1.52857800, 1.53389835, 1.53912110, 1.54390650, 1.54858517,
        1.55310776, 1.55744391, 1.56164927, 1.56566348, 1.56938671, 1.57307767,
        1.57654764, 1.57980083, 1.58304129, 1.58602496, 1.58880681, 1.59162477,
        1.59419690, 1.59693155, 1.59944600, 1.60185011, 1.60408668, 1.60627134,
        1.60826199, 1.61004547, 1.61985374, 1.62135878, 1.62268119, 1.62390423,
        1.62513143, 1.62632463, 1.62740270, 1.62842767, 1.62945532, 1.63033070,
        1.63128026, 1.63204102
    ])

    def __init__(
        self,
        min_duration_sec: float = 3.0,
        max_duration_sec: float = 30.0,
        min_snr_db: float = 15.0,
        max_clipping_ratio: float = 0.001,
        silence_rms_threshold: float = 1e-4,
        min_active_speech_ratio: float = 0.10,
        snr_method: str = "quartile",
    ):
        self.min_duration_sec = min_duration_sec
        self.max_duration_sec = max_duration_sec
        self.min_snr_db = min_snr_db
        self.max_clipping_ratio = max_clipping_ratio
        self.silence_rms_threshold = silence_rms_threshold
        self.min_active_speech_ratio = min_active_speech_ratio
        self.snr_method = snr_method

    @classmethod
    def validate_format(cls_or_self, file_path: Union[str, Path]) -> AudioFormatResult:
        """
        Inspects file container and header validity without loading audio into memory.
        """
        path = Path(file_path)
        if not path.exists():
            return AudioFormatResult(
                is_valid=False,
                format="UNKNOWN",
                sample_rate=0,
                channels=0,
                bit_depth=0,
                duration_sec=0.0,
                reasons=[f"File does not exist: {path}"]
            )
        if not path.is_file():
            return AudioFormatResult(
                is_valid=False,
                format="UNKNOWN",
                sample_rate=0,
                channels=0,
                bit_depth=0,
                duration_sec=0.0,
                reasons=[f"Path is not a regular file: {path}"]
            )
        if path.stat().st_size == 0:
            return AudioFormatResult(
                is_valid=False,
                format="UNKNOWN",
                sample_rate=0,
                channels=0,
                bit_depth=0,
                duration_sec=0.0,
                reasons=[f"File is empty (0 bytes): {path}"]
            )

        try:
            info = sf.info(str(path))
            fmt = info.format or "UNKNOWN"
            sr = info.samplerate
            ch = info.channels
            dur = info.duration
            subtype = info.subtype or ""

            bit_depth = 16
            if "16" in subtype:
                bit_depth = 16
            elif "24" in subtype:
                bit_depth = 24
            elif "32" in subtype or "FLOAT" in subtype:
                bit_depth = 32
            elif "8" in subtype:
                bit_depth = 8

            reasons: List[str] = []
            if fmt.upper() not in {"WAV", "FLAC", "OGG", "MP3", "AIFF"}:
                reasons.append(f"Unsupported audio container format: {fmt}")
            if sr < 8000 or sr > 192000:
                reasons.append(f"Sample rate out of supported range (8k-192k): {sr} Hz")
            if ch < 1 or ch > 8:
                reasons.append(f"Unsupported channel count: {ch}")
            if dur <= 0.0:
                reasons.append(f"Invalid audio duration: {dur:.2f}s")

            return AudioFormatResult(
                is_valid=len(reasons) == 0,
                format=fmt,
                sample_rate=sr,
                channels=ch,
                bit_depth=bit_depth,
                duration_sec=dur,
                reasons=reasons
            )
        except Exception as exc:
            return AudioFormatResult(
                is_valid=False,
                format="CORRUPT",
                sample_rate=0,
                channels=0,
                bit_depth=0,
                duration_sec=0.0,
                reasons=[f"Failed to parse audio container or corrupt header: {str(exc)}"]
            )

    @classmethod
    def estimate_snr_wada(cls_or_self, audio: np.ndarray) -> float:
        """
        Waveform Amplitude Distribution Analysis SNR estimator (Kim & Stern 2008).
        """
        eps = 1e-10
        wav = np.asarray(audio, dtype=np.float64).flatten()
        if wav.size == 0 or np.all(wav == 0):
            return 0.0

        max_val = np.max(np.abs(wav))
        if max_val > 0:
            wav = wav / max_val

        a_d = np.abs(wav)
        a_d = np.maximum(a_d, eps)

        d_val1 = np.mean(a_d)
        d_val2 = np.mean(np.log(a_d))
        if d_val1 <= 0:
            return 0.0

        d_val3 = np.log(d_val1) - d_val2
        db_vals = AudioValidator._WADA_DB_VALS[:len(AudioValidator._WADA_G_VALS)]

        if d_val3 <= AudioValidator._WADA_G_VALS[0]:
            return float(db_vals[0])
        elif d_val3 >= AudioValidator._WADA_G_VALS[-1]:
            return float(db_vals[-1])

        estimated_snr = float(np.interp(d_val3, AudioValidator._WADA_G_VALS, db_vals))
        return round(float(np.clip(estimated_snr, -20.0, 80.0)), 2)

    def estimate_snr_quartile(
        self_or_cls,
        audio: np.ndarray,
        sample_rate: int,
    ) -> float:
        """
        Short-time frame energy quartile SNR estimator (P85 - P15).
        """
        audio_flat = np.asarray(audio, dtype=np.float64).flatten()
        if audio_flat.size == 0:
            return 0.0

        silence_thresh = getattr(self_or_cls, "silence_rms_threshold", 1e-4)

        frame_ms, hop_ms = 25.0, 10.0
        frame_len = max(1, int(sample_rate * frame_ms / 1000.0))
        hop_len = max(1, int(sample_rate * hop_ms / 1000.0))

        if len(audio_flat) < frame_len:
            rms = np.sqrt(np.mean(audio_flat ** 2))
            return 0.0 if rms < silence_thresh else 20.0

        num_frames = 1 + (len(audio_flat) - frame_len) // hop_len
        frames = np.lib.stride_tricks.as_strided(
            audio_flat,
            shape=(num_frames, frame_len),
            strides=(audio_flat.strides[0] * hop_len, audio_flat.strides[0])
        )
        frame_power = np.mean(frames ** 2, axis=1)
        frame_db = 10.0 * np.log10(np.maximum(frame_power, 1e-12))

        # Stationary signal guard (e.g. constant white noise or pure tone without pauses)
        if np.std(frame_db) < 2.0:
            return 0.0

        noise_floor_db = float(np.percentile(frame_db, 15))
        signal_level_db = float(np.percentile(frame_db, 85))
        snr = signal_level_db - noise_floor_db
        return round(float(np.clip(snr, 0.0, 80.0)), 2)

    def estimate_snr(
        self_or_cls,
        audio: np.ndarray,
        sample_rate: int,
    ) -> float:
        """
        Routes to configured blind SNR estimation method.
        """
        method = getattr(self_or_cls, "snr_method", "quartile")
        if method == "wada":
            return AudioValidator.estimate_snr_wada(audio)
        return AudioValidator.estimate_snr_quartile(self_or_cls, audio, sample_rate)

    def validate_quality(
        self_or_cls,
        audio: np.ndarray,
        sample_rate: int,
        strict_duration: bool = False,
    ) -> QualityValidationResult:
        """
        Enforces duration bounds, clipping, silence/energy, and SNR quality gates.
        """
        # Resolve configuration values
        min_dur = getattr(self_or_cls, "min_duration_sec", 3.0)
        max_dur = getattr(self_or_cls, "max_duration_sec", 30.0)
        min_snr = getattr(self_or_cls, "min_snr_db", 15.0)
        max_clip = getattr(self_or_cls, "max_clipping_ratio", 0.001)
        silence_thresh = getattr(self_or_cls, "silence_rms_threshold", 1e-4)
        min_active_ratio = getattr(self_or_cls, "min_active_speech_ratio", 0.10)

        audio_flat = np.asarray(audio, dtype=np.float32).flatten()

        # Normalize integer types if supplied
        if np.issubdtype(audio.dtype, np.integer):
            if audio.dtype == np.int16:
                audio_flat = audio_flat / 32768.0
            elif audio.dtype == np.int32:
                audio_flat = audio_flat / 2147483648.0
            elif audio.dtype == np.uint8:
                audio_flat = (audio_flat - 128.0) / 128.0

        duration_sec = len(audio_flat) / max(1, sample_rate)
        reasons: List[str] = []

        # 1. Duration bounds quality gate [3.0s, 30.0s]
        if duration_sec < min_dur:
            reasons.append(
                f"Audio duration {duration_sec:.2f}s is below minimum threshold of {min_dur:.1f}s"
            )
        elif duration_sec > max_dur:
            reasons.append(
                f"Audio duration {duration_sec:.2f}s exceeds maximum threshold of {max_dur:.1f}s"
            )

        # 2. Clipping detection (|x| >= 0.999)
        if audio_flat.size > 0:
            clipped_count = np.sum(np.abs(audio_flat) >= 0.999)
            clipping_ratio = float(clipped_count) / float(audio_flat.size)
        else:
            clipping_ratio = 0.0

        if clipping_ratio > max_clip:
            reasons.append(
                f"Clipping ratio {clipping_ratio * 100:.3f}% exceeds maximum threshold of {max_clip * 100:.3f}%"
            )

        # 3. Energy ratio / silence check
        rms = float(np.sqrt(np.mean(audio_flat ** 2))) if audio_flat.size > 0 else 0.0
        frame_len = max(1, int(sample_rate * 0.025))
        if len(audio_flat) >= frame_len:
            reshaped = audio_flat[:(len(audio_flat) // frame_len) * frame_len].reshape(-1, frame_len)
            frame_rms = np.sqrt(np.mean(reshaped ** 2, axis=1))
            active_ratio = float(np.mean(frame_rms > silence_thresh))
        else:
            active_ratio = 1.0 if rms > silence_thresh else 0.0

        is_silent = (rms < silence_thresh) or (active_ratio < min_active_ratio)
        if is_silent:
            reasons.append(
                f"Audio is silent or lacks active speech energy (RMS={rms:.2e}, active ratio={active_ratio:.1%})"
            )

        # 4. SNR estimation gate (>= 15.0 dB)
        snr_db = AudioValidator.estimate_snr(self_or_cls, audio_flat, sample_rate)
        if snr_db < min_snr and not is_silent:
            reasons.append(
                f"Estimated SNR {snr_db:.1f} dB is below required threshold of {min_snr:.1f} dB"
            )

        is_valid = len(reasons) == 0
        return QualityValidationResult(
            is_valid=is_valid,
            duration_sec=round(duration_sec, 3),
            snr_db=snr_db,
            clipping_ratio=round(clipping_ratio, 6),
            is_silent=is_silent,
            reasons=reasons
        )

    def validate_or_raise(
        self_or_cls,
        audio: np.ndarray,
        sample_rate: int,
    ) -> None:
        """
        Validates audio quality and raises specific typed exceptions on failure.
        """
        res = AudioValidator.validate_quality(self_or_cls, audio, sample_rate)
        if res.is_valid:
            return

        min_dur = getattr(self_or_cls, "min_duration_sec", 3.0)
        max_dur = getattr(self_or_cls, "max_duration_sec", 30.0)
        max_clip = getattr(self_or_cls, "max_clipping_ratio", 0.001)
        min_snr = getattr(self_or_cls, "min_snr_db", 15.0)

        if res.is_silent:
            raise AudioSilentError(f"Audio validation failed: {res.reasons[0]}")
        if res.duration_sec < min_dur:
            raise AudioTooShortError(f"Audio validation failed: {res.reasons[0]}")
        if res.duration_sec > max_dur:
            raise AudioTooLongError(f"Audio validation failed: {res.reasons[0]}")
        if res.clipping_ratio > max_clip:
            raise AudioClippingError(f"Audio validation failed: {res.reasons[0]}")
        if res.snr_db < min_snr:
            raise ExcessiveNoiseError(f"Audio validation failed: {res.reasons[0]}")
        raise AudioValidationError(f"Audio validation failed: {'; '.join(res.reasons)}")
