"""
Tier 1 & Tier 2 API Tests: Voice Synthesis Route, Parameter Boundaries & Consent (14 Test Cases).
Coverage:
- Valid synthesis submission with consented profile returns HTTP 202 Accepted
- TC-T2-BND-SEC-05: Synthesis request without profile or consent rejected with HTTP 403 Forbidden
- TC-T2-BND-SEC-05: Synthesis request with unconsented profile rejected with HTTP 403 Forbidden
- Synthesis request authorized via active session consent header returns HTTP 202 Accepted
- Synthesis request with non-existent profile returns HTTP 404 Not Found
- TC-T2-BND-TXT-01: Empty target text rejected with HTTP 422
- TC-T2-BND-TXT-02: Whitespace-only target text rejected with HTTP 422
- TC-T2-BND-TXT-03: Single character target text accepted
- TC-T2-BND-TXT-04: Exactly 500 characters target text accepted
- TC-T2-BND-TXT-05: Exceeding 500 characters (501 chars) rejected with HTTP 422
- TC-T2-BND-TXT-06: Unicode and emoji characters in target text accepted
- TC-T2-BND-PRM-01: Speed out of bounds rejected with HTTP 422
- TC-T2-BND-PRM-03: Pitch out of bounds rejected with HTTP 422
- Job status polling and 404 for non-existent job
"""

import uuid
from fastapi.testclient import TestClient
import pytest


@pytest.fixture
def consented_profile(client: TestClient) -> dict:
    """Fixture providing a registered voice profile with verified speaker consent."""
    payload = {
        "name": f"Consented Profile {uuid.uuid4().hex[:6]}",
        "description": "Standard speaker profile with explicit affirmative consent",
        "speaker_consent_given": True,
        "consent_signature": "Verified Speaker",
    }
    res = client.post("/api/v1/profiles", json=payload)
    assert res.status_code == 201
    return res.json()


