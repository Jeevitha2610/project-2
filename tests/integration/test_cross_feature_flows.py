"""
VoiceStudio Tier 3 Cross-Feature Combinations & Integration Flows.

Implements all 5 complex cross-feature pairwise workflows defined in TEST_INFRA.md:
- TC-T3-FLW-01: Profile Lifecycle & Synthesis Flow
- TC-T3-FLW-02: ASR Transcription Assistance & Accuracy Feedback Loop
- TC-T3-FLW-03: Task Queue, Telemetry & SSE Broadcast Flow
- TC-T3-FLW-04: Upload Validation Failure & Clean Rollback Flow
- TC-T3-FLW-05: Synthesis, Precomputed Peaks & Speaker Similarity Flow
"""

from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf
import torch
from fastapi.testclient import TestClient

from tests.contracts import (
    AudioProcessor,
    AudioValidator,
    AsrEvaluator,
    DatabaseManager,
    SpeakerVerification,
    StorageSecurity,
    VoiceCloner,
)


@pytest.mark.integration
class TestCrossFeatureFlows:
    """Tier 3: Complex Pairwise Cross-Feature Integration Flows."""

    def test_tc_t3_flw_01_profile_lifecycle_to_synthesis(
        self, client: TestClient, clean_wav_file: Path, test_db: DatabaseManager, temp_storage_dir: Path
    ):
        """
        TC-T3-FLW-01: Profile Lifecycle & Synthesis Flow.
        Profile creation with audio upload -> format validation -> task queue synthesis ->
        history record -> audio download and SHA256 integrity check.
        """
        # Step 1: Upload reference audio for validation
        with open(clean_wav_file, "rb") as f:
            upload_res = client.post(
                "/api/v1/clone/validate",
                files={"file": ("reference.wav", f, "audio/wav")},
            )
        assert upload_res.status_code == 200, f"Upload failed: {upload_res.text}"
        upload_data = upload_res.json()
        assert upload_data["is_valid"] is True
        audio_id = upload_data["audio_id"]
        assert audio_id.startswith("aud-")
        assert upload_data["duration_sec"] > 0
        assert len(upload_data["peaks"]) == 100

        # Step 2: Create Voice Profile with audio reference and explicit consent
        profile_payload = {
            "name": "Flow 01 Studio Voice",
            "description": "Integration test profile for lifecycle synthesis flow",
            "speaker_consent_given": True,
            "consent_signature": "Tester Verified Consent",
            "reference_audio_id": audio_id,
            "reference_transcript": "This is a clean reference speech sample for voice cloning.",
        }
        prof_res = client.post("/api/v1/profiles", json=profile_payload)
        assert prof_res.status_code == 201, f"Profile creation failed: {prof_res.text}"
        profile = prof_res.json()
        profile_id = profile["id"]
        assert profile["name"] == "Flow 01 Studio Voice"
        assert profile["reference_audio_id"] == audio_id

        # Step 3: Enqueue synthesis request using the created profile
        synthesis_payload = {
            "profile_id": profile_id,
            "target_text": "VoiceStudio creates local speech conditioned on reference audio.",
            "speed": 1.0,
            "pitch": 0.0,
            "temperature": 0.7,
            "nfe_steps": 24,
        }
        synth_res = client.post("/api/v1/synthesis", json=synthesis_payload)
        assert synth_res.status_code == 202, f"Synthesis submission failed: {synth_res.text}"
        synth_data = synth_res.json()
        assert synth_data["status"] == "queued"
        job_id = synth_data["job_id"]

        # Step 4: Execute synthesis through worker queue
        proc_res = client.post("/api/v1/synthesis/process-next")
        assert proc_res.status_code == 200, f"Worker processing failed: {proc_res.text}"
        proc_data = proc_res.json()
        assert proc_data["status"] == "completed"
        assert proc_data["job_id"] == job_id
        result_payload = proc_data["result"]
        gen_audio_id = result_payload["audio_id"]
        assert gen_audio_id.startswith("aud-")
        assert result_payload["duration_seconds"] > 0
        assert len(result_payload["peaks"]) == 100

        # Step 5: Verify generation history record in SQLite database
        hist_res = client.get("/api/v1/synthesis/history")
        assert hist_res.status_code == 200
        history = hist_res.json()
        matching = [h for h in history if h.get("prompt_text") == synthesis_payload["target_text"]]
        assert len(matching) >= 1
        assert matching[0]["status"] == "completed"

        # Step 6: Download generated WAV audio file
        down_res = client.get(f"/api/v1/audio/{gen_audio_id}/download")
        assert down_res.status_code == 200, f"Download failed: {down_res.text}"
        assert down_res.headers.get("content-type") == "audio/wav"
        assert "attachment" in down_res.headers.get("content-disposition", "")
        downloaded_bytes = down_res.content
        assert len(downloaded_bytes) > 1000

        # Step 7: Byte-level SHA256 integrity check against database registry
        recomputed_hash = hashlib.sha256(downloaded_bytes).hexdigest()
        db_audio_record = test_db.get_audio_record(gen_audio_id)
        assert db_audio_record is not None
        assert db_audio_record["sha256_hash"] == recomputed_hash, (
            f"SHA256 integrity mismatch: expected {db_audio_record['sha256_hash']}, got {recomputed_hash}"
        )

    def test_tc_t3_flw_02_asr_assistance_to_accuracy_evaluation(
        self, client: TestClient, clean_wav_file: Path, test_db: DatabaseManager, temp_storage_dir: Path
    ):
        """
        TC-T3-FLW-02: ASR Transcription Assistance & Accuracy Feedback Loop.
        Upload reference audio -> request ASR transcription assistance -> edit transcript ->
        synthesize target text -> independent ASR evaluation computing WER/CER metrics.
        """
        # Step 1: Upload unannotated reference audio
        with open(clean_wav_file, "rb") as f:
            upload_res = client.post(
                "/api/v1/clone/validate",
                files={"file": ("raw_reference.wav", f, "audio/wav")},
            )
        assert upload_res.status_code == 200
        ref_audio_id = upload_res.json()["audio_id"]

        # Step 2: Request ASR transcription assistance on uploaded reference
        asr_res = client.post("/api/v1/clone/transcribe", params={"audio_id": ref_audio_id})
        assert asr_res.status_code == 200, f"ASR transcription failed: {asr_res.text}"
        assisted_transcript = asr_res.json()["transcript"]
        assert isinstance(assisted_transcript, str)
        assert len(assisted_transcript) > 0

        # Step 3: User edits / refines transcript and creates profile
        refined_transcript = f"{assisted_transcript} verified by user."
        prof_payload = {
            "name": "ASR Assisted Voice Profile",
            "description": "Profile using ASR transcription assistance",
            "speaker_consent_given": True,
            "consent_signature": "ASR Consent Verified",
            "reference_audio_id": ref_audio_id,
            "reference_transcript": refined_transcript,
        }
        prof_res = client.post("/api/v1/profiles", json=prof_payload)
        assert prof_res.status_code == 201
        profile_id = prof_res.json()["id"]

        # Step 4: Synthesize target text
        target_text = "The quick brown fox jumps over the lazy dog."
        synth_payload = {
            "profile_id": profile_id,
            "target_text": target_text,
            "speed": 1.0,
            "pitch": 0.0,
            "temperature": 0.7,
        }
        submit_res = client.post("/api/v1/synthesis", json=synth_payload)
        assert submit_res.status_code == 202

        # Step 5: Process through task queue
        proc_res = client.post("/api/v1/synthesis/process-next")
        assert proc_res.status_code == 200
        proc_result = proc_res.json()["result"]
        gen_audio_path = Path(proc_result["audio_path"])
        assert gen_audio_path.exists()

        # Step 6: Run independent ASR evaluation on generated audio
        evaluator = AsrEvaluator()
        accuracy_metrics = evaluator.evaluate_accuracy(target_text, gen_audio_path)

        # Step 7: Assert metrics schema adherence and non-negative bounds
        assert 0.0 <= accuracy_metrics.wer <= 100.0
        assert 0.0 <= accuracy_metrics.cer <= 100.0
        assert accuracy_metrics.substitutions >= 0
        assert accuracy_metrics.deletions >= 0
        assert accuracy_metrics.insertions >= 0
        assert accuracy_metrics.reference_words > 0
        assert len(accuracy_metrics.transcribed_text) > 0

        # Step 8: Assert evaluation persists in database
        with test_db.get_connection() as conn:
            eval_row = conn.execute("SELECT * FROM evaluation_metrics ORDER BY evaluated_at DESC LIMIT 1").fetchone()
            assert eval_row is not None
            assert eval_row["target_text"] == target_text
            assert eval_row["wer"] == accuracy_metrics.wer
            assert eval_row["cer"] == accuracy_metrics.cer

    @pytest.mark.anyio
    async def test_tc_t3_flw_03_task_queue_telemetry_sse_broadcast(
        self, async_client, clean_wav_file: Path, test_db: DatabaseManager
    ):
        """
        TC-T3-FLW-03: Task Queue, Telemetry & SSE Broadcast Flow.
        Connect SSE stream -> enqueue synthesis job -> observe queued/progress/completion
        SSE events -> verify psutil telemetry metrics.
        """
        # Step 1: Submit synthesis job with session consent header
        synth_payload = {
            "target_text": "Live telemetry streaming and asynchronous task queue test.",
            "speed": 1.0,
            "pitch": 0.0,
            "temperature": 0.7,
        }
        submit_res = await async_client.post(
            "/api/v1/synthesis",
            json=synth_payload,
            headers={"X-Voice-Consent": "granted"},
        )
        assert submit_res.status_code == 202, f"Submission failed: {submit_res.text}"
        job_id = submit_res.json()["job_id"]

        # Step 2: Connect to SSE events stream and collect streamed packets
        received_events = []
        telemetry_payload = None

        async with async_client.stream("GET", "/api/v1/system/events") as response:
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

            # Read initial events (telemetry and queue state)
            async for line in response.aiter_lines():
                if line.startswith("event:"):
                    current_event = line.replace("event:", "").strip()
                    received_events.append(current_event)
                elif line.startswith("data:") and received_events and received_events[-1] == "telemetry":
                    telemetry_payload = json.loads(line.replace("data:", "").strip())
                    break  # Initial telemetry captured

        # Step 3: Verify psutil telemetry metrics in SSE stream
        assert "telemetry" in received_events
        assert telemetry_payload is not None
        assert "cpu_percent" in telemetry_payload
        assert telemetry_payload["ram_total_mb"] > 0
        assert telemetry_payload["ram_used_mb"] > 0
        assert 0.0 <= telemetry_payload["ram_percent"] <= 100.0
        assert telemetry_payload["process_rss_mb"] > 0
        assert telemetry_payload["queue_depth"] >= 1

        # Step 4: Process the queued job
        proc_res = await async_client.post("/api/v1/synthesis/process-next")
        assert proc_res.status_code == 200
        assert proc_res.json()["status"] == "completed"

        # Step 5: Verify completed job state via status endpoint
        status_res = await async_client.get(f"/api/v1/synthesis/jobs/{job_id}")
        assert status_res.status_code == 200
        assert status_res.json()["status"] == "completed"

    def test_tc_t3_flw_04_upload_validation_failure_clean_rollback(
        self, client: TestClient, test_db: DatabaseManager, temp_storage_dir: Path
    ):
        """
        TC-T3-FLW-04: Upload Validation Failure & Clean Rollback Flow.
        Upload corrupt/unsupported audio -> AudioValidator rejects ->
        assert NO orphan profile in SQLite database and NO orphan temp files on disk.
        """
        # Baseline snapshot: count profiles and audio records
        with test_db.get_connection() as conn:
            initial_profile_count = conn.execute("SELECT count(*) FROM voice_profiles").fetchone()[0]
            initial_audio_count = conn.execute("SELECT count(*) FROM audio_files").fetchone()[0]

        ref_dir = temp_storage_dir / "references"
        ref_dir.mkdir(parents=True, exist_ok=True)
        initial_files = set(ref_dir.glob("*"))

        # Test A: Corrupted WAV file upload
        corrupt_bytes = b"RIFF\x24\x00\x00\x00WAVEfmt \x10\x00\x00\x00BAD_DATA_NOT_AUDIO"
        corrupt_res = client.post(
            "/api/v1/clone/validate",
            files={"file": ("corrupted_header.wav", io.BytesIO(corrupt_bytes), "audio/wav")},
        )
        assert corrupt_res.status_code == 400, f"Expected 400, got: {corrupt_res.status_code}"

        # Test B: Unsupported MIME / file extension upload
        unsupported_res = client.post(
            "/api/v1/clone/validate",
            files={"file": ("malicious.exe", io.BytesIO(b"MZ\x90\x00Executable"), "application/octet-stream")},
        )
        assert unsupported_res.status_code == 400

        # Test C: Pure digital silence audio upload
        sr = 24000
        silent_audio = np.zeros(int(2.0 * sr), dtype=np.float32)
        buf = io.BytesIO()
        sf.write(buf, silent_audio, sr, format="WAV", subtype="PCM_16")
        silent_bytes = buf.getvalue()

        silent_res = client.post(
            "/api/v1/clone/validate",
            files={"file": ("silent_tone.wav", io.BytesIO(silent_bytes), "audio/wav")},
        )
        assert silent_res.status_code == 400

        # Rollback Audit: Assert NO orphan profile records created
        with test_db.get_connection() as conn:
            final_profile_count = conn.execute("SELECT count(*) FROM voice_profiles").fetchone()[0]
            final_audio_count = conn.execute("SELECT count(*) FROM audio_files").fetchone()[0]

        assert final_profile_count == initial_profile_count, "Database contains orphan voice profile records!"
        assert final_audio_count == initial_audio_count, "Database contains orphan audio file catalog records!"

        # Rollback Audit: Assert NO orphan temporary or partial files remain on disk
        current_files = set(ref_dir.glob("*"))
        orphan_files = current_files - initial_files
        assert len(orphan_files) == 0, f"Filesystem contains orphan temp files: {orphan_files}"

    def test_tc_t3_flw_05_synthesis_peaks_streaming_speaker_similarity(
        self, client: TestClient, clean_wav_file: Path, test_db: DatabaseManager, temp_storage_dir: Path
    ):
        """
        TC-T3-FLW-05: Synthesis, Precomputed Peaks & Speaker Similarity Flow.
        Synthesize from reference audio -> export WAV -> verify 100-bin peak blocks ->
        stream audio via HTTP 206 -> verify SpeakerVerification cosine similarity score.
        """
        # Step 1: Synthesize speech from clean reference audio
        cloner = VoiceCloner()
        synth_result = cloner.synthesize(
            prompt_audio_path=clean_wav_file,
            prompt_text="Clean acoustic reference speech.",
            target_text="Acoustic peaks, streaming playback, and speaker verification flow.",
            speed=1.0,
            pitch=0.0,
            temperature=0.7,
            nfe_steps=24,
        )
        assert synth_result.duration_sec > 0
        assert synth_result.sample_rate == 24000

        # Step 2: Export WAV file and compute precomputed peak array
        gen_dir = temp_storage_dir / "generated"
        gen_dir.mkdir(parents=True, exist_ok=True)
        gen_wav_path = gen_dir / "flow05_output.wav"
        AudioProcessor.export_wav(synth_result.audio_tensor, synth_result.sample_rate, gen_wav_path)
        assert gen_wav_path.exists()

        audio_data, sr = sf.read(str(gen_wav_path), dtype="float32")
        mono = AudioProcessor.to_mono(audio_data)
        peaks = AudioProcessor.compute_rms_peaks(mono, num_blocks=100)

        # Step 3: Verify 100-bin normalized peak array structure
        assert len(peaks) == 100
        assert all(0.0 <= p <= 1.0 for p in peaks)
        assert max(peaks) > 0.0

        # Step 4: Register audio in database
        sha256 = StorageSecurity.compute_sha256(gen_wav_path)
        audio_rec = test_db.create_audio_record(
            file_type="generated",
            filename=gen_wav_path.name,
            file_path=str(gen_wav_path),
            sha256_hash=sha256,
            file_size_bytes=gen_wav_path.stat().st_size,
            sample_rate=sr,
            channels=1,
            duration_seconds=synth_result.duration_sec,
        )
        audio_id = audio_rec["id"]

        # Step 5: Test HTTP 206 Partial Content audio streaming with byte range
        range_res = client.get(
            f"/api/v1/audio/{audio_id}",
            headers={"Range": "bytes=0-1023"},
        )
        assert range_res.status_code == 206, f"Streaming failed: {range_res.status_code}"
        assert range_res.headers.get("content-type") == "audio/wav"
        assert range_res.headers.get("accept-ranges") == "bytes"
        assert range_res.headers.get("content-length") == "1024"
        assert "bytes 0-1023/" in range_res.headers.get("content-range", "")
        assert len(range_res.content) == 1024

        # Step 6: Verify precomputed peaks endpoint
        peaks_res = client.get(f"/api/v1/audio/{audio_id}/peaks")
        assert peaks_res.status_code == 200
        peaks_data = peaks_res.json()
        assert peaks_data["num_blocks"] == 100
        assert len(peaks_data["peaks"]) == 100

        # Step 7: Run SpeakerVerification comparing generated audio against reference
        speaker_verifier = SpeakerVerification(embedding_dim=512)
        similarity = speaker_verifier.compute_similarity(clean_wav_file, gen_wav_path)

        assert -1.0 <= similarity.cosine_similarity <= 1.0
        assert 0.0 <= similarity.calibrated_percentage <= 100.0
        assert similarity.embedding_dim == 512
