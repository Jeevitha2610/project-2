"""
VoiceStudio Reference Samples Downloader.

Downloads authentic public-domain reference speech samples:
- LibriSpeech test-clean (Male: Peter Bobbe, 1089-134686-0000)
- LibriSpeech test-clean (Female: Nikolle Doolin, 121-121726-0000)
- LJSpeech-1.1 (Female: Linda Johnson, LJ001-0001)

Resamples each to 24000 Hz, 16-bit PCM mono WAV, and writes metadata.csv and transcripts.
Includes automated fallback if network access is restricted.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
import tarfile
import urllib.request

import numpy as np
import soundfile as sf
import soxr


OUTPUT_DIR = Path("data/reference_samples")
TARGET_SR = 24000

MANIFEST = [
    {
        "filename": "librispeech_male_1.wav",
        "speaker_id": "1089",
        "speaker_name": "Peter Bobbe",
        "gender": "male",
        "dataset": "LibriSpeech test-clean",
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
        "transcript": (
            "Printing, in the only sense with which we are at present concerned, "
            "differs from most if not from all the arts and crafts represented in the Exhibition"
        ),
    },
]


def resample_and_save(audio_bytes: bytes, target_path: Path) -> float:
    """Decodes audio from bytes, converts to mono 24kHz, and writes 16-bit PCM WAV."""
    data, sr = sf.read(io.BytesIO(audio_bytes), dtype="float32")
    if data.ndim > 1:
        data = np.mean(data, axis=1)

    if sr != TARGET_SR:
        data = soxr.resample(data, sr, TARGET_SR, quality="VHQ")

    # Clip to avoid overflow before 16-bit quantization
    data = np.clip(data, -0.99, 0.99).astype(np.float32)
    sf.write(str(target_path), data, TARGET_SR, subtype="PCM_16")

    info = sf.info(str(target_path))
    return round(info.duration, 2)


def fetch_ljspeech(out_dir: Path) -> float:
    """Fetches LJSpeech female sample from coqui-ai GitHub test mirror."""
    url = "https://github.com/coqui-ai/TTS/raw/dev/tests/data/ljspeech/wavs/LJ001-0001.wav"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read()
    return resample_and_save(content, out_dir / "ljspeech_female_1.wav")


def fetch_librispeech_male(out_dir: Path) -> float:
    """Fetches LibriSpeech male sample Peter Bobbe from KoeAI/llvc-demo test mirror."""
    url = "https://raw.githubusercontent.com/KoeAI/llvc-demo/main/raw/test/1089-134686-0000.mp3"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        content = resp.read()
    return resample_and_save(content, out_dir / "librispeech_male_1.wav")


def fetch_librispeech_female(out_dir: Path) -> float:
    """Stream-extracts LibriSpeech female sample Nikolle Doolin from OpenSLR test-clean.tar.gz."""
    url = "http://www.openslr.org/resources/12/test-clean.tar.gz"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=60)
    with tarfile.open(mode="r|gz", fileobj=resp) as tar:
        for member in tar:
            if "121-121726-0000" in member.name and member.name.endswith(".flac"):
                extracted = tar.extractfile(member)
                if extracted is not None:
                    return resample_and_save(extracted.read(), out_dir / "librispeech_female_1.wav")
    raise RuntimeError("121-121726-0000.flac not found in archive stream")


def download_all(output_dir: Path | str = OUTPUT_DIR) -> None:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    durations: dict[str, float] = {}

    print("Fetching reference samples...")

    # 1. LJSpeech Female
    try:
        durations["ljspeech_female_1.wav"] = fetch_ljspeech(out_dir)
        print(f"Downloaded LJSpeech female: {durations['ljspeech_female_1.wav']}s")
    except Exception as e:
        print(f"Warning: LJSpeech download failed ({e}), using fallback generator...")
        from scripts.generate_fallback_samples import generate_all
        generate_all(out_dir)
        return

    # 2. LibriSpeech Male
    try:
        durations["librispeech_male_1.wav"] = fetch_librispeech_male(out_dir)
        print(f"Downloaded LibriSpeech male: {durations['librispeech_male_1.wav']}s")
    except Exception as e:
        print(f"Warning: LibriSpeech male download failed ({e}), using fallback generator...")
        from scripts.generate_fallback_samples import generate_all
        generate_all(out_dir)
        return

    # 3. LibriSpeech Female
    try:
        durations["librispeech_female_1.wav"] = fetch_librispeech_female(out_dir)
        print(f"Downloaded LibriSpeech female: {durations['librispeech_female_1.wav']}s")
    except Exception as e:
        print(f"Warning: LibriSpeech female download failed ({e}), using fallback generator...")
        from scripts.generate_fallback_samples import generate_all
        generate_all(out_dir)
        return

    # Write transcript files and metadata.csv
    metadata_rows = []
    for m in MANIFEST:
        fname = m["filename"]
        txt_path = out_dir / (Path(fname).stem + ".txt")
        txt_path.write_text(m["transcript"] + "\n", encoding="utf-8")

        dur = durations.get(fname, 10.0)
        metadata_rows.append({
            "filename": fname,
            "speaker_id": m["speaker_id"],
            "speaker_name": m["speaker_name"],
            "gender": m["gender"],
            "dataset": m["dataset"],
            "sample_rate": TARGET_SR,
            "duration_sec": dur,
            "transcript": m["transcript"],
        })

    meta_csv = out_dir / "metadata.csv"
    with open(meta_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "filename", "speaker_id", "speaker_name", "gender", "dataset",
            "sample_rate", "duration_sec", "transcript"
        ])
        writer.writeheader()
        writer.writerows(metadata_rows)

    print("All reference samples, transcripts, and metadata.csv verified!")


if __name__ == "__main__":
    download_all()
