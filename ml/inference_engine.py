"""Real neural zero-shot English voice cloning on CPU using F5-TTS.

Replaces the earlier DSP sine-wave placeholder (which produced an electronic
buzz rather than speech). The engine:

* loads the official F5-TTS v1 Base model + Vocos vocoder once (lazy, thread-safe),
* conditions generation on the reference audio + its exact transcript,
* optionally pitch-shifts the result (post-process, semitones),
* transcribes the output with a local Whisper ASR model to compute *real* WER/CER,
* reports measured inference time, CPU and RAM.

No preset-TTS fallback: if the model cannot load, synthesis raises an error.
"""
from __future__ import annotations

import gc
import math
import threading
import time
import uuid
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional, Tuple

import numpy as np
import psutil
import soundfile as sf

try:
    import static_ffmpeg
    static_ffmpeg.add_paths()
except Exception:
    pass

try:
    import torch
    import torchaudio

    def _safe_torchaudio_load(filepath, *args, **kwargs):
        data, sr = sf.read(filepath, dtype="float32")
        tensor = torch.from_numpy(data)
        if tensor.ndim == 1:
            tensor = tensor.unsqueeze(0)
        elif tensor.ndim == 2:
            tensor = tensor.t()
        return tensor, sr

    torchaudio.load = _safe_torchaudio_load
except Exception:
    pass

from backend.app.audio.processor import AudioProcessor
from backend.app.core.config import OUTPUTS_DIR
from backend.app.evaluation.metrics import compute_cer, compute_speaker_similarity, compute_wer
from ml.model_config import default_model_config

if TYPE_CHECKING:  # pragma: no cover - typing only
    from f5_tts.api import F5TTS  # type: ignore[import-not-found, unused-ignore]


class ModelNotAvailableError(RuntimeError):
    """Raised when the neural cloning model cannot be loaded."""


def _silent_info(*_args: Any, **_kwargs: Any) -> None:
    """Swallow F5-TTS's console progress messages."""


