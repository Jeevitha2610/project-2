# Graph Report - project2  (2026-11-15)

## Corpus Check
- Corpus is ~42,727 words - fits in a single context window. You may not need a graph.

## Summary
- 1007 nodes · 1952 edges · 57 communities (25 shown, 32 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 155 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- Voice Profile Service
- Studio UI & Wave Canvas
- Core Module 2
- Studio UI & Wave Canvas
- Voice Profile Service
- F5-TTS Voice Cloning Engine
- Core Module 6
- Core Module 7
- Studio UI & Wave Canvas
- Studio UI & Wave Canvas
- Studio UI & Wave Canvas
- Studio UI & Wave Canvas
- Studio UI & Wave Canvas
- Studio UI & Wave Canvas
- Voice Profile Service
- Audio & ML Verification Contracts
- Audio & ML Verification Contracts
- Unit Verification Suite 17
- Audio DSP & Validation
- Synthesis Orchestration Service
- Core Module 20
- Studio UI & Wave Canvas
- CPU & RAM Telemetry
- Core Module 23
- Audio DSP & Validation
- SQLite ORM & Persistence
- Core Module 26
- Audio DSP & Validation
- F5-TTS Voice Cloning Engine
- Voice Profile Service
- Studio UI & Wave Canvas
- Core Module 32
- Audio DSP & Validation
- Unit Verification Suite 35
- Core Module 37
- Synthesis Orchestration Service
- Core Module 39
- Core Module 41
- Core Module 42
- Studio UI & Wave Canvas
- Core Module 44
- Core Module 46
- Core Module 48
- Core Module 49
- Core Module 50
- Core Module 51

## God Nodes (most connected - your core abstractions)
1. `AudioProcessor` - 34 edges
2. `AudioValidator` - 28 edges
3. `DatabaseManager` - 28 edges
4. `create_test_api()` - 28 edges
5. `VoiceCloner` - 23 edges
6. `SerialTaskQueue` - 23 edges
7. `TestAudioValidatorQualityGates` - 22 edges
8. `TestAudioProcessorDSP` - 19 edges
9. `compilerOptions` - 18 edges
10. `ProfileService` - 17 edges

## Surprising Connections (you probably didn't know these)
- `FastAPI REST API Specification` --references--> `generate_speech()`  [EXTRACTED]
  docs/API.md → backend/app/api/endpoints/synthesis.py
- `FastAPI REST API Specification` --references--> `create_profile()`  [EXTRACTED]
  docs/API.md → backend/app/api/endpoints/profiles.py
- `VoiceStudio Layered System Architecture` --references--> `SynthesisService`  [EXTRACTED]
  docs/ARCHITECTURE.md → backend/app/services/synthesis_service.py
- `VoiceStudio User & Synthesis Workflow Guide` --references--> `StudioPage()`  [EXTRACTED]
  docs/USER_GUIDE.md → frontend/src/pages/StudioPage.tsx
- `F5-TTS v1 Base English CPU Model Selection` --rationale_for--> `VoiceCloningEngine`  [EXTRACTED]
  docs/MODEL_SELECTION_REPORT.md → ml/inference_engine.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **End-to-End Voice Cloning & Verification Pipeline** — frontend_src_pages_studiopage_studiopage, frontend_src_services_api_synthesisapi, backend_app_api_endpoints_synthesis_generate_speech, backend_app_services_synthesis_service_synthesisservice, ml_inference_engine_voicecloningengine, backend_app_evaluation_metrics_compute_wer [EXTRACTED 1.00]

## Communities (57 total, 32 thin omitted)

### Community 0 - "Voice Profile Service"
Cohesion: 0.06
Nodes (4): DatabaseManager, TestCrossFeatureFlows, TestDatabaseTier1, TestDatabaseTier2

### Community 1 - "Studio UI & Wave Canvas"
Cohesion: 0.12
Nodes (35): VoiceStudio User & Synthesis Workflow Guide, App(), readStoredTheme(), Theme, Header(), HeaderProps, Sidebar(), SidebarProps (+27 more)

### Community 2 - "Core Module 2"
Cohesion: 0.06
Nodes (47): dependencies, axios@^1.21.1, clsx@^2.1.1, lucide-react@^1.73.0, react@^19.3.1, react-dom@^19.3.1, tailwind-merge@^3.7.0, @tailwindcss/vite@^4.3.5 (+39 more)

### Community 3 - "Studio UI & Wave Canvas"
Cohesion: 0.06
Nodes (6): add_security_headers(), worker_func(), InvalidBindAddressError, StorageSecurity, TestStorageSecurityTier1, TestStorageSecurityTier2

### Community 4 - "Voice Profile Service"
Cohesion: 0.06
Nodes (10): AsrEvaluator, create_test_api(), _execute_worker_job(), process_next_job(), submit_synthesis(), run_worker(), system_events(), transcribe_audio() (+2 more)

### Community 5 - "F5-TTS Voice Cloning Engine"
Cohesion: 0.07
Nodes (12): calculate_levenshtein(), compute_cer(), compute_speaker_similarity(), compute_wer(), extract_acoustic_embedding(), normalize_text(), VoiceStudio Layered System Architecture, F5-TTS v1 Base English CPU Model Selection (+4 more)

### Community 6 - "Core Module 6"
Cohesion: 0.09
Nodes (4): JobRecord, SerialTaskQueue, TestTaskQueueTier1, TestTaskQueueTier2

### Community 7 - "Core Module 7"
Cohesion: 0.08
Nodes (5): ModelNotLoadedError, SynthesisResult, VoiceCloner, TestParameterBoundsTier2, TestVoiceClonerContractsTier1

### Community 8 - "Studio UI & Wave Canvas"
Cohesion: 0.11
Nodes (14): async_client(), audio_synthesizer(), clean_wav_file(), client(), clipped_wav_file(), corrupt_wav_file(), long_wav_file(), noisy_wav_file() (+6 more)

### Community 12 - "Studio UI & Wave Canvas"
Cohesion: 0.15
Nodes (3): generate_speech_wave(), InvalidAudioFormatError, AudioValidator

### Community 14 - "Voice Profile Service"
Cohesion: 0.19
Nodes (8): create_profile(), delete_profile(), get_profile(), get_profiles(), update_profile(), VoiceProfile, ProfileService, FastAPI REST API Specification

### Community 15 - "Audio & ML Verification Contracts"
Cohesion: 0.14
Nodes (8): AudioClippingError, AudioFormatResult, AudioSilentError, AudioTooLongError, AudioTooShortError, AudioValidationError, ExcessiveNoiseError, QualityValidationResult

### Community 16 - "Audio & ML Verification Contracts"
Cohesion: 0.16
Nodes (3): SpeakerSimilarityMetrics, SpeakerVerification, TestSpeakerVerificationContractsTier1

### Community 18 - "Audio DSP & Validation"
Cohesion: 0.14
Nodes (4): transcribe_audio(), upload_audio(), AudioProcessor, consented_profile()

### Community 19 - "Synthesis Orchestration Service"
Cohesion: 0.22
Nodes (8): delete_generation(), generate_speech(), get_history(), GenerationJob, SynthesisRequest, SynthesisResponse, Config, SynthesisService

### Community 20 - "Core Module 20"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 22 - "CPU & RAM Telemetry"
Cohesion: 0.13
Nodes (5): get_system_metrics(), Settings, SystemMonitor, EvaluationMetrics, SystemMetricsResponse

### Community 23 - "Core Module 23"
Cohesion: 0.20
Nodes (6): download_all(), fetch_librispeech_female(), fetch_librispeech_male(), fetch_ljspeech(), resample_and_save(), generate_all()

### Community 25 - "SQLite ORM & Persistence"
Cohesion: 0.15
Nodes (4): init_db(), health_check(), on_startup(), setup_database()

### Community 26 - "Core Module 26"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 29 - "F5-TTS Voice Cloning Engine"
Cohesion: 0.18
Nodes (5): get_models(), load_model(), unload_model(), ModelNotAvailableError, ModelAdapter

### Community 30 - "Voice Profile Service"
Cohesion: 0.27
Nodes (6): get_db(), VoiceProfileBase, VoiceProfileCreate, VoiceProfileResponse, Config, VoiceProfileUpdate

### Community 32 - "Core Module 32"
Cohesion: 0.13
Nodes (7): AudioClippingError, AudioSilentError, AudioTooLongError, AudioTooShortError, FileIntegrityError, InferenceTimeoutError, OutOfMemoryError

### Community 35 - "Unit Verification Suite 35"
Cohesion: 0.31
Nodes (6): clean_speech_audio(), processor(), sample_rate_16k(), sample_rate_24k(), sample_rate_44k(), validator()

### Community 39 - "Core Module 39"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

## Knowledge Gaps
- **6 isolated node(s):** `voicestudio`, `F5-TTS v1 Base English CPU Model Selection`, `Multi-Tier Verification & Testing Strategy`, `VoiceStudio User & Synthesis Workflow Guide`, `Model Weights & Open-Source License Audit` (+1 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 402 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **32 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `SynthesisAPI` connect `Studio UI & Wave Canvas` to `Synthesis Orchestration Service`, `CPU & RAM Telemetry`, `Voice Profile Service`?**
  _High betweenness centrality (0.151) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `AudioProcessor` (e.g. with `AudioValidator` and `InvalidAudioFormatError`) actually correct?**
  _`AudioProcessor` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `voicestudio`, `F5-TTS v1 Base English CPU Model Selection`, `Multi-Tier Verification & Testing Strategy` to the rest of the system?**
  _6 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Voice Profile Service` be split into smaller, more focused modules?**
  _Cohesion score 0.06349206349206349 - nodes in this community are weakly interconnected._
- **Why does `create_profile()` connect `Voice Profile Service` to `Studio UI & Wave Canvas`, `Voice Profile Service`?**
  _High betweenness centrality (0.080) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `AudioValidator` (e.g. with `AudioProcessor` and `TestAudioValidatorQualityGates`) actually correct?**
  _`AudioValidator` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Should `Studio UI & Wave Canvas` be split into smaller, more focused modules?**
  _Cohesion score 0.11538461538461539 - nodes in this community are weakly interconnected._