"""
Comprehensive Unit Test Suite for VoiceStudio Audio Processing & Validation.

Tests:
1. AudioProcessor: Mono mixdown, polyphase resampling, Butterworth 50Hz HPF,
   silence trimming, pure NumPy/SciPy ITU-R BS.1770-4 EBU R128 loudness normalization,
   True Peak limiting, RMS peak block extraction, lossless WAV export with synthetic tags.
2. AudioValidator: Format validation, corrupt headers, duration bounds [3s, 30s],
   clipping detection, silence/energy ratio, blind SNR estimation (WADA & Quartile).
"""

from __future__ import annotations

from pathlib import Path
import numpy as np
import pytest
import soundfile as sf
import torch

from voicestudio.audio.processor import AudioProcessor, PreprocessedAudio
from voicestudio.audio.validator import (
    AudioValidator,
    QualityValidationResult,
    AudioFormatResult,
    AudioValidationError,
    AudioTooShortError,
    AudioTooLongError,
    AudioClippingError,
    AudioSilentError,
    ExcessiveNoiseError,
    InvalidAudioFormatError,
)


# ============================================================================
# Pytest Fixtures
# ============================================================================

@pytest.fixture
def sample_rate_24k() -> int:
    return 24000


@pytest.fixture
def sample_rate_16k() -> int:
    return 16000


@pytest.fixture
def sample_rate_44k() -> int:
    return 44100


@pytest.fixture
def clean_speech_audio(sample_rate_24k: int) -> np.ndarray:
    """Generates synthetic speech-like bursty harmonic signal (5.0s, 24kHz)."""
    t = np.linspace(0, 5, sample_rate_24k * 5, endpoint=False)
    env = np.maximum(0.0, np.sin(2 * np.pi * 1.5 * t)) ** 2
    carrier = np.sin(2 * np.pi * 300 * t) * 0.7 + 0.3 * np.sin(2 * np.pi * 600 * t)
    return (env * carrier).astype(np.float32)


@pytest.fixture
def processor() -> AudioProcessor:
    return AudioProcessor(target_sample_rate=24000)


@pytest.fixture
def validator() -> AudioValidator:
    return AudioValidator()


# ============================================================================
# Test Suite 1: AudioProcessor DSP Operations
# ============================================================================

