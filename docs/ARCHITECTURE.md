# VoiceStudio — System Architecture

## 1. Architectural Overview

VoiceStudio follows a strict layered architecture with decoupled modules:

```text
+--------------------------------------------------------------+
|                Presentation Layer (Web UI)                   |
|  React 19 + TypeScript + Vite + Tailwind CSS + Wavesurfer    |
+--------------------------------------------------------------+
                               | (HTTP / REST)
+--------------------------------------------------------------+
|                     API Layer (FastAPI)                      |
|  Endpoints: /profiles, /synthesis, /models, /monitoring      |
+--------------------------------------------------------------+
                               |
+--------------------------------------------------------------+
|                   Application & Service Layer                |
|  ProfileService, SynthesisService, AudioProcessor            |
+--------------------------------------------------------------+
            |                                      |
+-------------------------+              +---------------------+
|    ML Inference Layer   |              |  Evaluation Engine  |
|  IndicF5 Voice Cloning  |              |  Levenshtein WER/CER|
|  Reference Conditioning |              |  Speaker Cosine Sim |
+-------------------------+              +---------------------+
            |                                      |
+--------------------------------------------------------------+
|                      Data & Storage Layer                    |
|  SQLite DB (WAL Mode) + Local Filesystem (/data/outputs)     |
+--------------------------------------------------------------+
```

## 2. Component Details

1. **Presentation Layer**: Built with React 19, TypeScript, Vite, Tailwind CSS, and Lucide React. Features all 12 navigation sections from Image 1.
2. **API Layer**: FastAPI application exposing validated endpoints with Pydantic v2 schemas and static file serving for audio playback.
3. **Audio Processing**: High-performance DSP routines for inspecting headers, sample rate resampling, channel normalization, clipping detection, and SNR estimation.
4. **Voice Cloning Engine**: Reference-conditioned speech synthesis modulating fundamental frequencies, glottal harmonics, and spectral timbre derived from reference audio.
5. **Evaluation Engine**: Independent text-adherence testing via Levenshtein DP alignment (WER and CER) and speaker similarity calculation via cosine distance on acoustic feature embeddings.
6. **Data Management**: SQLite metadata persistence for voice profiles, reference transcripts, and historical synthesis jobs.
