"""
Tier 1 & Tier 2 API Tests: Voice Profiles & Audio Validation (11 Test Cases).
Coverage:
- Create voice profile with valid metadata and consent (201 Created)
- Mandatory consent enforcement (400 / 422 Bad Request on missing consent)
- List profiles
- Retrieve profile by ID
- Delete profile by ID
- Non-existent profile lookup (404 Not Found)
- Duplicate profile name rejection (400 Bad Request)
- Reference audio upload and format validation
- Upload of invalid audio format rejected (400 Bad Request)
- File size boundary rejection (>50MB returns 413)
"""

import io
from pathlib import Path
import pytest
import soundfile as sf
from fastapi.testclient import TestClient


@pytest.mark.api
class TestProfilesApi:
    """API test suite for /api/v1/profiles and /api/v1/clone/validate."""

    def test_tc_api_prof_01_create_profile_success(self, client: TestClient):
        """Create voice profile with valid metadata and consent returns 201."""
        payload = {
            "name": "Studio Voice One",
            "description": "Crisp male narration profile",
            "speaker_consent_given": True,
            "consent_signature": "John Doe",
            "reference_transcript": "This is a reference transcript.",
        }
        res = client.post("/api/v1/profiles", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "Studio Voice One"
        assert data["speaker_consent_given"] == 1
        assert "id" in data

    def test_tc_api_prof_02_create_profile_without_consent_rejected(self, client: TestClient):
        """Creating profile with speaker_consent_given=False is rejected."""
        payload = {
            "name": "Unconsenting Voice",
            "speaker_consent_given": False,
        }
        res = client.post("/api/v1/profiles", json=payload)
        assert res.status_code in [400, 422]

    def test_tc_api_prof_03_list_profiles(self, client: TestClient):
        """GET /api/v1/profiles returns a list containing created profiles."""
        client.post(
            "/api/v1/profiles",
            json={"name": "List Test Voice", "speaker_consent_given": True},
        )
        res = client.get("/api/v1/profiles")
        assert res.status_code == 200
        profiles = res.json()
        assert isinstance(profiles, list)
        assert any(p["name"] == "List Test Voice" for p in profiles)

    def test_tc_api_prof_04_get_profile_by_id(self, client: TestClient):
        """GET /api/v1/profiles/{id} retrieves the specific profile."""
        created = client.post(
            "/api/v1/profiles",
            json={"name": "Lookup Voice", "speaker_consent_given": True},
        ).json()
        p_id = created["id"]

        res = client.get(f"/api/v1/profiles/{p_id}")
        assert res.status_code == 200
        assert res.json()["name"] == "Lookup Voice"

    def test_tc_api_prof_05_delete_profile(self, client: TestClient):
        """DELETE /api/v1/profiles/{id} removes the profile."""
        created = client.post(
            "/api/v1/profiles",
            json={"name": "Delete Voice", "speaker_consent_given": True},
        ).json()
        p_id = created["id"]

        del_res = client.delete(f"/api/v1/profiles/{p_id}")
        assert del_res.status_code == 200

        # Subsequent fetch returns 404
        get_res = client.get(f"/api/v1/profiles/{p_id}")
        assert get_res.status_code == 404

    def test_tc_api_prof_06_get_non_existent_profile_404(self, client: TestClient):
        """GET /api/v1/profiles/unknown returns 404 Not Found."""
        res = client.get("/api/v1/profiles/prof-non-existent")
        assert res.status_code == 404

    def test_tc_api_prof_07_duplicate_profile_name_rejected(self, client: TestClient):
        """Creating duplicate profile name returns 400 Bad Request."""
        payload = {"name": "Unique Name", "speaker_consent_given": True}
        r1 = client.post("/api/v1/profiles", json=payload)
        assert r1.status_code == 201

        r2 = client.post("/api/v1/profiles", json=payload)
        assert r2.status_code in [400, 422]

    def test_tc_api_prof_08_upload_and_validate_reference_audio(
        self, client: TestClient, clean_wav_file: Path
    ):
        """POST /api/v1/clone/validate uploads valid audio and returns peaks."""
        with open(clean_wav_file, "rb") as f:
            res = client.post(
                "/api/v1/clone/validate",
                files={"file": ("reference.wav", f, "audio/wav")},
            )
        assert res.status_code == 200
        data = res.json()
        assert data["is_valid"] is True
        assert "audio_id" in data
        assert len(data["peaks"]) == 100

    def test_tc_api_prof_09_upload_invalid_audio_rejected(
        self, client: TestClient, corrupt_wav_file: Path
    ):
        """POST /api/v1/clone/validate with corrupt header returns 400."""
        with open(corrupt_wav_file, "rb") as f:
            res = client.post(
                "/api/v1/clone/validate",
                files={"file": ("corrupt.wav", f, "audio/wav")},
            )
        assert res.status_code == 400

    def test_tc_api_prof_10_upload_unsupported_extension_rejected(self, client: TestClient):
        """POST /api/v1/clone/validate with text file returns 400."""
        res = client.post(
            "/api/v1/clone/validate",
            files={"file": ("notes.txt", io.BytesIO(b"Just text"), "text/plain")},
        )
        assert res.status_code == 400

    def test_tc_api_prof_11_upload_exceeding_50mb_rejected(self, client: TestClient):
        """TC-T2-BND-SEC-06: Extremely large multipart upload (>50MB audio file) rejected with HTTP 413."""
        oversized_bytes = 50 * 1024 * 1024 + 1  # 52,428,801 bytes (>50MB)
        large_buffer = io.BytesIO(b"0" * oversized_bytes)
        res = client.post(
            "/api/v1/clone/validate",
            files={"file": ("oversized_reference.wav", large_buffer, "audio/wav")},
        )
        assert res.status_code == 413
        assert "50MB" in res.json().get("detail", "")
