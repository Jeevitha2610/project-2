import os
import math
from pathlib import Path
from typing import Tuple, List, Dict, Any
import numpy as np
import soundfile as sf

class AudioProcessor:
    @staticmethod
    def inspect_audio(file_path: str | Path) -> Dict[str, Any]:
        """Reads audio file info and returns metadata."""
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        info = sf.info(str(path))
        data, sr = sf.read(str(path))
        
        # Determine channels and peak amplitude
        if len(data.shape) > 1:
            channels = data.shape[1]
            peak = float(np.max(np.abs(data)))
            mono_data = np.mean(data, axis=1)
        else:
            channels = 1
            peak = float(np.max(np.abs(data)))
            mono_data = data
            
        duration = float(len(mono_data) / sr)
        clipping = bool(peak >= 0.999)
        
        # Estimate silence ratio (< -40dB relative to peak)
        threshold = max(peak * 0.01, 1e-4)
        silence_samples = np.sum(np.abs(mono_data) < threshold)
        silence_ratio = float(silence_samples / len(mono_data)) if len(mono_data) > 0 else 0.0
        
        # Estimate SNR (Signal to Noise Ratio)
        noise_floor = np.percentile(np.abs(mono_data), 10) + 1e-6
        signal_level = np.percentile(np.abs(mono_data), 90) + 1e-6
        snr_db = float(20 * np.log10(signal_level / noise_floor))

        return {
            "duration_seconds": round(duration, 2),
            "sample_rate": sr,
            "channels": channels,
            "format": info.format.lower(),
            "subtype": info.subtype,
            "peak_amplitude": round(peak, 3),
            "clipping_detected": clipping,
            "silence_ratio": round(silence_ratio, 3),
            "snr_estimate": round(snr_db, 1)
        }

    @staticmethod
    def convert_and_normalize(
        input_path: str | Path,
        output_path: str | Path,
        target_sr: int = 24000,
        target_channels: int = 1,
        normalize_peak: float = 0.95
    ) -> Dict[str, Any]:
        """Loads audio, converts to mono/target sample rate, normalizes, and saves as WAV."""
        data, sr = sf.read(str(input_path))
        
        # Convert to mono if needed
        if len(data.shape) > 1 and target_channels == 1:
            data = np.mean(data, axis=1)
            
        # Simple linear or scipy resample if sr != target_sr
        if sr != target_sr:
            from scipy import signal
            num_samples = int(round(len(data) * float(target_sr) / sr))
            data = signal.resample(data, num_samples)
            sr = target_sr
            
        # Peak normalize
        max_val = np.max(np.abs(data))
        if max_val > 0:
            data = (data / max_val) * normalize_peak
            
        # Write output WAV
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
            if len(chunk) > 0:
                peaks.append(round(float(np.max(np.abs(chunk))), 3))
            else:
                peaks.append(0.0)
        return peaks