@pytest.mark.api
class TestSynthesisApi:
    """API test suite for /api/v1/synthesis."""

    def test_tc_api_syn_01_submit_synthesis_success(
        self, client: TestClient, consented_profile: dict
    ):
        """Valid synthesis submission with consented profile returns 202 Accepted with job_id."""
        payload = {
            "profile_id": consented_profile["id"],
            "target_text": "Welcome to VoiceStudio production speech synthesis.",
            "speed": 1.0,
            "pitch": 0.0,
            "temperature": 0.7,
            "nfe_steps": 24,
        }
        res = client.post("/api/v1/synthesis", json=payload)
        assert res.status_code == 202
        data = res.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        assert "queue_position" in data

    def test_tc_t2_bnd_sec_05_synthesis_without_profile_or_consent_rejected(
        self, client: TestClient
    ):
        """TC-T2-BND-SEC-05: Synthesis request submitted without profile or consent returns HTTP 403 Forbidden."""
        payload = {
            "target_text": "Attempting synthesis with no profile or consent record.",
        }
        res = client.post("/api/v1/synthesis", json=payload)
        assert res.status_code == 403
        data = res.json()
        assert data["detail"] == "Mandatory voice consent required before synthesis"

    def test_tc_t2_bnd_sec_05_synthesis_unconsented_profile_rejected(
        self, client: TestClient, test_db
    ):
        """TC-T2-BND-SEC-05: Synthesis request submitted with unconsented profile returns HTTP 403 Forbidden."""
        unconsented_id = f"prof-unconsented-{uuid.uuid4().hex[:6]}"
        with test_db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO voice_profiles (
                    id, name, description, speaker_consent_given, consent_timestamp,
                    consent_signature, created_at, updated_at
                ) VALUES (?, ?, ?, 0, '2026-01-01T00:00:00Z', '', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')
                """,
                (unconsented_id, f"Unconsented Voice {uuid.uuid4().hex[:6]}", "Unconsented voice"),
            )
            conn.commit()

        payload = {
            "profile_id": unconsented_id,
            "target_text": "Attempting synthesis using an unconsented voice profile.",
        }
        res = client.post("/api/v1/synthesis", json=payload)
        assert res.status_code == 403
        data = res.json()
        assert data["detail"] == "Mandatory voice consent required before synthesis"

    def test_tc_api_syn_consented_session_header_accepted(self, client: TestClient):
        """Synthesis request authorized via active session consent header returns 202 Accepted."""
        payload = {
            "target_text": "Synthesis authorized via active session consent header.",
        }
        headers = {"X-Voice-Consent": "granted"}
        res = client.post("/api/v1/synthesis", json=payload, headers=headers)
        assert res.status_code == 202
        assert "job_id" in res.json()

    def test_tc_api_syn_non_existent_profile_returns_404(self, client: TestClient):
        """Synthesis request with non-existent profile ID returns 404 Not Found."""
        payload = {
            "profile_id": "prof-missing-profile-id",
            "target_text": "Valid text with non-existent profile.",
        }
        res = client.post("/api/v1/synthesis", json=payload)
        assert res.status_code == 404
        assert res.json()["detail"] == "Voice profile not found"

    def test_tc_api_syn_02_empty_target_text_rejected(self, client: TestClient):
        """TC-T2-BND-TXT-01: Empty target text string rejected with HTTP 422."""
        payload = {"target_text": ""}
        res = client.post("/api/v1/synthesis", json=payload)
        assert res.status_code == 422

    def test_tc_api_syn_03_whitespace_only_target_text_rejected(self, client: TestClient):
        """TC-T2-BND-TXT-02: Whitespace-only target text rejected with HTTP 422."""
        payload = {"target_text": "    \t\n   "}
        res = client.post("/api/v1/synthesis", json=payload)
        assert res.status_code == 422

    def test_tc_api_syn_04_single_character_accepted(
        self, client: TestClient, consented_profile: dict
    ):
        """TC-T2-BND-TXT-03: Single character target text accepted."""
        payload = {"profile_id": consented_profile["id"], "target_text": "A"}
        res = client.post("/api/v1/synthesis", json=payload)
        assert res.status_code == 202

    def test_tc_api_syn_05_exact_500_characters_accepted(
        self, client: TestClient, consented_profile: dict
    ):
        """TC-T2-BND-TXT-04: Exactly 500 characters target text accepted."""
        payload = {"profile_id": consented_profile["id"], "target_text": "A" * 500}
        res = client.post("/api/v1/synthesis", json=payload)
        assert res.status_code == 202

    def test_tc_api_syn_06_exceeding_500_characters_rejected(self, client: TestClient):
        """TC-T2-BND-TXT-05: 501 characters target text rejected with HTTP 422."""
        payload = {"target_text": "A" * 501}
        res = client.post("/api/v1/synthesis", json=payload)
        assert res.status_code == 422

    def test_tc_api_syn_07_unicode_emoji_accepted(
        self, client: TestClient, consented_profile: dict
    ):
        """TC-T2-BND-TXT-06: Unicode and emoji characters handled safely."""
        payload = {
            "profile_id": consented_profile["id"],
            "target_text": "Hello 🎙️ café naïve ñ!",
        }
        res = client.post("/api/v1/synthesis", json=payload)
        assert res.status_code == 202

    def test_tc_api_syn_08_speed_out_of_bounds_rejected(self, client: TestClient):
        """TC-T2-BND-PRM-01: Speed outside [0.5, 2.0] rejected with HTTP 422."""
        res_low = client.post("/api/v1/synthesis", json={"target_text": "Valid", "speed": 0.2})
        assert res_low.status_code == 422

        res_high = client.post("/api/v1/synthesis", json={"target_text": "Valid", "speed": 3.0})
        assert res_high.status_code == 422

    def test_tc_api_syn_09_pitch_out_of_bounds_rejected(self, client: TestClient):
        """TC-T2-BND-PRM-03: Pitch outside [-12.0, 12.0] rejected with HTTP 422."""
        res_low = client.post("/api/v1/synthesis", json={"target_text": "Valid", "pitch": -20.0})
        assert res_low.status_code == 422

        res_high = client.post("/api/v1/synthesis", json={"target_text": "Valid", "pitch": 20.0})
        assert res_high.status_code == 422

    def test_tc_api_syn_10_job_status_polling(
        self, client: TestClient, consented_profile: dict
    ):
        """Poll job status by ID; non-existent job returns 404."""
        sub_res = client.post(
            "/api/v1/synthesis",
            json={"profile_id": consented_profile["id"], "target_text": "Polling test"},
        ).json()
        job_id = sub_res["job_id"]

        status_res = client.get(f"/api/v1/synthesis/jobs/{job_id}")
        assert status_res.status_code == 200
        assert status_res.json()["job_id"] == job_id
        assert status_res.json()["status"] in ["queued", "processing", "completed"]

        # Missing job
        missing_res = client.get("/api/v1/synthesis/jobs/job-unknown")
        assert missing_res.status_code == 404