class VoiceCloningEngine:
    def __init__(self) -> None:
        cfg = default_model_config
        self.model_name: str = cfg.model_name
        self.model_id: str = cfg.model_id
        self.device: str = "CPU"
        self.sample_rate: int = cfg.sample_rate
        self._tts: Optional["F5TTS"] = None
        self._asr: Optional[Callable[..., Any]] = None
        self._lock = threading.Lock()
        self.last_error: Optional[str] = None
        self.progress: Dict[str, Any] = {
            "is_running": False,
            "percent": 0,
            "stage": "Idle",
            "elapsed_seconds": 0.0,
        }

    def get_progress(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self.progress)

    def _update_progress(self, percent: int, stage: str, elapsed: float = 0.0) -> None:
        with self._lock:
            self.progress["percent"] = min(100, max(0, percent))
            self.progress["stage"] = stage
            self.progress["is_running"] = percent < 100
            if elapsed > 0:
                self.progress["elapsed_seconds"] = round(elapsed, 1)

    # ------------------------------------------------------------------ loading
    @property
    def is_loaded(self) -> bool:
        return self._tts is not None

    def load(self) -> None:
        with self._lock:
            self._load_unlocked()

    def _load_unlocked(self) -> "F5TTS":
        """Load the model if needed and return it (caller must hold the lock)."""
        if self._tts is not None:
            return self._tts
        try:
            import torch
            from f5_tts.api import F5TTS  # type: ignore[import-not-found, unused-ignore]

            torch.set_num_threads(max(1, psutil.cpu_count(logical=False) or 4))
            tts = F5TTS(model=self.model_id, device="cpu")
            self.sample_rate = int(getattr(tts, "target_sample_rate", default_model_config.sample_rate))
            self._tts = tts
            self.last_error = None
            return tts
        except Exception as exc:  # noqa: BLE001 - surface any load failure
            self.last_error = f"{type(exc).__name__}: {exc}"
            raise ModelNotAvailableError(
                f"F5-TTS model could not be loaded: {self.last_error}"
            ) from exc

    def unload(self) -> None:
        with self._lock:
            self._tts = None
            self._asr = None
            gc.collect()

    def _get_asr(self) -> Callable[..., Any]:
        if self._asr is None:
            from transformers import pipeline  # type: ignore[import-not-found, unused-ignore]

            self._asr = pipeline(
                "automatic-speech-recognition",
                model=default_model_config.asr_model_id,
                device="cpu",
            )
        return self._asr

    def transcribe(self, audio: np.ndarray, sr: int) -> Optional[str]:
        """Independent ASR transcript of ``audio``; ``None`` if ASR is unavailable."""
        try:
            if audio.ndim > 1:
                audio = np.mean(audio, axis=-1 if audio.shape[-1] <= 2 else 0)
            asr = self._get_asr()
            result = asr({"raw": audio.astype(np.float32).flatten(), "sampling_rate": sr})
            text = result.get("text", "") if isinstance(result, dict) else ""
            return str(text).strip()
        except Exception as exc:  # noqa: BLE001
            self.last_error = f"ASR failed: {type(exc).__name__}: {exc}"
            return None

    # --------------------------------------------------------------- synthesis
    @staticmethod
    def _pitch_shift(wav: np.ndarray, sr: int, semitones: float) -> np.ndarray:
        if abs(semitones) < 1e-3:
            return wav
        import torch
        import torchaudio.functional as AF

        t = torch.from_numpy(np.ascontiguousarray(wav, dtype=np.float32)).unsqueeze(0)
        shifted = AF.pitch_shift(t, sr, n_steps=float(semitones))
        out: np.ndarray = shifted.squeeze(0).detach().cpu().numpy().astype(np.float32)
        return out

    @staticmethod
    def _temperature_to_cfg(temperature: float) -> float:
        """F5-TTS has no sampling temperature. We map the UI 'temperature' to
        classifier-free-guidance strength: lower temperature -> stronger guidance
        (tighter adherence), higher -> looser / more varied. Default 0.7 -> 2.0."""
        return float(np.clip(2.0 + (0.7 - temperature) * 1.5, 1.0, 3.5))

    def _infer(
        self,
        ref_audio_path: str,
        ref_transcript: str,
        target_text: str,
        speech_speed: float,
        temperature: float,
        seed: Optional[int],
    ) -> Tuple[np.ndarray, int]:
        infer_kwargs: Dict[str, Any] = {
            "ref_file": str(ref_audio_path),
            "ref_text": ref_transcript.strip(),
            "gen_text": target_text.strip(),
            "show_info": _silent_info,
            "speed": float(speech_speed),
            "cfg_strength": self._temperature_to_cfg(temperature),
            "nfe_step": int(default_model_config.nfe_step),
            "remove_silence": False,
        }
        # Only forward an explicit seed: the "random seed" sentinel differs
        # between f5-tts releases (None in >=1.0, -1 in older ones), so leaving
        # it out lets the installed version pick its own default.
        if seed is not None:
            infer_kwargs["seed"] = int(seed)

        with self._lock:
            tts = self._load_unlocked()
            wav, sr, _spec = tts.infer(**infer_kwargs)

        if wav is None:
            raise RuntimeError("F5-TTS returned no audio.")
        return np.asarray(wav, dtype=np.float32).flatten(), int(sr)

    def synthesize(
        self,
        ref_audio_path: str,
        ref_transcript: str,
        target_text: str,
        speech_speed: float = 1.0,
        pitch: float = 0.0,
        temperature: float = 0.7,
        seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not target_text or not target_text.strip():
            raise ValueError("Target text is empty.")
        if not ref_transcript or not ref_transcript.strip():
            raise ValueError("Reference transcript is required for accurate cloning.")

        start_time = time.time()
        proc = psutil.Process()
        psutil.cpu_percent(interval=None)
        start_rss = proc.memory_info().rss

        self._update_progress(5, "Analyzing speaker reference voice & acoustic timbre...", 0.0)

        # Background progress stepper while ODE runs on CPU
        stop_event = threading.Event()

        def _ode_ticker():
            ode_start = time.time()
            while not stop_event.wait(0.4):
                el = time.time() - ode_start
                # Smooth curve: reaches ~40% around 12s, ~70% around 35s, capped at 83%
                p = min(83, int(18 + 65 * (1.0 - math.exp(-el / 28.0))))
                with self._lock:
                    self.progress["percent"] = p
                    self.progress["stage"] = f"Solving flow-matching ODE on CPU ({p}%)..."
                    self.progress["is_running"] = True
                    self.progress["elapsed_seconds"] = round(time.time() - start_time, 1)

        ticker = threading.Thread(target=_ode_ticker, daemon=True)
        ticker.start()

        try:
            wav, sr = self._infer(
                ref_audio_path, ref_transcript, target_text, speech_speed, temperature, seed
            )
        except Exception as exc:
            self._update_progress(0, f"Inference failed: {exc}", time.time() - start_time)
            raise
        finally:
            stop_event.set()
            ticker.join(timeout=1.0)

        if wav.size == 0:
            self._update_progress(0, "F5-TTS produced an empty waveform.", time.time() - start_time)
            raise RuntimeError("F5-TTS produced an empty waveform.")

        self._update_progress(85, "Synthesizing waveform with Vocos 24kHz neural vocoder...", time.time() - start_time)
        wav = self._pitch_shift(wav, sr, pitch)
        peak = float(np.max(np.abs(wav)))
        if peak > 0.99:
            wav = wav / peak * 0.95

        self._update_progress(90, "Writing lossless WAV audio file...", time.time() - start_time)
        output_filename = f"gen_{uuid.uuid4().hex[:10]}.wav"
        output_path = OUTPUTS_DIR / output_filename
        sf.write(str(output_path), wav, sr, subtype="PCM_16")

        inference_time = round(time.time() - start_time, 2)
        peak_cpu = round(psutil.cpu_percent(interval=None), 1)
        peak_ram = round(max(start_rss, proc.memory_info().rss) / (1024**2), 1)

        # Independent evaluation: real ASR transcript of the generated audio.
        self._update_progress(93, "Evaluating text accuracy (WER/CER) with Whisper ASR...", time.time() - start_time)
        out_meta = AudioProcessor.inspect_audio(output_path)
        recognized = self.transcribe(wav, sr)
        wer: Optional[float] = None
        cer: Optional[float] = None
        if recognized is not None:
            wer = float(compute_wer(target_text, recognized)["wer"])
            cer = float(compute_cer(target_text, recognized)["cer"])

        self._update_progress(98, "Computing acoustic speaker similarity matrix...", time.time() - start_time)
        speaker_sim = round(compute_speaker_similarity(str(ref_audio_path), str(output_path)), 4)

        self._update_progress(100, "Speech synthesis complete!", inference_time)

        return {
            "output_path": str(output_path),
            "output_filename": output_filename,
            "output_url": f"/data/outputs/{output_filename}",
            "duration_seconds": out_meta["duration_seconds"],
            "sample_rate": sr,
            "channels": 1,
            "peak_amplitude": out_meta["peak_amplitude"],
            "clipping_detected": out_meta["clipping_detected"],
            "snr_estimate": out_meta["snr_estimate"],
            "silence_ratio": out_meta["silence_ratio"],
            "wer": wer,
            "cer": cer,
            "recognized_transcript": recognized,
            "speaker_similarity": speaker_sim,
            "inference_time_seconds": inference_time,
            "cpu_peak": peak_cpu,
            "ram_peak_mb": peak_ram,
        }


# Global engine instance (model weights are loaded lazily on first use / load())
voice_cloning_engine = VoiceCloningEngine()
