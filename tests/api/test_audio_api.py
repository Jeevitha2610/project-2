"""
Tier 1 & Tier 2 API Tests: Audio Streaming, Peak Blocks, and WAV Download (9 Test Cases).
Coverage:
- TC-T1-STR-01: HTTP 206 Partial Content with Range: bytes=0-1024
- TC-T1-STR-02: Full audio stream delivery (HTTP 200) with Accept-Ranges
- TC-T1-STR-03: Precomputed 100-bin RMS peaks endpoint
- TC-T1-STR-04: Lossless WAV download with Content-Disposition attachment
- TC-T1-STR-06: Non-existent audio ID returns HTTP 404
- TC-T2-BND-AUD-07: Out-of-bounds byte range returns HTTP 416
- TC-T2-BND-AUD-08: Non-existent audio download returns HTTP 404
- TC-T2-BND-AUD-09: Multipart byte range requests return HTTP 416
- TC-T2-BND-AUD-10: Malformed range header returns HTTP 416
"""

from pathlib import Path
from fastapi.testclient import TestClient
import pytest


@pytest.fixture
def registered_audio_id(client: TestClient, clean_wav_file: Path) -> str:
    """Helper fixture to upload and register a reference audio file, returning audio_id."""
    with open(clean_wav_file, "rb") as f:
        res = client.post(
            "/api/v1/clone/validate",
            files={"file": ("stream_test.wav", f, "audio/wav")},
        )
    assert res.status_code == 200
    return res.json()["audio_id"]


@pytest.mark.api
class TestAudioApi:
    """API test suite for /api/v1/audio."""

    def test_tc_t1_str_01_http_206_partial_content_streaming(
        self, client: TestClient, registered_audio_id: str
    ):
        """TC-T1-STR-01: GET /api/v1/audio/{id} with Range returns HTTP 206 Partial Content."""
        headers = {"Range": "bytes=0-1023"}
        res = client.get(f"/api/v1/audio/{registered_audio_id}", headers=headers)
        assert res.status_code == 206
        assert "Content-Range" in res.headers
        assert res.headers["Content-Range"].startswith("bytes 0-1023/")
        assert len(res.content) == 1024
        assert res.headers["Content-Type"] == "audio/wav"

    def test_tc_t1_str_02_full_audio_stream_delivery(
        self, client: TestClient, registered_audio_id: str
    ):
        """TC-T1-STR-02: GET /api/v1/audio/{id} without Range header returns full audio."""
        res = client.get(f"/api/v1/audio/{registered_audio_id}")
        assert res.status_code == 200
        assert res.headers["Content-Type"] == "audio/wav"
        assert res.headers.get("Accept-Ranges") == "bytes"
        assert len(res.content) > 1000

    def test_tc_t1_str_03_precomputed_peaks_endpoint(
        self, client: TestClient, registered_audio_id: str
    ):
        """TC-T1-STR-03: GET /api/v1/audio/{id}/peaks returns 100 normalized peak blocks."""
        res = client.get(f"/api/v1/audio/{registered_audio_id}/peaks")
        assert res.status_code == 200
        data = res.json()
        assert data["audio_id"] == registered_audio_id
        assert len(data["peaks"]) == 100
        assert all(0.0 <= p <= 1.0 for p in data["peaks"])

    def test_tc_t1_str_04_lossless_wav_download(
        self, client: TestClient, registered_audio_id: str
    ):
        """TC-T1-STR-04: GET /api/v1/audio/{id}/download serves WAV with attachment header."""
        res = client.get(f"/api/v1/audio/{registered_audio_id}/download")
        assert res.status_code == 200
        assert res.headers["Content-Type"] == "audio/wav"
        assert "attachment" in res.headers.get("Content-Disposition", "")
        assert res.content.startswith(b"RIFF")

    def test_tc_t1_str_06_non_existent_audio_peaks_404(self, client: TestClient):
        """TC-T1-STR-06: Requesting peaks for unknown audio ID returns 404."""
        res = client.get("/api/v1/audio/aud-unknown/peaks")
        assert res.status_code == 404

    def test_tc_t2_bnd_aud_07_out_of_bounds_range_416(
        self, client: TestClient, registered_audio_id: str
    ):
        """TC-T2-BND-AUD-07: Invalid range header returns HTTP 416 Range Not Satisfiable."""
        headers = {"Range": "bytes=99999999-999999999"}
        res = client.get(f"/api/v1/audio/{registered_audio_id}", headers=headers)
        assert res.status_code == 416

    def test_tc_t2_bnd_aud_08_non_existent_audio_download_404(self, client: TestClient):
        """Requesting download for unknown audio ID returns 404."""
        res = client.get("/api/v1/audio/aud-unknown/download")
        assert res.status_code == 404

    def test_tc_t2_bnd_aud_09_multipart_range_rejected_416(
        self, client: TestClient, registered_audio_id: str
    ):
        """Multipart byte range requests return HTTP 416 Range Not Satisfiable."""
        headers = {"Range": "bytes=0-100, 200-300"}
        res = client.get(f"/api/v1/audio/{registered_audio_id}", headers=headers)
        assert res.status_code == 416

    def test_tc_t2_bnd_aud_10_malformed_range_syntax_rejected_416(
        self, client: TestClient, registered_audio_id: str
    ):
        """Malformed range header with trailing characters returns HTTP 416."""
        headers = {"Range": "bytes=0-100junk"}
        res = client.get(f"/api/v1/audio/{registered_audio_id}", headers=headers)
        assert res.status_code == 416
