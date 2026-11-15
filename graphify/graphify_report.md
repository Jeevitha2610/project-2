# VoiceStudio — Graphify Architecture Knowledge Graph Report

## 1. Summary Statistics
* **Total Nodes**: 30
* **Total Edges**: 28
* **Orphan Nodes**: 0 (All components are connected)
* **Categories**: UI Pages, Frontend Components, API Routes, Backend Services, Audio Modules, Evaluation Modules, ML Engine, Database Entities, Storage Locations, Test Suites.

## 2. Key Hubs (Highest In-Degree / Out-Degree)
1. **Frontend API Client (`frontend_api_client`)**: Central bridge between presentation UI pages and backend FastAPI endpoints.
2. **Synthesis Service (`service_synthesis`)**: Orchestrates ML inference engine, SQLite job persistence, and independent evaluation metrics.
3. **Audio Processor (`audio_processor`)**: Core DSP engine utilized by reference validation, profile creation, and ML synthesis.
4. **Voice Cloning Engine (`ml_inference_engine`)**: Execution hub for acoustic timbre conditioning and WAV output generation.

## 3. Dependency Validation
* All referenced target files exist in the project repository.
* All API endpoints resolve to concrete backend handlers.
* All data entities map directly to SQLAlchemy ORM models and SQLite schemas.
