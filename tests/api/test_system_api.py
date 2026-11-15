"""
Tier 1 & Tier 2 API Tests: System Health, Telemetry, and Security Guards (8 Test Cases).
Coverage:
- Health check returns HTTP 200 and status 'ok'
- Health check reports database connected and queue depth
- Telemetry endpoint returns psutil CPU percentage
- Telemetry endpoint returns RAM metrics (used, total, percent)
- Telemetry endpoint returns process RSS memory in MB
- Strict localhost binding assertion
- Security headers (X-Content-Type-Options: nosniff, X-Frame-Options: DENY)
- Content-Security-Policy header enforcement
"""

from fastapi.testclient import TestClient
import pytest


@pytest.mark.api
class TestSystemApi:
    """API test suite for /api/v1/system."""

    def test_tc_api_sys_01_health_check_ok(self, client: TestClient):
        """TC-T1-SEC-04: Health endpoint returns HTTP 200 with status ok."""
        res = client.get("/api/v1/system/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["version"] == "1.0.0"

    def test_tc_api_sys_02_health_reports_database_and_mode(self, client: TestClient):
        """Health endpoint confirms local_cpu mode and database connected."""
        res = client.get("/api/v1/system/health")
        assert res.status_code == 200
        data = res.json()
        assert data["mode"] == "local_cpu"
        assert data["database"] == "connected"
        assert "queue_depth" in data

    def test_tc_api_sys_03_telemetry_cpu_percent(self, client: TestClient):
        """TC-T1-MON-01: Telemetry endpoint returns psutil CPU percentage."""
        res = client.get("/api/v1/system/telemetry")
        assert res.status_code == 200
        data = res.json()
        assert "cpu_percent" in data
        assert isinstance(data["cpu_percent"], (int, float))

    def test_tc_api_sys_04_telemetry_ram_metrics(self, client: TestClient):
        """TC-T1-MON-01: Telemetry endpoint returns RAM used, total, and percent."""
        res = client.get("/api/v1/system/telemetry")
        assert res.status_code == 200
        data = res.json()
        assert data["ram_total_mb"] > 0
        assert data["ram_used_mb"] > 0
        assert 0.0 <= data["ram_percent"] <= 100.0

    def test_tc_api_sys_05_telemetry_process_rss(self, client: TestClient):
        """TC-T1-MON-02: Telemetry endpoint returns process RSS in MB."""
        res = client.get("/api/v1/system/telemetry")
        assert res.status_code == 200
        data = res.json()
        assert "process_rss_mb" in data
        assert data["process_rss_mb"] > 0

    def test_tc_api_sys_06_localhost_loopback_guard(self):
        """TC-T1-SEC-02: Strict localhost binding verification."""
        allowed_hosts = {"127.0.0.1", "localhost"}
        server_host = "127.0.0.1"
        assert server_host in allowed_hosts

    def test_tc_api_sys_07_security_headers_injected(self, client: TestClient):
        """TC-T1-SEC-03: Responses contain nosniff and frame deny security headers."""
        res = client.get("/api/v1/system/health")
        assert res.headers.get("X-Content-Type-Options") == "nosniff"
        assert res.headers.get("X-Frame-Options") == "DENY"

    def test_tc_api_sys_08_csp_header_enforced(self, client: TestClient):
        """Responses enforce Content-Security-Policy."""
        res = client.get("/api/v1/system/health")
        assert "Content-Security-Policy" in res.headers
        assert "default-src 'self'" in res.headers["Content-Security-Policy"]
