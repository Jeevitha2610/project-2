# VoiceStudio — REST API Documentation

Base URL: `http://127.0.0.1:8000/api/v1`

## 1. Profiles API

### `POST /profiles/`
Create a new voice profile with reference audio file and transcript.
- **Request**: Multipart Form Data
  - `name`: String (required)
  - `reference_transcript`: String (required)
  - `audio_file`: Binary Audio File (WAV, MP3, FLAC)
  - `description`: String (optional)
- **Response**: `VoiceProfileResponse`

### `GET /profiles/`
List all saved voice profiles.
- **Response**: `List[VoiceProfileResponse]`

### `DELETE /profiles/{profile_id}`
Delete a profile and its associated audio file.

---

## 2. Synthesis API

### `POST /synthesis/generate`
Execute voice cloning speech synthesis.
- **Request**: JSON (`SynthesisRequest`)
  ```json
  {
    "profile_id": "uuid-string",
    "target_text": "Hello, this is a cloned voice sample generated using VoiceStudio.",
    "speech_speed": 1.0,
    "pitch": 0.0,
    "temperature": 0.7,
    "output_format": "WAV (Lossless)"
  }
  ```
- **Response**: `SynthesisResponse` (includes generated audio URL, WER, CER, speaker similarity, duration, CPU peak, and inference time).

### `GET /synthesis/history`
List previous generation jobs.

### `DELETE /synthesis/history/{job_id}`
Delete a generation record and clean up the audio file.

---

## 3. Monitoring API

### `GET /monitoring/`
Retrieve real-time host hardware metrics.
- **Response**:
  ```json
  {
    "cpu_percent": 12.0,
    "ram_used_gb": 4.2,
    "ram_total_gb": 16.0,
    "ram_percent": 26.3,
    "disk_free_gb": 120.4,
    "device": "CPU (Intel Core)",
    "model_name": "IndicF5 (English)",
    "model_status": "Loaded",
    "queue_length": 0
  }
  ```