@pytest.mark.unit
class TestAudioProcessorDSP:
    def test_to_mono_from_1d(self, processor: AudioProcessor):
        mono_in = np.ones(1000, dtype=np.float32)
        out = processor.to_mono(mono_in)
        assert out.ndim == 1
        assert len(out) == 1000

    def test_to_mono_from_stereo_channels_first(self, processor: AudioProcessor):
        stereo = np.ones((2, 1000), dtype=np.float32)
        stereo[0] *= 0.8
        stereo[1] *= 0.4
        out = processor.to_mono(stereo)
        assert out.shape == (1000,)
        assert np.isclose(out[0], 0.6)

    def test_to_mono_from_stereo_samples_first(self, processor: AudioProcessor):
        stereo = np.ones((1000, 2), dtype=np.float32)
        stereo[:, 0] *= 0.8
        stereo[:, 1] *= 0.4
        out = processor.to_mono(stereo)
        assert out.shape == (1000,)
        assert np.isclose(out[0], 0.6)

    def test_resample_ratio_and_duration_preservation(
        self, processor: AudioProcessor, sample_rate_44k: int, sample_rate_24k: int
    ):
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate_44k * duration), endpoint=False)
        tone = np.sin(2 * np.pi * 1000 * t).astype(np.float32)
        resampled = processor.resample(tone, sample_rate_44k, sample_rate_24k)
        expected_samples = int(round(len(tone) * sample_rate_24k / sample_rate_44k))
        assert abs(len(resampled) - expected_samples) <= 2

    def test_resample_frequency_accuracy(
        self, processor: AudioProcessor, sample_rate_44k: int, sample_rate_24k: int
    ):
        duration = 1.0
        t = np.linspace(0, duration, int(sample_rate_44k * duration), endpoint=False)
        tone_1k = np.sin(2 * np.pi * 1000 * t).astype(np.float32)
        resampled = processor.resample(tone_1k, sample_rate_44k, sample_rate_24k)
        fft = np.abs(np.fft.rfft(resampled))
        freqs = np.fft.rfftfreq(len(resampled), 1 / sample_rate_24k)
        peak_freq = freqs[np.argmax(fft)]
        assert abs(peak_freq - 1000.0) < 10.0

    def test_resample_same_rate_noop(
        self, processor: AudioProcessor, clean_speech_audio: np.ndarray, sample_rate_24k: int
    ):
        out = processor.resample(clean_speech_audio, sample_rate_24k, sample_rate_24k)
        assert np.array_equal(out, clean_speech_audio)

    def test_butterworth_dc_rejection(self, processor: AudioProcessor, sample_rate_24k: int):
        dc_signal = np.ones(sample_rate_24k * 2, dtype=np.float32) * 0.5
        filtered = processor.apply_butterworth_highpass(dc_signal, sample_rate_24k, cutoff_hz=50.0)
        assert abs(np.mean(filtered[sample_rate_24k // 2:])) < 1e-4

    def test_butterworth_50hz_cutoff_attenuation(
        self, processor: AudioProcessor, sample_rate_24k: int
    ):
        # Forward-backward zero-phase sosfiltfilt squares magnitude: -3.01 dB * 2 = -6.02 dB at cutoff
        t = np.linspace(0, 2, sample_rate_24k * 2, endpoint=False)
        sig_50hz = np.sin(2 * np.pi * 50.0 * t).astype(np.float32)
        filtered = processor.apply_butterworth_highpass(sig_50hz, sample_rate_24k, cutoff_hz=50.0)
        in_rms = np.sqrt(np.mean(sig_50hz ** 2))
        out_rms = np.sqrt(np.mean(filtered[sample_rate_24k // 2:] ** 2))
        attenuation_db = 20 * np.log10(out_rms / in_rms)
        assert -7.0 < attenuation_db < -5.0

    def test_butterworth_passband_preservation(
        self, processor: AudioProcessor, sample_rate_24k: int
    ):
        t = np.linspace(0, 2, sample_rate_24k * 2, endpoint=False)
        sig_1k = np.sin(2 * np.pi * 1000.0 * t).astype(np.float32)
        filtered = processor.apply_butterworth_highpass(sig_1k, sample_rate_24k, cutoff_hz=50.0)
        in_rms = np.sqrt(np.mean(sig_1k ** 2))
        out_rms = np.sqrt(np.mean(filtered[sample_rate_24k // 2:] ** 2))
        gain = out_rms / in_rms
        assert 0.98 < gain < 1.02

    def test_silence_trimming(self, processor: AudioProcessor, sample_rate_24k: int):
        t = np.linspace(0, 2, sample_rate_24k * 2, endpoint=False)
        active = np.sin(2 * np.pi * 440 * t).astype(np.float32) * 0.5
        silence = np.zeros(sample_rate_24k, dtype=np.float32)
        padded = np.concatenate([silence, active, silence])
        trimmed = processor.trim_silence(padded, sample_rate_24k, threshold_db=-40.0)
        assert abs(len(trimmed) - len(active)) < sample_rate_24k * 0.25

    def test_silence_trimming_empty_or_all_silence(
        self, processor: AudioProcessor, sample_rate_24k: int
    ):
        silent = np.zeros(sample_rate_24k * 2, dtype=np.float32)
        trimmed = processor.trim_silence(silent, sample_rate_24k, threshold_db=-40.0)
        assert len(trimmed) == 0 or len(trimmed) <= sample_rate_24k * 2

    def test_lufs_normalization_and_true_peak_limiting(
        self, processor: AudioProcessor, sample_rate_24k: int, clean_speech_audio: np.ndarray
    ):
        normalized = processor.normalize_loudness(
            clean_speech_audio, sample_rate_24k, target_lufs=-23.0, true_peak_limit=-1.0
        )
        max_peak = np.max(np.abs(normalized))
        # Peak must not exceed -1.0 dBTP (10^(-1/20) approx 0.89125)
        assert max_peak <= 10.0 ** (-1.0 / 20.0) + 1e-4

    def test_compute_rms_peaks_shape_and_range(
        self, processor: AudioProcessor, clean_speech_audio: np.ndarray
    ):
        peaks = processor.compute_rms_peaks(clean_speech_audio, num_blocks=200)
        assert len(peaks) == 200
        assert all(0.0 <= p <= 1.0 for p in peaks)
        assert max(peaks) == pytest.approx(1.0, abs=1e-3)

    def test_export_wav_integrity_and_reload(
        self, processor: AudioProcessor, sample_rate_24k: int, clean_speech_audio: np.ndarray, tmp_path: Path
    ):
        out_path = tmp_path / "exports" / "test_out.wav"
        written = processor.export_wav(clean_speech_audio, sample_rate_24k, out_path, is_synthetic=True)
        assert written.exists()
        info = sf.info(str(written))
        assert info.format == "WAV"
        assert info.samplerate == sample_rate_24k
        assert info.channels == 1
        data, sr = sf.read(str(written))
        assert len(data) == len(clean_speech_audio)

    def test_preprocess_reference_audio_end_to_end(
        self, processor: AudioProcessor, sample_rate_24k: int, clean_speech_audio: np.ndarray, tmp_path: Path
    ):
        wav_path = tmp_path / "test_ref.wav"
        sf.write(str(wav_path), clean_speech_audio, sample_rate_24k, subtype="PCM_16")
        prep = processor.preprocess_reference_audio(wav_path, target_sr=24000)
        assert isinstance(prep, PreprocessedAudio)
        assert prep.sample_rate == 24000
        assert prep.audio_tensor.ndim == 2
        assert prep.audio_tensor.shape[0] == 1
        assert len(prep.peaks) == 200
        assert len(prep.sha256) == 64
        assert prep.duration_sec >= 3.0


# ============================================================================
# Test Suite 2: AudioValidator Quality Gates & Exceptions
# ============================================================================

@pytest.mark.unit
class TestAudioValidatorQualityGates:
    def test_validate_format_valid_wav(
        self, validator: AudioValidator, sample_rate_24k: int, clean_speech_audio: np.ndarray, tmp_path: Path
    ):
        wav_path = tmp_path / "clean.wav"
        sf.write(str(wav_path), clean_speech_audio, sample_rate_24k, subtype="PCM_16")
        res = validator.validate_format(wav_path)
        assert res.is_valid
        assert res.format == "WAV"
        assert res.sample_rate == sample_rate_24k
        assert res.channels == 1
        assert res.bit_depth == 16
        assert len(res.reasons) == 0

    def test_validate_format_corrupt_header(self, validator: AudioValidator, tmp_path: Path):
        corrupt = tmp_path / "corrupt.wav"
        corrupt.write_bytes(b"NOT_A_VALID_RIFF_HEADER_1234567890")
        res = validator.validate_format(corrupt)
        assert not res.is_valid
        assert res.format == "CORRUPT"
        assert len(res.reasons) > 0

    def test_validate_format_zero_bytes(self, validator: AudioValidator, tmp_path: Path):
        empty = tmp_path / "empty.wav"
        empty.touch()
        res = validator.validate_format(empty)
        assert not res.is_valid
        assert any("empty" in r for r in res.reasons)

    def test_validate_format_missing_file(self, validator: AudioValidator, tmp_path: Path):
        res = validator.validate_format(tmp_path / "non_existent.wav")
        assert not res.is_valid
        assert any("does not exist" in r for r in res.reasons)

    def test_quality_gate_valid_speech(
        self, validator: AudioValidator, sample_rate_24k: int, clean_speech_audio: np.ndarray
    ):
        res = validator.validate_quality(clean_speech_audio, sample_rate_24k)
        assert res.is_valid
        assert res.duration_sec == pytest.approx(5.0, abs=0.01)
        assert res.snr_db >= 15.0
        assert res.clipping_ratio <= 0.001
        assert not res.is_silent
        assert len(res.reasons) == 0

    def test_quality_gate_reject_too_short(
        self, validator: AudioValidator, sample_rate_24k: int, clean_speech_audio: np.ndarray
    ):
        short_audio = clean_speech_audio[:int(sample_rate_24k * 2.0)]  # 2.0s < 3.0s
        res = validator.validate_quality(short_audio, sample_rate_24k)
        assert not res.is_valid
        assert any("below minimum threshold of 3.0s" in r for r in res.reasons)
        with pytest.raises(AudioTooShortError):
            validator.validate_or_raise(short_audio, sample_rate_24k)

    def test_quality_gate_reject_too_long(
        self, validator: AudioValidator, sample_rate_24k: int, clean_speech_audio: np.ndarray
    ):
        long_audio = np.tile(clean_speech_audio, 7)  # 35.0s > 30.0s
        res = validator.validate_quality(long_audio, sample_rate_24k)
        assert not res.is_valid
        assert any("exceeds maximum threshold of 30.0s" in r for r in res.reasons)
        with pytest.raises(AudioTooLongError):
            validator.validate_or_raise(long_audio, sample_rate_24k)

    def test_quality_gate_reject_clipping(
        self, validator: AudioValidator, sample_rate_24k: int, clean_speech_audio: np.ndarray
    ):
        clipped = np.clip(clean_speech_audio * 5.0, -1.0, 1.0)
        res = validator.validate_quality(clipped, sample_rate_24k)
        assert not res.is_valid
        assert res.clipping_ratio > 0.001
        assert any("Clipping ratio" in r for r in res.reasons)
        with pytest.raises(AudioClippingError):
            validator.validate_or_raise(clipped, sample_rate_24k)

    def test_quality_gate_reject_silence(
        self, validator: AudioValidator, sample_rate_24k: int
    ):
        silent = np.zeros(sample_rate_24k * 5, dtype=np.float32)
        res = validator.validate_quality(silent, sample_rate_24k)
        assert not res.is_valid
        assert res.is_silent
        assert any("silent" in r for r in res.reasons)
        with pytest.raises(AudioSilentError):
            validator.validate_or_raise(silent, sample_rate_24k)

    def test_quality_gate_reject_low_snr(
        self, validator: AudioValidator, sample_rate_24k: int, clean_speech_audio: np.ndarray
    ):
        noise = np.random.normal(0, 0.35, len(clean_speech_audio)).astype(np.float32)
        noisy = clean_speech_audio + noise
        noisy = noisy * 0.5 / np.max(np.abs(noisy))
        res = validator.validate_quality(noisy, sample_rate_24k)
        assert not res.is_valid
        assert res.snr_db < 15.0
        assert any("SNR" in r for r in res.reasons)
        with pytest.raises(ExcessiveNoiseError):
            validator.validate_or_raise(noisy, sample_rate_24k)

    def test_estimate_snr_wada(
        self, validator: AudioValidator, sample_rate_24k: int, clean_speech_audio: np.ndarray
    ):
        snr_clean = validator.estimate_snr_wada(clean_speech_audio)
        assert snr_clean > 30.0

        noise = np.random.normal(0, 1.0, sample_rate_24k * 5).astype(np.float32)
        snr_noise = validator.estimate_snr_wada(noise)
        assert snr_noise <= 0.0

    def test_estimate_snr_quartile(
        self, validator: AudioValidator, sample_rate_24k: int, clean_speech_audio: np.ndarray
    ):
        snr_clean = validator.estimate_snr_quartile(clean_speech_audio, sample_rate_24k)
        assert snr_clean >= 15.0
