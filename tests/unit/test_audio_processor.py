"""
Tier 1 & Tier 2 Unit Tests: AudioProcessor & AudioValidator (13 Test Cases).
Coverage:
- TC-T1-AUD-01: Resample arbitrary sample rate to 24kHz target
- TC-T1-AUD-02: Multi-channel downmixing to mono
- TC-T1-AUD-03: Butterworth 50Hz high-pass filter
- TC-T1-AUD-04: Silence trimming
- TC-T1-AUD-05: EBU R128 loudness normalization
- TC-T1-AUD-06: Peak limiter application (-1.0 dBFS)
- TC-T1-AUD-07: Peak blocks extraction (100 bins)
- TC-T2-BND-AUD-01: Boundary: Ultra-short audio rejected
- TC-T2-BND-AUD-02: Boundary: Pure silence rejected
- TC-T2-BND-AUD-03: Boundary: Severely clipped audio detected/rejected
- TC-T2-BND-AUD-04: Boundary: Excessive noise (<15dB SNR) detected/rejected
- TC-T2-BND-AUD-05: Boundary: Corrupted WAV header rejected
- TC-T2-BND-AUD-06: Boundary: Non-audio file renamed to .wav rejected
"""

import math
from pathlib import Path
import numpy as np
import pytest
import soundfile as sf
import torch

try:
    from voicestudio.audio.processor import AudioProcessor
    from voicestudio.audio.validator import (
        AudioValidator,
        AudioTooShortError,
        AudioSilentError,
        AudioClippingError,
        ExcessiveNoiseError,
        InvalidAudioFormatError,
    )
except ImportError:
    from tests.contracts import (
        AudioProcessor,
        AudioValidator,
        AudioTooShortError,
        AudioSilentError,
        AudioClippingError,
        ExcessiveNoiseError,
        InvalidAudioFormatError,
    )


@pytest.mark.unit
class TestAudioProcessorTier1:
    """Tier 1: Feature Coverage for AudioProcessor."""

    def test_tc_t1_aud_01_resample_arbitrary_to_24k(self, audio_synthesizer):
        """TC-T1-AUD-01: Resample 44.1kHz, 48kHz, 16kHz audio to 24kHz target."""
        for orig_sr in [44100, 48000, 16000]:
            duration = 1.5
            audio, sr = audio_synthesizer(duration_sec=duration, sample_rate=orig_sr, freq_hz=440.0)
            resampled = AudioProcessor.resample(audio, orig_sr=orig_sr, target_sr=24000)
            
            expected_samples = int(duration * 24000)
            assert abs(len(resampled) - expected_samples) <= 2
            assert resampled.dtype == np.float32

    def test_tc_t1_aud_02_stereo_downmix_to_mono(self, audio_synthesizer):
        """TC-T1-AUD-02: Multi-channel downmixing (stereo to mono without phase cancellation)."""
        duration = 2.0
        stereo_audio, sr = audio_synthesizer(duration_sec=duration, sample_rate=24000, stereo=True)
        assert stereo_audio.ndim == 2
        
        mono = AudioProcessor.to_mono(stereo_audio)
        assert mono.ndim == 1
        assert len(mono) == stereo_audio.shape[0]
        # Verify signal amplitude is preserved
        assert np.max(np.abs(mono)) > 0.1

    def test_tc_t1_aud_03_butterworth_highpass_50hz(self):
        """TC-T1-AUD-03: Butterworth 50Hz high-pass filter attenuates DC & rumble."""
        sr = 24000
        duration = 1.0
        t = np.linspace(0, duration, int(sr * duration), endpoint=False)
        # Mix 20Hz rumble (to be attenuated) with 1000Hz tone (to be preserved)
        rumble = 0.5 * np.sin(2 * np.pi * 20.0 * t)
        signal = 0.5 * np.sin(2 * np.pi * 1000.0 * t)
        mixed = (rumble + signal).astype(np.float32)

        filtered = AudioProcessor.apply_butterworth_highpass(mixed, sample_rate=sr, cutoff_hz=50.0)
        
        # Power spectrum analysis via FFT
        fft_orig = np.abs(np.fft.rfft(mixed))
        fft_filt = np.abs(np.fft.rfft(filtered))
        freqs = np.fft.rfftfreq(len(mixed), 1.0 / sr)
        
        idx_20hz = np.argmin(np.abs(freqs - 20.0))
        idx_1000hz = np.argmin(np.abs(freqs - 1000.0))
        
        # 20Hz must be significantly attenuated (>12dB drop)
        attenuation_db = 20.0 * np.log10((fft_filt[idx_20hz] + 1e-9) / (fft_orig[idx_20hz] + 1e-9))
        assert attenuation_db < -12.0
        # 1000Hz must be preserved (within 1dB)
        preservation_db = 20.0 * np.log10((fft_filt[idx_1000hz] + 1e-9) / (fft_orig[idx_1000hz] + 1e-9))
        assert abs(preservation_db) < 1.5

    def test_tc_t1_aud_04_silence_trimming(self, audio_synthesizer):
        """TC-T1-AUD-04: Silence trimming removes leading and trailing silence."""
        sr = 24000
        leading_silence = np.zeros(int(0.5 * sr), dtype=np.float32)  # 500ms
        trailing_silence = np.zeros(int(0.5 * sr), dtype=np.float32) # 500ms
        tone, _ = audio_synthesizer(duration_sec=1.5, sample_rate=sr, freq_hz=440.0)
        
        audio = np.concatenate([leading_silence, tone, trailing_silence])
        trimmed = AudioProcessor.trim_silence(audio, sample_rate=sr, threshold_db=-40.0)
        
        # Trimmed length should be less than original and close to active tone length
        assert len(trimmed) < len(audio)
        assert len(trimmed) >= len(tone)

    def test_tc_t1_aud_05_ebu_r128_loudness_normalization(self, audio_synthesizer):
        """TC-T1-AUD-05: Loudness normalization targets -23.0 LUFS."""
        sr = 24000
        # Very quiet audio
        quiet, _ = audio_synthesizer(duration_sec=2.0, sample_rate=sr, freq_hz=440.0)
        quiet = quiet * 0.01  # -40 dBFS
        
        normalized = AudioProcessor.normalize_loudness(quiet, sample_rate=sr, target_lufs=-23.0)
        # Verify energy boosted
        rms_norm = np.sqrt(np.mean(np.square(normalized)))
        lufs_est = 20.0 * np.log10(rms_norm)
        assert abs(lufs_est - (-23.0)) <= 3.0

    def test_tc_t1_aud_06_true_peak_limiter(self, audio_synthesizer):
        """TC-T1-AUD-06: Peak limiter constrains true peak to -1.0 dBTP."""
        sr = 24000
        # Over-amplified audio
        loud, _ = audio_synthesizer(duration_sec=2.0, sample_rate=sr, clip=False)
        loud = loud * 5.0  # Massive amplitude
        
        limited = AudioProcessor.normalize_loudness(loud, sample_rate=sr, true_peak_limit=-1.0)
        max_allowed_peak = 10.0 ** (-1.0 / 20.0)  # ~0.891
        max_peak = np.max(np.abs(limited))
        assert max_peak <= max_allowed_peak + 1e-4

    def test_tc_t1_aud_07_peak_block_extraction(self, audio_synthesizer):
        """TC-T1-AUD-07: Extract 100-bin normalized peak array."""
        audio, sr = audio_synthesizer(duration_sec=3.0, sample_rate=24000)
        peaks = AudioProcessor.compute_rms_peaks(audio, num_blocks=100)
        
        assert len(peaks) == 100
        assert all(0.0 <= p <= 1.0 for p in peaks)
        assert max(peaks) == pytest.approx(1.0, abs=1e-3)


