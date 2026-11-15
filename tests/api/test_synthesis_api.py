"""
Tier 1 & Tier 2 API Tests: Voice Synthesis Route & Parameter Boundaries (10 Test Cases).
Coverage:
- Valid synthesis submission returns HTTP 202 Accepted
- Empty target text rejected with HTTP 422
- Whitespace-only target text rejected with HTTP 422
- Single character target text accepted
- Exactly 500 characters target text accepted
- Exceeding 500 characters (501 chars) rejected with HTTP 422
- Unicode and emoji characters in target text accepted
- Speed out of bounds rejected with HTTP 422
- Pitch out of bounds rejected with HTTP 422
- Job status polling and 404 for non-existent job
"""

from fastapi.testclient import TestClient
import pytest


@pytest.mark.api
class TestSynthesisApi:
    """API test suite for /api/v1/synthesis."""

    def test_tc_api_syn_01_submit_synthesis_success(self, client: TestClient):
        """Valid synthesis submission returns 202 Accepted with job_id."""
        payload = {
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

    def test_tc_api_syn_04_single_character_accepted(self, client: TestClient):
        """TC-T2-BND-TXT-03: Single character target text accepted."""
        payload = {"target_text": "A"}
        res = client.post("/api/v1/synthesis", json=payload)
        assert res.status_code == 202

    def test_tc_api_syn_05_exact_500_characters_accepted(self, client: TestClient):
        """TC-T2-BND-TXT-04: Exactly 500 characters target text accepted."""
        payload = {"target_text": "A" * 500}
        res = client.post("/api/v1/synthesis", json=payload)
        assert res.status_code == 202

    def test_tc_api_syn_06_exceeding_500_characters_rejected(self, client: TestClient):
        """TC-T2-BND-TXT-05: 501 characters target text rejected with HTTP 422."""
        payload = {"target_text": "A" * 501}
        res = client.post("/api/v1/synthesis", json=payload)
        assert res.status_code == 422

    def test_tc_api_syn_07_unicode_emoji_accepted(self, client: TestClient):
        """TC-T2-BND-TXT-06: Unicode and emoji characters handled safely."""
        payload = {"target_text": "Hello 🎙️ café naïve ñ!"}
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

    def test_tc_api_syn_10_job_status_polling(self, client: TestClient):
        """Poll job status by ID; non-existent job returns 404."""
        sub_res = client.post("/api/v1/synthesis", json={"target_text": "Polling test"}).json()
        job_id = sub_res["job_id"]

        status_res = client.get(f"/api/v1/synthesis/jobs/{job_id}")
        assert status_res.status_code == 200
        assert status_res.json()["job_id"] == job_id
        assert status_res.json()["status"] in ["queued", "processing", "completed"]

        # Missing job
        missing_res = client.get("/api/v1/synthesis/jobs/job-unknown")
        assert missing_res.status_code == 404
