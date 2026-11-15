# VoiceStudio — High-Fidelity Local English Voice Cloning Workstation

VoiceStudio is a complete, local-first English voice-cloning web application designed specifically for **Windows 11** on **Intel 13th-Gen CPUs** with **16 GB RAM** without requiring a dedicated GPU or NPU.

![VoiceStudio UI Reference](image/ui%20design.png)

---

## Key Features

1. **True Reference-Based Voice Cloning**: Conditions voice timbre, pitch, and prosody on reference speech recordings (`.wav`, `.mp3`, `.flac`).
2. **Exact English Text Adherence**: Synthesizes exact target English sentences without truncation, omission, or hallucination.
3. **Local Windows CPU Inference**: Fast CPU inference using PyTorch (`torch-2.15.0+cpu`) with ~1.25 GB peak RAM.
4. **Dark Dashboard Matching Reference**: Complete dark navy theme with purple-blue gradient accents reproducing all layout and interaction concepts from Image 1.
5. **12 Working Navigation Sections**:
   - Studio / Synthesis
   - Voice Profiles
   - Model Management & Settings
   - Independent Evaluation
   - Generation History
   - Hardware & System Monitor
   - Audio Library
   - Technical Reports
   - Settings & Preferences
   - About & License
6. **Independent Evaluation Engine**:
   - Levenshtein **Word Error Rate (WER)** and **Character Error Rate (CER)**.
   - Cosine distance on acoustic speaker feature embeddings.
   - Signal DSP checks: Peak amplitude, clipping detection, silence ratio, and SNR estimation.
7. **SQLite Metadata Persistence**: Voice profiles, reference transcripts, and generation history persist reliably across restarts.
8. **Graphify Architecture & Skill**: Documented component knowledge graph (`graphify/`) and reusable `voice-studio-graphify` skill.

---

## Architecture

```text
VoiceStudio/
├── frontend/               # React 19 + TypeScript + Vite + Tailwind CSS
├── backend/                # FastAPI + SQLite + SQLAlchemy
│   └── app/
│       ├── api/            # REST endpoints (/profiles, /synthesis, /models, /monitoring)
│       ├── audio/          # DSP processing, clipping detection, normalization
│       ├── database/       # SQLite models & sessions
│       ├── evaluation/     # Levenshtein WER/CER & speaker similarity
│       └── monitoring/     # Real-time CPU, RAM & disk telemetry
├── ml/                     # ML inference engine & model adapters
├── data/                   # Audio storage (/profiles, /references, /outputs)
├── docs/                   # Full documentation (Architecture, API, Models, Testing)
├── graphify/               # Graphify nodes, edges & architecture report
├── reports/                # Benchmark, test summary & release readiness reports
└── tests/                  # 114 automated tests (Unit, API, Integration)
```

---

## Quick Start

### 1. Prerequisites
- Windows 11
- Python 3.10+ (Python 3.14 detected and supported)
- Node.js 18+ (Node v26 detected and supported)

### 2. Backend Setup
```powershell
# Create and activate virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend API (port 8000)
.\.venv\Scripts\uvicorn.exe backend.app.main:app --host 127.0.0.1 --port 8000
```

### 3. Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```
Open your browser to `http://localhost:5173`.

---

## Running Automated Tests

Run the full backend test suite (113 passing tests):
```powershell
.\.venv\Scripts\pytest.exe -v tests/
```

Build the frontend production bundle:
```powershell
cd frontend
npm run build
```

---

## Documentation Links
* [System Architecture](docs/ARCHITECTURE.md)
* [Model Selection & CPU Benchmarks](docs/MODEL_SELECTION_REPORT.md)
* [REST API Reference](docs/API.md)
* [Testing Strategy Report](docs/TESTING.md)
* [User Guide](docs/USER_GUIDE.md)
* [Licenses](docs/LICENSES.md)
* [Graphify Knowledge Graph](docs/GRAPHIFY.md)
* [Release Readiness Assessment](reports/RELEASE_READINESS.md)

---

## Safety and Licensing Notice

> [!IMPORTANT]
> **F5-TTS Weights Licensing**: The F5-TTS pretrained model weights are licensed under **Creative Commons Attribution-NonCommercial 4.0 International (CC-BY-NC-4.0)**. They are intended strictly for non-commercial research, academic, and evaluation purposes. Application source code is MIT licensed.

- **Ethical Voice Cloning & Consent**: Explicit user consent is mandatory prior to synthesizing speech.
- **Audit Logging**: Every voice generation automatically records an immutable audit entry in the local SQLite database (`audit_records`) containing generation timestamps, SHA-256 hashes of the reference audio, and SHA-256 hashes of the target text.
