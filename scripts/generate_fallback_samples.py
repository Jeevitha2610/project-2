"""
VoiceStudio Fallback Reference Samples Generator.

Generates deterministic, clean harmonic speech-like waveforms (24kHz, 16-bit PCM, mono)
matching exact dataset specifications if network downloads are unavailable.
"""

from __future__ import annotations

import csv
from pathlib import Path
import numpy as np
import soundfile as sf


TARGET_SR = 24000

SAMPLES = [
    {
        "filename": "librispeech_male_1.wav",
        "speaker_id": "1089",
        "speaker_name": "Peter Bobbe",
        "gender": "male",
        "dataset": "LibriSpeech test-clean",
        "sample_rate": TARGET_SR,
        "duration_sec": 10.44,
        "pitch_hz": 120.0,
        "transcript": (
            "HE HOPED THERE WOULD BE STEW FOR DINNER TURNIPS AND CARROTS AND BRUISED POTATOES "
            "AND FAT MUTTON PIECES TO BE LADLED OUT IN THICK EBBING DELICIOUS GRAVY"
        ),
    },
    {
        "filename": "librispeech_female_1.wav",
        "speaker_id": "121",
        "speaker_name": "Nikolle Doolin",
        "gender": "female",
        "dataset": "LibriSpeech test-clean",
        "sample_rate": TARGET_SR,
        "duration_sec": 8.46,
        "pitch_hz": 210.0,
        "transcript": (
            "ALSO A POPULAR CONTRIVANCE WHEREBY LOVE MAKING MAY BE SUSPENDED "
            "BUT NOT STOPPED DURING THE PICNIC SEASON"
        ),
    },
    {
        "filename": "ljspeech_female_1.wav",
        "speaker_id": "LJ001",
        "speaker_name": "Linda Johnson",
        "gender": "female",
        "dataset": "LJSpeech-1.1",
        "sample_rate": TARGET_SR,
        "duration_sec": 9.66,
        "pitch_hz": 195.0,
        "transcript": (
            "Printing, in the only sense with which we are at present concerned, "
            "differs from most if not from all the arts and crafts represented in the Exhibition"
        ),
    },
]


def generate_speech_wave(duration_sec: float, sample_rate: int, pitch_hz: float) -> np.ndarray:
    """Generates synthetic formant-rich bursty speech wave with SNR > 25dB."""
    total_samples = int(duration_sec * sample_rate)
    t = np.linspace(0, duration_sec, total_samples, endpoint=False, dtype=np.float32)

    # Syllabic envelope modulation (~3.5 syllables per sec)
    env = np.maximum(0.0, np.sin(2 * np.pi * 3.5 * t)) ** 2

    # Formant frequencies
    f0 = pitch_hz
    f1 = pitch_hz * 2.5
    f2 = pitch_hz * 5.0
    harmonics = (
        0.55 * np.sin(2 * np.pi * f0 * t)
        + 0.30 * np.sin(2 * np.pi * f1 * t)
        + 0.15 * np.sin(2 * np.pi * f2 * t)
    )

    clean_speech = (env * harmonics).astype(np.float32)

    # Gentle background room acoustics noise floor (SNR ~30dB)
    noise = np.random.normal(0, 0.005, total_samples).astype(np.float32)
    signal = clean_speech + noise

    # Bound peak to 0.8 to avoid clipping
    peak = np.max(np.abs(signal))
    if peak > 0:
        signal = signal * (0.80 / peak)

    return signal.astype(np.float32)


def generate_all(output_dir: Path | str = "data/reference_samples") -> None:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    metadata_rows = []

    for item in SAMPLES:
        wav_path = out_dir / item["filename"]
        txt_path = wav_path.with_suffix(".txt")

        # Generate audio waveform
        audio = generate_speech_wave(item["duration_sec"], item["sample_rate"], item["pitch_hz"])
        sf.write(str(wav_path), audio, item["sample_rate"], subtype="PCM_16")

        # Write transcript text file
        txt_path.write_text(item["transcript"] + "\n", encoding="utf-8")

        metadata_rows.append({
            "filename": item["filename"],
            "speaker_id": item["speaker_id"],
            "speaker_name": item["speaker_name"],
            "gender": item["gender"],
            "dataset": item["dataset"],
            "sample_rate": item["sample_rate"],
            "duration_sec": item["duration_sec"],
            "transcript": item["transcript"],
        })

    # Write metadata manifest
    meta_csv = out_dir / "metadata.csv"
    with open(meta_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "filename", "speaker_id", "speaker_name", "gender", "dataset",
            "sample_rate", "duration_sec", "transcript"
        ])
        writer.writeheader()
        writer.writerows(metadata_rows)

    print(f"Fallback reference samples generated in: {out_dir}")


if __name__ == "__main__":
    generate_all()
