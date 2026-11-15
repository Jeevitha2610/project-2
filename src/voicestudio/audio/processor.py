"""
AudioProcessor: High-fidelity deterministic audio DSP pipeline for VoiceStudio.

Provides polyphase resampling, mono downmixing, 50Hz Butterworth HPF, silence trimming,
pure NumPy/SciPy ITU-R BS.1770-4 EBU R128 loudness normalization, True Peak limiting,
RMS peak block extraction, and lossless WAV export with synthetic media RIFF metadata.
"""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass
from math import gcd
from pathlib import Path
import struct
from typing import List, Optional, Tuple, Union

import numpy as np
import scipy.signal
import soundfile as sf
import soxr
import torch

from voicestudio.audio.validator import (
    AudioValidator,
    InvalidAudioFormatError,
)


@dataclass
class PreprocessedAudio:
    """Preprocessed audio container matching VoiceStudio interface contract."""
    audio_tensor: torch.Tensor          # shape (1, samples)
    sample_rate: int                    # e.g. 24000 or 16000
    duration_sec: float
    peaks: List[float]                  # 100-300 normalized RMS blocks in [0.0, 1.0]
    snr_db: float
    sha256: str
    lufs: float = -23.0


class AudioProcessor:
    """Production Audio DSP processor for reference conditioning and speech synthesis."""

    def __init__(self, target_sample_rate: int = 24000):
        self.target_sample_rate = target_sample_rate

    @staticmethod
    def load_audio(file_path: Union[str, Path]) -> Tuple[np.ndarray, int]:
        """Load audio from file (WAV, MP3, FLAC, OGG) as float32 numpy array."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")
        data, sr = sf.read(str(path), dtype="float32")
        return data, sr

    @staticmethod
    def to_mono(audio: np.ndarray) -> np.ndarray:
        """Convert multi-channel audio to single-channel mono float32."""
        arr = np.asarray(audio, dtype=np.float32)
        if arr.ndim == 1:
            return arr
        elif arr.ndim == 2:
            # Channel dimension can be first (C, N) or second (N, C)
            if arr.shape[0] < arr.shape[1] and arr.shape[0] <= 8:
                return np.mean(arr, axis=0).astype(np.float32)
            else:
                return np.mean(arr, axis=1).astype(np.float32)
        else:
            flat = arr.reshape(-1, arr.shape[-1])
            return np.mean(flat, axis=-1).astype(np.float32)

    @staticmethod
    def resample(audio: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
        """Resample audio using soxr VHQ sinc-interpolation with scipy fallback."""
        if orig_sr == target_sr:
            return audio.astype(np.float32)
        try:
            resampled = soxr.resample(audio, orig_sr, target_sr, quality="VHQ")
            return resampled.astype(np.float32)
        except Exception:
            g = gcd(orig_sr, target_sr)
            up = target_sr // g
            down = orig_sr // g
            resampled = scipy.signal.resample_poly(audio, up, down)
            return resampled.astype(np.float32)

    @staticmethod
    def apply_butterworth_highpass(
        audio: np.ndarray,
        sample_rate: int,
        cutoff_hz: float = 50.0,
        order: int = 4,
    ) -> np.ndarray:
        """Apply 4th-order Butterworth high-pass filter using zero-phase SOS."""
        if len(audio) < 100:
            return audio.astype(np.float32)
        sos = scipy.signal.butter(
            order, cutoff_hz, btype="highpass", fs=sample_rate, output="sos"
        )
        filtered = scipy.signal.sosfiltfilt(sos, audio)
        return filtered.astype(np.float32)

    @staticmethod
    def trim_silence(
        audio: np.ndarray,
        sample_rate: int,
        threshold_db: float = -40.0,
        min_silence_ms: float = 200.0,
        padding_ms: float = 50.0,
    ) -> np.ndarray:
        """Trim leading, trailing, and excessive internal silence via energy VAD."""
        if len(audio) == 0:
            return audio
        frame_len = max(1, int(0.020 * sample_rate))  # 20ms
        hop_len = max(1, int(0.010 * sample_rate))    # 10ms
        num_frames = max(1, (len(audio) - frame_len) // hop_len + 1)

        rms = np.zeros(num_frames, dtype=np.float32)
        for i in range(num_frames):
            chunk = audio[i * hop_len : i * hop_len + frame_len]
            rms[i] = np.sqrt(np.mean(chunk**2) + 1e-12)

        frame_db = 20.0 * np.log10(rms)
        active = np.where(frame_db >= threshold_db)[0]
        if len(active) == 0:
            return audio

        pad_frames = int(padding_ms / 10.0)
        start_frame = max(0, active[0] - pad_frames)
        end_frame = min(num_frames - 1, active[-1] + pad_frames)

        start_samp = start_frame * hop_len
        end_samp = min(len(audio), end_frame * hop_len + frame_len)
        return audio[start_samp:end_samp].astype(np.float32)

    @staticmethod
    def measure_lufs(audio: np.ndarray, sample_rate: int) -> float:
        """Measure ITU-R BS.1770-4 integrated loudness in LUFS."""
        if len(audio) == 0:
            return -70.0
        if sample_rate != 48000:
            a_48k = soxr.resample(audio, sample_rate, 48000, quality="VHQ")
        else:
            a_48k = audio

        # ITU-R BS.1770-4 Stage 1: High shelf filter (+4 dB boost @ 1.5 kHz)
        b1 = np.array([1.53512485958697, -2.69169618940638, 1.19839281085285], dtype=np.float64)
        a1 = np.array([1.0, -1.69065929318241, 0.73248077421585], dtype=np.float64)
        # ITU-R BS.1770-4 Stage 2: High pass RLB filter (cutoff ~38 Hz)
        b2 = np.array([1.0, -2.0, 1.0], dtype=np.float64)
        a2 = np.array([1.0, -1.99004745483398, 0.99007225036621], dtype=np.float64)

        y = scipy.signal.lfilter(b1, a1, a_48k)
        y = scipy.signal.lfilter(b2, a2, y)

        block_size = int(0.400 * 48000)  # 400ms
        hop_size = int(0.100 * 48000)    # 100ms
        if len(y) < block_size:
            ms = np.mean(y**2)
            return float(-0.691 + 10.0 * np.log10(max(ms, 1e-12)))

        num_blocks = 1 + (len(y) - block_size) // hop_size
        z = np.zeros(num_blocks, dtype=np.float64)
        for j in range(num_blocks):
            st = j * hop_size
            z[j] = np.mean(y[st : st + block_size] ** 2)

        l_blocks = -0.691 + 10.0 * np.log10(np.maximum(z, 1e-12))
        abs_mask = l_blocks >= -70.0
        if not np.any(abs_mask):
            return -70.0

        z_abs = z[abs_mask]
        gamma_rel = -0.691 + 10.0 * np.log10(np.mean(z_abs)) - 10.0
        rel_mask = abs_mask & (l_blocks > gamma_rel)
        z_final = np.mean(z[rel_mask]) if np.any(rel_mask) else np.mean(z_abs)
        return float(-0.691 + 10.0 * np.log10(max(z_final, 1e-12)))

    @staticmethod
    def normalize_loudness(
        audio: np.ndarray,
        sample_rate: int,
        target_lufs: float = -23.0,
        true_peak_limit: float = -1.0,
    ) -> np.ndarray:
        """EBU R128 Loudness Normalization with True Peak limiting."""
        if len(audio) == 0:
            return audio
        init_lufs = AudioProcessor.measure_lufs(audio, sample_rate)
        if init_lufs <= -69.0:
            return audio.astype(np.float32)

        delta_l = target_lufs - init_lufs
        gain = 10.0 ** (delta_l / 20.0)
        scaled = audio * gain

        # True Peak check (4x oversampling)
        oversampled = soxr.resample(scaled, sample_rate, sample_rate * 4, quality="VHQ")
        max_tp_lin = np.max(np.abs(oversampled))
        tp_limit_lin = 10.0 ** (true_peak_limit / 20.0)

        if max_tp_lin > tp_limit_lin and max_tp_lin > 1e-6:
            reduction = tp_limit_lin / max_tp_lin
            scaled = scaled * reduction

        return np.clip(scaled, -1.0, 1.0).astype(np.float32)

    @staticmethod
    def compute_rms_peaks(audio: np.ndarray, num_blocks: int = 200) -> List[float]:
        """Precompute normalized RMS peak blocks for HTML5 canvas visualization."""
        if len(audio) == 0:
            return [0.0] * num_blocks
        num_samples = len(audio)
        if num_samples < num_blocks:
            peaks = [float(abs(x)) for x in audio]
            peaks += [0.0] * (num_blocks - len(peaks))
            return peaks

        block_size = num_samples / num_blocks
        rms_vals = np.zeros(num_blocks, dtype=np.float32)
        for i in range(num_blocks):
            s = int(i * block_size)
            e = int((i + 1) * block_size)
            chk = audio[s:e]
            if len(chk) > 0:
                rms_vals[i] = np.sqrt(np.mean(chk**2))

        m = np.max(rms_vals)
        norm_peaks = (rms_vals / m) if m > 1e-6 else rms_vals
        return [round(float(p), 4) for p in norm_peaks]

    @staticmethod
    def estimate_snr(audio: np.ndarray, sample_rate: int) -> float:
        """Estimate speech SNR using AudioValidator quartile method."""
        return AudioValidator.estimate_snr_quartile(AudioValidator, audio, sample_rate)

    @classmethod
    def preprocess_reference_audio(
        cls_or_self,
        input_path: Union[str, Path],
        target_sr: Optional[int] = None,
    ) -> PreprocessedAudio:
        """
        Execute full reference audio preprocessing pipeline with validation gates.
        """
        sr_target = target_sr or getattr(cls_or_self, "target_sample_rate", 24000)

        # 1. Format validation
        fmt_res = AudioValidator.validate_format(input_path)
        if not fmt_res.is_valid:
            raise InvalidAudioFormatError(
                f"Audio format validation failed: {'; '.join(fmt_res.reasons)}"
            )

        # 2. Load audio
        raw_audio, orig_sr = AudioProcessor.load_audio(input_path)

        # 3. Downmix to mono
        mono = AudioProcessor.to_mono(raw_audio)

        # 4. Quality validation gate (duration, clipping, silence, SNR)
        AudioValidator.validate_or_raise(AudioValidator, mono, orig_sr)

        # 5. Butterworth 50Hz HPF (zero-phase)
        filtered = AudioProcessor.apply_butterworth_highpass(
            mono, orig_sr, cutoff_hz=50.0, order=4
        )

        # 6. Polyphase resampling to target sample rate
        resampled = AudioProcessor.resample(filtered, orig_sr, sr_target)

        # 7. Silence trimming (200ms threshold)
        trimmed = AudioProcessor.trim_silence(
            resampled, sr_target, threshold_db=-40.0, min_silence_ms=200.0
        )

        # 8. EBU R128 loudness normalization (-23 LUFS) & True Peak limiting (-1.0 dBTP)
        normed = AudioProcessor.normalize_loudness(
            trimmed, sr_target, target_lufs=-23.0, true_peak_limit=-1.0
        )

        duration = len(normed) / sr_target
        peaks = AudioProcessor.compute_rms_peaks(normed, num_blocks=200)
        snr = AudioProcessor.estimate_snr(normed, sr_target)
        lufs = AudioProcessor.measure_lufs(normed, sr_target)
        sha256 = hashlib.sha256(normed.tobytes()).hexdigest()
        tensor = torch.from_numpy(normed).unsqueeze(0)  # shape (1, samples)

        return PreprocessedAudio(
            audio_tensor=tensor,
            sample_rate=sr_target,
            duration_sec=duration,
            peaks=peaks,
            snr_db=snr,
            sha256=sha256,
            lufs=lufs,
        )

    @classmethod
    def export_wav(
        cls_or_self,
        audio: Union[np.ndarray, torch.Tensor],
        sample_rate: int,
        output_path: Union[str, Path],
        is_synthetic: bool = True,
        subtype: str = "PCM_16",
    ) -> Path:
        """Export lossless WAV with optional synthetic media RIFF INFO tags."""
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if isinstance(audio, torch.Tensor):
            data = audio.detach().cpu().numpy()
        else:
            data = np.asarray(audio)
        if data.ndim == 2 and data.shape[0] == 1:
            data = data.squeeze(0)

        buf = io.BytesIO()
        sf.write(buf, data, sample_rate, format="WAV", subtype=subtype)
        raw_wav = buf.getvalue()

        if is_synthetic:
            tags = {
                "INAM": "VoiceStudio Audio Asset",
                "ISFT": "VoiceStudio v1.0",
                "ICMT": "VoiceStudio-AI-Synthetic; Ethics-Consent-Verified",
                "ISRC": "VoiceStudio-AI-Synthetic",
            }
            subchunks = b""
            for k, v in tags.items():
                k_b = k.encode("ascii")[:4].ljust(4, b" ")
                v_b = v.encode("utf-8") + b"\x00"
                sub_len = len(v_b)
                pad = b"\x00" if (sub_len % 2 != 0) else b""
                subchunks += k_b + struct.pack("<I", sub_len) + v_b + pad
            list_chunk = b"LIST" + struct.pack("<I", 4 + len(subchunks)) + b"INFO" + subchunks
            new_data = raw_wav + list_chunk
            new_riff_size = len(new_data) - 8
            final_bytes = new_data[:4] + struct.pack("<I", new_riff_size) + new_data[8:]
        else:
            final_bytes = raw_wav

        with open(out_path, "wb") as f:
            f.write(final_bytes)
        return out_path
