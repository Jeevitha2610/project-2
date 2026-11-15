# VoiceStudio — User Guide

Welcome to **VoiceStudio**, the local-first English voice cloning workstation for Windows 11.

## Getting Started

### 1. Launching VoiceStudio
1. Open terminal in the project root.
2. Start the Backend API:
   ```powershell
   .\.venv\Scripts\uvicorn.exe backend.app.main:app --host 127.0.0.1 --port 8000
   ```
3. Start the Frontend Dashboard:
   ```powershell
   cd frontend
   npm run dev
   ```
4. Open your browser to `http://localhost:5173`.

---

## 2. Voice Cloning Workflow

1. **Select or Upload a Reference Voice**:
   - In the Studio view, click on **Reference Voice**.
   - Upload a clean 3-10 second English speech recording (`.wav` or `.mp3`).
   - Enter or verify the **Reference Transcript** corresponding to what is spoken in the audio.
2. **Configure Voice Synthesis**:
   - Type your desired sentence in the **Target Text** box.
   - Adjust **Speech Speed** (default `1.0x`), **Pitch** (`0.0`), and **Temperature** (`0.7`).
   - Select your desired output format (default `WAV (Lossless)`).
3. **Generate Speech**:
   - Click the large gradient **Generate Speech** button.
   - The engine conditions the model on your reference audio and synthesizes the speech on your CPU.
4. **Playback & Verification**:
   - Listen to the synthesized waveform directly in the audio player.
   - Review the independent evaluation metrics:
     - **Word Error Rate (WER)**: Text adherence score.
     - **Character Error Rate (CER)**: Character-level accuracy.
     - **Speaker Similarity**: Cosine similarity comparing voice acoustic features.
   - Click the Download icon to save the WAV file.
