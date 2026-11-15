import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database.session import init_db

@pytest.fixture(autouse=True)
def setup_database():
    init_db()

def test_health():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "online"
        assert data["device"] == "CPU"

def test_monitoring():
    with TestClient(app) as client:
        response = client.get("/api/v1/monitoring/")
        assert response.status_code == 200
        data = response.json()
        assert "cpu_percent" in data
        assert "ram_used_gb" in data
        assert "ram_total_gb" in data

def test_models():
    with TestClient(app) as client:
        response = client.get("/api/v1/models/")
        assert response.status_code == 200
        models = response.json()
        assert len(models) >= 1
        assert models[0]["device"] == "CPU"

def test_profiles_and_synthesis():
    with TestClient(app) as client:
        # 1. Check default profile
        response = client.get("/api/v1/profiles/")
        assert response.status_code == 200
        profiles = response.json()
        assert len(profiles) >= 1
        profile = profiles[0]
        profile_id = profile["id"]
        
        # 2. Run synthesis on target text
        target_sentence = "Hello, this is a cloned voice sample generated using VoiceStudio."
        synth_req = {
            "profile_id": profile_id,
            "target_text": target_sentence,
            "speech_speed": 1.0,
            "pitch": 0.0,
            "temperature": 0.7,
            "output_format": "WAV (Lossless)"
        }
        synth_resp = client.post("/api/v1/synthesis/generate", json=synth_req)
        assert synth_resp.status_code == 200
        result = synth_resp.json()
        
        assert result["status"] == "completed"
        assert result["target_text"] == target_sentence
        assert result["duration_seconds"] > 0
        assert result["sample_rate"] == 24000
        assert result["speaker_similarity"] >= 0.5
        assert result["wer"] is None or (0.0 <= result["wer"] <= 1.0)
        assert result["cer"] is None or (0.0 <= result["cer"] <= 1.0)
        assert result["output_audio_url"].startswith("/data/outputs/")
        
        # 3. Check history
        hist_resp = client.get("/api/v1/synthesis/history")
        assert hist_resp.status_code == 200
        history = hist_resp.json()
        assert len(history) >= 1
        assert history[0]["id"] == result["id"]
