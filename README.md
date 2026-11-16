# VoiceStudio — High-Fidelity Zero-Shot Voice Cloning Workstation

VoiceStudio is a complete zero-shot voice-cloning web application with real-time neural synthesis, featuring **F5-TTS v1 Base**, **Vocos 24 kHz vocoder**, **SpeechBrain ECAPA-TDNN speaker similarity**, **faster-whisper ASR verification**, a **FastAPI** backend, and a modern **React 19 / TypeScript / Tailwind CSS** frontend.

It supports dual execution:
1. **Local Windows 11 CPU Engine**: Optimized for Intel Core i5-13th Gen H (4 P-cores + 8 E-cores) with zero dedicated GPU required.
2. **Google Colab NVIDIA T4 GPU Cloud Bridge**: One-click GPU inference worker via secure Cloudflare Tunnel, dropping generation time to **~4.6 seconds** at **32 ODE steps** (~250x faster).

![VoiceStudio UI Reference](image/ui%20design.png)

---

## What Has Happened: Completed Upgrades & Optimizations

### 1. Auto-Transcribe & Audio Preprocessing (Fixing "First Words Cut Off")
- Automatically transcribes uploaded reference audio using faster-whisper (int8) to guarantee word-level phonetic alignment.
- Trims references to clean sentence boundaries (6–10s) with 0.15s trailing silence.
- Normalizes loudness to 0.95 peak, removes background noise via spectral gating (`noisereduce`), and converts to mono 24 kHz PCM WAV.
- Caches processed audio and mel spectrograms in `ml/reference_cache.py`.

### 2. Completeness Gate (Zero Skipped Words Guarantee)
- Splits target text into sentence chunks of $\le 25$ words after normalizing numbers, currency, dates, and abbreviations.
- Verifies every generated chunk with faster-whisper (int8) against the intended text.
- Pipelined verification: verifies Chunk $N$ concurrently while generating Chunk $N+1$.
- If WER $> 0.08$, automatically regenerates with a new seed up to 4 attempts and saves the best attempt.

### 3. Honest Metrics & Evaluation
- Whisper is restricted strictly to Word Error Rate (WER) and Character Error Rate (CER).
- Real speaker similarity calculated using **SpeechBrain ECAPA-TDNN** 192-dimensional cosine similarity embeddings against the reference.
- Calculates and reports real-time factor (RTF: inference time / duration).

### 4. Controls Cleanup
- Replaced ambiguous temperature controls with a numeric **Seed input + Randomize toggle**.
- Speech Speed slider preserved; Pitch marked as experimental (`[exp]`) with similarity degradation warnings.
- Added Quality Mode selector: **Draft (10 ODE steps)** for previews vs. **Final (32 ODE steps)** for export.

### 5. CPU Optimization & Google Colab GPU Bridge
- **P-Core Optimization**: OpenMP threads clamped to physical P-cores (`VOICESTUDIO_NUM_THREADS=4`), avoiding E-core thrashing.
- **Google Colab GPU Bridge** (`scripts/colab_gpu_worker.ipynb`):
  - Connects to free NVIDIA Tesla T4 or A100 GPUs via Cloudflare Tunnel (`trycloudflare.com`).
  - Reduces 32-step ODE synthesis time from **1,186 seconds on CPU down to 4.68 seconds on GPU** (~250x speedup).
  - Live Colab GPU telemetry badge in top header (`🟣 GPU (T4): X%`).
  - Seamless automatic fallback: if Colab disconnects, VoiceStudio safely finishes on local CPU.

### 6. Safety, Attribution & Licensing
- Mandatory voice cloning consent gate in UI.
- Pretrained weights licensed under Creative Commons Non-Commercial (**CC-BY-NC-4.0**).
- Automated SQLite audit logging (`audit_records`) storing timestamp, reference audio SHA-256, and text SHA-256 for every synthesis.

### 7. Regression Test Suite
- Automated test suite in `tests/test_voice_regression.py` covering:
  - 3 reference clips (sample, Dr. Kalam exact, EU speech).
  - 5 regression test sentences.
  - Asserting average WER $\le 0.10$ and speaker similarity $\ge 0.35$ floor.