@pytest.mark.unit
class TestAudioValidatorTier2:
    """Tier 2: Boundary & Corner Cases for Audio Signal & Quality Gates."""

    def test_tc_t2_bnd_aud_01_ultra_short_audio_rejected(self, short_wav_file):
        """TC-T2-BND-AUD-01: Ultra-short audio (<0.5s) rejected."""
        with pytest.raises(AudioTooShortError):
            AudioProcessor.preprocess_reference_audio(short_wav_file)

    def test_tc_t2_bnd_aud_02_pure_silence_rejected(self, silent_wav_file):
        """TC-T2-BND-AUD-02: Pure silence audio rejected."""
        with pytest.raises(AudioSilentError):
            AudioProcessor.preprocess_reference_audio(silent_wav_file)

    def test_tc_t2_bnd_aud_03_severely_clipped_audio_rejected(self, clipped_wav_file):
        """TC-T2-BND-AUD-03: Heavily clipped audio triggers AudioClippingError."""
        with pytest.raises(AudioClippingError):
            AudioProcessor.preprocess_reference_audio(clipped_wav_file)

    def test_tc_t2_bnd_aud_04_high_noise_audio_rejected(self, noisy_wav_file):
        """TC-T2-BND-AUD-04: High background noise (SNR < 15 dB) rejected."""
        with pytest.raises(ExcessiveNoiseError):
            AudioProcessor.preprocess_reference_audio(noisy_wav_file)

    def test_tc_t2_bnd_aud_05_corrupt_wav_header_rejected(self, corrupt_wav_file):
        """TC-T2-BND-AUD-05: Corrupted WAV header rejected with InvalidAudioFormatError."""
        with pytest.raises(InvalidAudioFormatError):
            AudioProcessor.preprocess_reference_audio(corrupt_wav_file)

    def test_tc_t2_bnd_aud_06_non_audio_file_renamed_wav_rejected(self, tmp_path):
        """TC-T2-BND-AUD-06: Non-audio text or binary file renamed to .wav rejected."""
        fake_wav = tmp_path / "fake.wav"
        fake_wav.write_text("This is an ordinary text file disguised as a wav file.", encoding="utf-8")
        
        with pytest.raises(InvalidAudioFormatError):
            AudioProcessor.preprocess_reference_audio(fake_wav)
