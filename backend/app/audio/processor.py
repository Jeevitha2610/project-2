import os
import math
import re
from pathlib import Path
from typing import Tuple, List, Dict, Any, Optional
import numpy as np
import soundfile as sf
import librosa
import noisereduce as nr

_whisper_model = None

_reference_processing_state = {
    "stage": "idle",
    "percent": 0,
    "message": ""
}

def update_processing_state(stage: str, percent: int, message: str):
    global _reference_processing_state
    _reference_processing_state = {
        "stage": stage,
        "percent": percent,
        "message": message
    }

def get_processing_state() -> dict:
    global _reference_processing_state
    return dict(_reference_processing_state)

def get_whisper_model():
    """Lazy loader for faster-whisper int8 model."""
    global _whisper_model
    if _whisper_model is None:
        from faster_whisper import WhisperModel
        # Use base int8 for fast CPU transcription
        _whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
    return _whisper_model


class AudioProcessor:
    @staticmethod
    def inspect_audio(file_path: str | Path) -> Dict[str, Any]:
        """Reads audio file info and returns metadata."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        try:
            info = sf.info(str(path))
            data, sr = sf.read(str(path))
            detected_format = info.format.lower()
            detected_subtype = info.subtype
        except Exception:
            data, sr = librosa.load(str(path), sr=None, mono=False)
            if data.ndim > 1:
                data = data.T  # soundfile shape convention (samples, channels)
            detected_format = path.suffix.lstrip(".").lower() or "wav"
            detected_subtype = "PCM_16"
        
        # Determine channels and peak amplitude
        if len(data.shape) > 1:
            channels = data.shape[1]
            peak = float(np.max(np.abs(data)))
            mono_data = np.mean(data, axis=1)
        else:
            channels = 1
            peak = float(np.max(np.abs(data))) if len(data) > 0 else 0.0
            mono_data = data
            
        duration = float(len(mono_data) / sr) if sr > 0 else 0.0
        clipping = bool(peak >= 0.999)
        
        # Estimate silence ratio (< -40dB relative to peak)
        threshold = max(peak * 0.01, 1e-4)
        silence_samples = np.sum(np.abs(mono_data) < threshold)
        silence_ratio = float(silence_samples / len(mono_data)) if len(mono_data) > 0 else 0.0
        
        # Estimate SNR (Signal to Noise Ratio)
        noise_floor = np.percentile(np.abs(mono_data), 10) + 1e-6 if len(mono_data) > 0 else 1e-6
        signal_level = np.percentile(np.abs(mono_data), 90) + 1e-6 if len(mono_data) > 0 else 1e-6
        snr_db = float(20 * np.log10(signal_level / noise_floor))

        return {
            "duration_seconds": round(duration, 2),
            "sample_rate": sr,
            "channels": channels,
            "format": detected_format,
            "subtype": detected_subtype,
            "peak_amplitude": round(peak, 3),
            "clipping_detected": clipping,
            "silence_ratio": round(silence_ratio, 3),
            "snr_estimate": round(snr_db, 1)
        }

    @staticmethod
    def denoise(data: np.ndarray, sr: int) -> np.ndarray:
        """Applies spectral gating noise reduction."""
        if len(data) == 0:
            return data
        try:
            return nr.reduce_noise(y=data, sr=sr, prop_decrease=0.85, stationary=True)
        except Exception:
            return data

    @staticmethod
    def normalize_loudness(data: np.ndarray, target_peak: float = 0.95) -> np.ndarray:
        """Normalizes audio peak amplitude to target peak level."""
        max_val = np.max(np.abs(data)) if len(data) > 0 else 0.0
        if max_val > 0:
            return (data / max_val) * target_peak
        return data

    @staticmethod
    def transcribe_audio(
        audio_data: np.ndarray,
        sr: int = 24000
    ) -> Dict[str, Any]:
        """Transcribes audio using faster-whisper (int8, CPU)."""
        if len(audio_data.shape) > 1:
            audio_data = np.mean(audio_data, axis=1)
        
        # Whisper requires 16000 Hz
        if sr != 16000:
            audio_16k = librosa.resample(audio_data, orig_sr=sr, target_sr=16000)
        else:
            audio_16k = audio_data

        whisper = get_whisper_model()
        segments, info = whisper.transcribe(
            audio_16k.astype(np.float32),
            language="en",
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=250)
        )
        
        seg_list = []
        full_text_parts = []
        for s in segments:
            seg_list.append({
                "start": round(s.start, 2),
                "end": round(s.end, 2),
                "text": s.text.strip()
            })
            if s.text.strip():
                full_text_parts.append(s.text.strip())
                
        transcript = " ".join(full_text_parts).strip()
        return {
            "transcript": transcript,
            "language": info.language,
            "language_probability": info.language_probability,
            "segments": seg_list
        }

    @staticmethod
    def process_reference_audio(
        input_path: str | Path,
        output_path: str | Path,
        target_sr: int = 24000,
        target_duration_range: Tuple[float, float] = (6.0, 10.0),
        trailing_silence_s: float = 0.15
    ) -> Dict[str, Any]:
        """Processes reference audio:
        1. Converts to mono at target_sr (24000 Hz).
        2. Denoises using noisereduce.
        3. Normalizes loudness.
        4. Transcribes with faster-whisper.
        5. Trims to clean sentence boundary (6-10s) with a short trailing silence.
        6. Caches processed audio and mel representation.
        """
        try:
            data, sr = sf.read(str(input_path))
        except Exception:
            data, sr = librosa.load(str(input_path), sr=None, mono=False)
            if data.ndim > 1:
                data = data.T
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)

        # Resample to 24000 Hz if needed
        if sr != target_sr:
            data = librosa.resample(data, orig_sr=sr, target_sr=target_sr)
            sr = target_sr

        # 1. Denoise & normalize
        update_processing_state("denoising", 40, "Denoising audio & normalizing loudness to -1dB peak...")
        data = AudioProcessor.denoise(data, sr)
        data = AudioProcessor.normalize_loudness(data, target_peak=0.95)

        # 2. Transcribe with Whisper to detect sentence boundaries
        update_processing_state("transcribing", 70, "Transcribing speech phonetics & sentence alignment with Whisper...")
        asr_result = AudioProcessor.transcribe_audio(data, sr)
        segments = asr_result["segments"]

        cut_time = None
        selected_text = ""

        if segments:
            # Look for sentence boundary within 6.0 to 10.0 seconds
            # A sentence end is marked by '.', '!', or '?'
            sentence_ends = []
            running_text = []
            for seg in segments:
                running_text.append(seg["text"])
                end_time = seg["end"]
                text = seg["text"].strip()
                is_sentence_end = bool(re.search(r'[.!?]$', text))
                sentence_ends.append((end_time, " ".join(running_text), is_sentence_end))

            min_d, max_d = target_duration_range
            
            # 1. Try to find a sentence end in [min_d, max_d]
            candidates = [s for s in sentence_ends if s[2] and min_d <= s[0] <= max_d + 1.0]
            if candidates:
                best = candidates[-1]  # Pick the largest complete sentence within range
                cut_time, selected_text, _ = best
            else:
                # 2. Try to find any sentence end closest to 6-10s
                complete_sentences = [s for s in sentence_ends if s[2]]
                if complete_sentences:
                    # Closest to target range
                    best = min(complete_sentences, key=lambda s: abs(s[0] - 8.0))
                    cut_time, selected_text, _ = best
                else:
                    # 3. Fallback to last segment end
                    last_seg = segments[-1]
                    cut_time = min(float(last_seg["end"]), max_d)
                    selected_text = asr_result["transcript"]

        if cut_time is None or cut_time <= 0:
            total_duration = len(data) / sr
            cut_time = min(total_duration, target_duration_range[1])
            selected_text = asr_result["transcript"]

        # Trim audio to cut_time
        cut_samples = min(len(data), int(round(cut_time * sr)))
        trimmed_data = data[:cut_samples]

        # Add short trailing silence
        silence_samples = int(round(trailing_silence_s * sr))
        if silence_samples > 0:
            silence = np.zeros(silence_samples, dtype=trimmed_data.dtype)
            trimmed_data = np.concatenate([trimmed_data, silence])

        # Final peak normalization
        trimmed_data = AudioProcessor.normalize_loudness(trimmed_data, target_peak=0.95)

        # Save processed reference
        output_p = Path(output_path)
        output_p.parent.mkdir(parents=True, exist_ok=True)
        sf.write(str(output_p), trimmed_data.astype(np.float32), sr, subtype="PCM_16")

        # Cache in ReferenceCache
        try:
            from ml.reference_cache import reference_cache
            reference_cache.set(
                audio_path=output_path,
                cleaned_path=output_path,
                transcript=selected_text,
            )
        except Exception:
            pass

        info = AudioProcessor.inspect_audio(output_p)
        info["transcript"] = selected_text
        info["output_path"] = str(output_p)
        update_processing_state("ready", 100, "Ready! Voice profile successfully created.")
        return info

    @staticmethod
    def convert_and_normalize(
        input_path: str | Path,
        output_path: str | Path,
        target_sr: int = 24000,
        target_channels: int = 1,
        normalize_peak: float = 0.95
    ) -> Dict[str, Any]:
        """Loads audio, converts to mono/target sample rate, normalizes, and saves as WAV."""
        try:
            data, sr = sf.read(str(input_path))
        except Exception:
            data, sr = librosa.load(str(input_path), sr=None, mono=False)
            if data.ndim > 1:
                data = data.T
        
        # Convert to mono if needed
        if len(data.shape) > 1 and target_channels == 1:
            data = np.mean(data, axis=1)
            
        if sr != target_sr:
            data = librosa.resample(data, orig_sr=sr, target_sr=target_sr)
            sr = target_sr
            
        max_val = np.max(np.abs(data)) if len(data) > 0 else 0.0
        if max_val > 0:
            data = (data / max_val) * normalize_peak
            
        sf.write(str(output_path), data.astype(np.float32), target_sr, subtype="PCM_16")
        return AudioProcessor.inspect_audio(output_path)

    @staticmethod
    def extract_waveform_peaks(file_path: str | Path, num_peaks: int = 100) -> List[float]:
        """Generates normalized waveform peak array for quick UI rendering."""
        data, _ = sf.read(str(file_path))
        if len(data.shape) > 1:
            data = np.mean(data, axis=1)
        
        if len(data) == 0:
            return [0.0] * num_peaks
            
        chunk_size = max(1, len(data) // num_peaks)
        peaks = []
        for i in range(num_peaks):
            start = i * chunk_size
            end = min(len(data), start + chunk_size)
            chunk = data[start:end]
            val = float(np.max(np.abs(chunk))) if len(chunk) > 0 else 0.0
            peaks.append(round(min(1.0, val), 3))
        return peaks