---

## Measured Performance Benchmarks

Tested on sentence: *"Hello! We are now synthesizing on the NVIDIA Tesla T4 GPU in Google Colab with thirty-two ODE steps."*

| Metric | Local Intel Core i5-13th Gen CPU | Google Colab NVIDIA Tesla T4 GPU | Measured Impact |
| :--- | :---: | :---: | :---: |
| **Inference Time (32 ODE steps)** | **1,186.7 s** (~19.7 min) | **4.68 s** | **~250x Speedup** |
| **Real-Time Factor (RTF)** | ~185.0 | **~1.03** | **Real-time generation** |
| **Speaker Similarity (ECAPA)** | `0.398` – `0.544` | **`0.717` (71.7%)** | **High acoustic fidelity** |
| **Completeness Gate WER** | `0.00%` | `0.00%` | **Zero skipped words** |

---

## Architecture & Graphify Knowledge Graph

VoiceStudio's full architecture is indexed in a navigable knowledge graph in [`graphify-out/`](graphify-out/):
- **Interactive Visual Graph**: [`graphify-out/graph.html`](graphify-out/graph.html)
- **Architecture Report**: [`graphify-out/GRAPH_REPORT.md`](graphify-out/GRAPH_REPORT.md)
- **GraphRAG JSON Schema**: [`graphify-out/graph.json`](graphify-out/graph.json)

```text
VoiceStudio/
├── frontend/               # React 19 + TypeScript + Vite + Tailwind CSS
│   ├── src/components/     # Studio UI, Header with live GPU badge, Wave animation
│   └── src/pages/          # Studio, Profiles, Models, Evaluation, Reports
├── backend/                # FastAPI application server
│   └── app/
│       ├── api/            # Endpoints (/synthesis, /profiles, /models, /monitoring)
│       ├── audio/          # Text normalizer, Whisper transcription, DSP audio processor
│       ├── database/       # SQLite schema, Session & AuditRecord logger
│       ├── evaluation/     # Levenshtein WER/CER & SpeechBrain ECAPA-TDNN similarity
│       └── monitoring/     # Live CPU, RAM, Disk & Colab GPU telemetry
├── ml/                     # ML inference engine, reference cache & remote GPU client
├── scripts/                # Colab GPU worker notebook & benchmarks
│   └── colab_gpu_worker.ipynb
├── graphify-out/           # Rebuilt 1204-node architecture knowledge graph
├── docs/                   # Architecture, API, Benchmarks & User Guides
└── tests/                  # Backend smoke tests & voice regression test suite
```

---

## Quick Start

### 1. Prerequisites
- Windows 11
- Python 3.10+ (Python 3.14 supported)
- Node.js 18+

### 2. Backend Setup
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# Start backend server (port 8000)
.\.venv\Scripts\python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Frontend Setup
```powershell
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`.

### 4. Optional: Enable Google Colab T4 GPU
1. Open [`scripts/colab_gpu_worker.ipynb`](scripts/colab_gpu_worker.ipynb) in Google Colab.
2. Select **Runtime** > **Change runtime type** > **T4 GPU**.
3. Run all cells (`Ctrl + F9`).
4. Copy the printed `https://xxxx.trycloudflare.com` URL into `.env` as `VOICESTUDIO_REMOTE_GPU_URL`.
5. The UI will show the `🟣 GPU (T4): X%` badge and run all generations on GPU in ~4.6 seconds!

---

## Safety and Licensing Notice

> [!IMPORTANT]
> **F5-TTS Weights Licensing**: The F5-TTS pretrained model weights are licensed under **Creative Commons Attribution-NonCommercial 4.0 International (CC-BY-NC-4.0)**. They are intended strictly for non-commercial research, academic, and evaluation purposes. Application source code is MIT licensed.

- **Ethical Voice Cloning & Consent**: Explicit user consent is required before synthesis.
- **Audit Logging**: Every generation cryptographically hashes the reference audio and target text into the SQLite `audit_records` table.
- **Attribution**: All shared outputs imitating real persons must be labeled as **"AI-generated synthetic voice"**.
