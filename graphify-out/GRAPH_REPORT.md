# Graph Report - project2  (2026-11-16)

## Corpus Check
- 96 files · ~47,687 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 16 file(s) not represented in the graph (top: (none) 11, .css 2, .csv 1)

## Summary
- 1204 nodes · 2312 edges · 67 communities (38 shown, 29 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 192 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `974bf87a`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Voice Profile Service
- Studio UI & Wave Canvas
- Core Module 2
- Studio UI & Wave Canvas
- Voice Profile Service
- inference_engine.py
- Core Module 6
- Core Module 7
- Studio UI & Wave Canvas
- Studio UI & Wave Canvas
- Studio UI & Wave Canvas
- Studio UI & Wave Canvas
- Communities (57 total, 32 thin omitted)
- Studio UI & Wave Canvas
- SynthesisService
- Audio & ML Verification Contracts
- Communities (57 total, 32 thin omitted)
- contracts.py
- AudioProcessor
- normalize_text_input
- Core Module 20
- Studio UI & Wave Canvas
- pathlib
- Core Module 23
- Audio DSP & Validation
- main.py
- Core Module 26
- Audio DSP & Validation
- endpoints/models.py
- VoiceCloningEngine
- Studio UI & Wave Canvas
- Core Module 32
- Audio DSP & Validation
- monitoring.py
- Unit Verification Suite 35
- Core Module 36
- Core Module 37
- Synthesis Orchestration Service
- Core Module 39
- Core Module 40
- Core Module 41
- Studio UI & Wave Canvas
- Core Module 44
- Studio UI & Wave Canvas
- Graph Report - project2  (2026-11-15)
- Graph Report - project2  (2026-11-15)
- README.md
- VoiceStudio — High-Fidelity Local English Voice Cloning Workstation
- Core Module 51
- VoiceStudio CPU Optimization & Speed Benchmarks
- ReferenceCache
- ModelNotAvailableError
- 2. Reusable Skill: `voice-studio-graphify`
- VoiceStudio — Model Benchmark & Hardware Performance
- React + TypeScript + Vite
- _silent_info
- VoiceStudio — Test Execution Summary
- voice-studio-graphify
- model_config.py

## God Nodes (most connected - your core abstractions)
1. `AudioProcessor` - 34 edges
2. `DatabaseManager` - 30 edges
3. `create_test_api()` - 30 edges
4. `AudioValidator` - 28 edges
5. `TestAudioValidatorQualityGates` - 26 edges
6. `Communities (57 total, 32 thin omitted)` - 26 edges
7. `Communities (57 total, 32 thin omitted)` - 26 edges
8. `VoiceCloner` - 25 edges
9. `SerialTaskQueue` - 25 edges
10. `AudioProcessor` - 22 edges

## Surprising Connections (you probably didn't know these)
- `Suggested Questions` --references--> `TestAudioValidatorQualityGates`  [INFERRED]
  GRAPH_REPORT_2026-11-15_14-33-52.md → tests/unit/test_audio.py
- `Suggested Questions` --references--> `TestAudioValidatorQualityGates`  [INFERRED]
  graphify/graphify_report.md → tests/unit/test_audio.py
- `God Nodes (most connected - your core abstractions)` --references--> `ProfileService`  [INFERRED]
  GRAPH_REPORT_2026-11-15_14-33-52.md → backend/app/services/profile_service.py
- `God Nodes (most connected - your core abstractions)` --references--> `ProfileService`  [INFERRED]
  graphify/graphify_report.md → backend/app/services/profile_service.py
- `Surprising Connections (you probably didn't know these)` --references--> `SynthesisService`  [INFERRED]
  GRAPH_REPORT_2026-11-15_14-33-52.md → backend/app/services/synthesis_service.py

## Import Cycles
- 2-file cycle: `backend/app/database/models.py -> backend/app/database/session.py -> backend/app/database/models.py`

## Hyperedges (group relationships)
- **End-to-End Voice Cloning & Verification Pipeline** — frontend_src_pages_studiopage_studiopage, frontend_src_services_api_synthesisapi, backend_app_api_endpoints_synthesis_generate_speech, backend_app_services_synthesis_service_synthesisservice, ml_inference_engine_voicecloningengine, backend_app_evaluation_metrics_compute_wer [EXTRACTED 1.00]

## Communities (67 total, 29 thin omitted)

### Community 0 - "Voice Profile Service"
Cohesion: 0.06
Nodes (4): DatabaseManager, TestCrossFeatureFlows, TestDatabaseTier1, TestDatabaseTier2

### Community 1 - "Studio UI & Wave Canvas"
Cohesion: 0.12
Nodes (34): App(), readStoredTheme(), Theme, Header(), HeaderProps, Sidebar(), SidebarProps, WaveAnimation() (+26 more)

### Community 2 - "Core Module 2"
Cohesion: 0.06
Nodes (47): dependencies, axios@^1.21.1, clsx@^2.1.1, lucide-react@^1.73.0, react@^19.3.1, react-dom@^19.3.1, tailwind-merge@^3.7.0, @tailwindcss/vite@^4.3.5 (+39 more)

### Community 3 - "Studio UI & Wave Canvas"
Cohesion: 0.06
Nodes (7): add_security_headers(), worker_func(), FileIntegrityError, InvalidBindAddressError, StorageSecurity, TestStorageSecurityTier1, TestStorageSecurityTier2

### Community 4 - "Voice Profile Service"
Cohesion: 0.06
Nodes (11): client(), AsrEvaluator, create_test_api(), _execute_worker_job(), process_next_job(), submit_synthesis(), run_worker(), system_events() (+3 more)

### Community 5 - "inference_engine.py"
Cohesion: 0.10
Nodes (10): calculate_levenshtein(), compute_cer(), compute_speaker_similarity(), compute_wer(), normalize_text(), concat_chunks_with_crossfade(), _safe_torchaudio_load(), test_reference_whisper_transcription() (+2 more)

### Community 6 - "Core Module 6"
Cohesion: 0.08
Nodes (4): JobRecord, SerialTaskQueue, TestTaskQueueTier1, TestTaskQueueTier2

### Community 7 - "Core Module 7"
Cohesion: 0.06
Nodes (8): ModelNotLoadedError, SpeakerSimilarityMetrics, SpeakerVerification, SynthesisResult, VoiceCloner, TestParameterBoundsTier2, TestSpeakerVerificationContractsTier1, TestVoiceClonerContractsTier1

### Community 8 - "Studio UI & Wave Canvas"
Cohesion: 0.12
Nodes (13): async_client(), audio_synthesizer(), clean_wav_file(), clipped_wav_file(), corrupt_wav_file(), long_wav_file(), noisy_wav_file(), sample_audio_resolver() (+5 more)

### Community 12 - "Communities (57 total, 32 thin omitted)"
Cohesion: 0.08
Nodes (26): Communities (57 total, 32 thin omitted), Community 0 - "Voice Profile Service", Community 12 - "Studio UI & Wave Canvas", Community 14 - "Voice Profile Service", Community 15 - "Audio & ML Verification Contracts", Community 16 - "Audio & ML Verification Contracts", Community 18 - "Audio DSP & Validation", Community 19 - "Synthesis Orchestration Service" (+18 more)

### Community 14 - "SynthesisService"
Cohesion: 0.06
Nodes (28): create_profile(), delete_profile(), get_profile(), get_profiles(), update_profile(), cancel_synthesis(), delete_generation(), generate_speech() (+20 more)

### Community 15 - "Audio & ML Verification Contracts"
Cohesion: 0.17
Nodes (7): AudioClippingError, AudioSilentError, AudioTooLongError, AudioTooShortError, AudioValidationError, ExcessiveNoiseError, InvalidAudioFormatError

### Community 16 - "Communities (57 total, 32 thin omitted)"
Cohesion: 0.08
Nodes (26): Communities (57 total, 32 thin omitted), Community 0 - "Voice Profile Service", Community 12 - "Studio UI & Wave Canvas", Community 14 - "Voice Profile Service", Community 15 - "Audio & ML Verification Contracts", Community 16 - "Audio & ML Verification Contracts", Community 18 - "Audio DSP & Validation", Community 19 - "Synthesis Orchestration Service" (+18 more)

### Community 18 - "AudioProcessor"
Cohesion: 0.18
Nodes (4): transcribe_audio(), upload_audio(), AudioProcessor, test_reference_clips_exist_and_valid()

### Community 19 - "normalize_text_input"
Cohesion: 0.15
Nodes (11): _integer_to_words(), normalize_text_input(), _replace_currency(), _replace_date(), _replace_decimal(), _replace_number(), _replace_percent(), _replace_year() (+3 more)

### Community 20 - "Core Module 20"
Cohesion: 0.10
Nodes (19): compilerOptions, allowArbitraryExtensions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection (+11 more)

### Community 22 - "pathlib"
Cohesion: 0.15
Nodes (3): Settings, EvaluationMetrics, run_benchmark()

### Community 23 - "Core Module 23"
Cohesion: 0.17
Nodes (7): download_all(), fetch_librispeech_female(), fetch_librispeech_male(), fetch_ljspeech(), resample_and_save(), generate_all(), generate_speech_wave()

### Community 25 - "main.py"
Cohesion: 0.17
Nodes (5): get_whisper_model(), get_ecapa_classifier(), health_check(), on_startup(), _warmup_models()

### Community 26 - "Core Module 26"
Cohesion: 0.12
Nodes (16): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, noEmit, noFallthroughCasesInSwitch (+8 more)

### Community 29 - "endpoints/models.py"
Cohesion: 0.27
Nodes (3): get_models(), get_remote_gpu(), ModelAdapter

### Community 30 - "VoiceCloningEngine"
Cohesion: 0.18
Nodes (4): Surprising Connections (you probably didn't know these), Surprising Connections (you probably didn't know these), VoiceCloningEngine, _verify_audio()

### Community 32 - "Core Module 32"
Cohesion: 0.13
Nodes (7): AudioClippingError, AudioSilentError, AudioTooLongError, AudioTooShortError, ExcessiveNoiseError, InferenceTimeoutError, OutOfMemoryError

### Community 33 - "Audio DSP & Validation"
Cohesion: 0.26
Nodes (3): AudioProcessor, PreprocessedAudio, QualityValidationResult

### Community 34 - "monitoring.py"
Cohesion: 0.27
Nodes (3): get_system_metrics(), SystemMonitor, SystemMetricsResponse

### Community 35 - "Unit Verification Suite 35"
Cohesion: 0.31
Nodes (6): clean_speech_audio(), processor(), sample_rate_16k(), sample_rate_24k(), sample_rate_44k(), validator()

### Community 39 - "Core Module 39"
Cohesion: 0.33
Nodes (5): plugins, rules, react/only-export-components, react/rules-of-hooks, $schema

### Community 46 - "Graph Report - project2  (2026-11-15)"
Cohesion: 0.20
Nodes (9): Community Hubs (Navigation), Corpus Check, God Nodes (most connected - your core abstractions), Graph Report - project2  (2026-11-15), Hyperedges (group relationships), Import Cycles, Knowledge Gaps, Suggested Questions (+1 more)

### Community 48 - "Graph Report - project2  (2026-11-15)"
Cohesion: 0.20
Nodes (9): Community Hubs (Navigation), Corpus Check, God Nodes (most connected - your core abstractions), Graph Report - project2  (2026-11-15), Hyperedges (group relationships), Import Cycles, Knowledge Gaps, Suggested Questions (+1 more)

### Community 49 - "README.md"
Cohesion: 0.18
Nodes (9): FastAPI REST API Specification, VoiceStudio Layered System Architecture, Model Weights & Open-Source License Audit, F5-TTS v1 Base English CPU Model Selection, Multi-Tier Verification & Testing Strategy, VoiceStudio User & Synthesis Workflow Guide, Architecture Reference: 5-Layer Voice Cloning Blueprint, Release Gates Audit (+1 more)

### Community 50 - "VoiceStudio — High-Fidelity Local English Voice Cloning Workstation"
Cohesion: 0.20
Nodes (10): 1. Prerequisites, 2. Backend Setup, 3. Frontend Setup, Architecture, Documentation Links, Key Features, Quick Start, Running Automated Tests (+2 more)

### Community 57 - "VoiceStudio CPU Optimization & Speed Benchmarks"
Cohesion: 0.22
Nodes (8): Before vs After Comparison, Benchmark Design & Methodology, Draft Mode (10 ODE Steps — Fast Interactive Preview), Final Mode (18 ODE Steps — High-Fidelity Export), Measured Performance on 3 Test Sentences, Speedup & Quality Takeaways, System Environment, VoiceStudio CPU Optimization & Speed Benchmarks

### Community 59 - "ModelNotAvailableError"
Cohesion: 0.25
Nodes (4): load_model(), RemoteGpuRequest, set_remote_gpu(), ModelNotAvailableError

### Community 60 - "2. Reusable Skill: `voice-studio-graphify`"
Cohesion: 0.33
Nodes (5): 1. Overview, 2. Reusable Skill: `voice-studio-graphify`, Location:, Scanning and Updating Workflow:, VoiceStudio — Graphify Knowledge Graph & Skill Documentation

### Community 61 - "VoiceStudio — Model Benchmark & Hardware Performance"
Cohesion: 0.40
Nodes (4): 1. Test Environment, 2. Synthesis Performance Metrics, 3. Audio & Independent Accuracy Metrics, VoiceStudio — Model Benchmark & Hardware Performance

### Community 62 - "React + TypeScript + Vite"
Cohesion: 0.50
Nodes (3): Expanding the Oxlint configuration, React Compiler, React + TypeScript + Vite

### Community 64 - "VoiceStudio — Test Execution Summary"
Cohesion: 0.50
Nodes (3): 1. Test Suite Results, 2. Test Execution Commands, VoiceStudio — Test Execution Summary

### Community 65 - "voice-studio-graphify"
Cohesion: 0.50
Nodes (3): Instructions, Purpose, voice-studio-graphify

## Knowledge Gaps
- **4 isolated node(s):** `voicestudio`, `Model Weights & Open-Source License Audit`, `Architecture Reference: 5-Layer Voice Cloning Blueprint`, `Multi-Tier Verification & Testing Strategy`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 522 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **29 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DatabaseManager` connect `Voice Profile Service` to `Voice Profile Service`, `Studio UI & Wave Canvas`, `Graph Report - project2  (2026-11-15)`, `Graph Report - project2  (2026-11-15)`, `contracts.py`?**
  _High betweenness centrality (0.090) - this node is a cross-community bridge._
- **Are the 4 inferred relationships involving `AudioProcessor` (e.g. with `AudioValidator` and `InvalidAudioFormatError`) actually correct?**
  _`AudioProcessor` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `voicestudio`, `Model Weights & Open-Source License Audit`, `Architecture Reference: 5-Layer Voice Cloning Blueprint` to the rest of the system?**
  _4 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Voice Profile Service` be split into smaller, more focused modules?**
  _Cohesion score 0.06349206349206349 - nodes in this community are weakly interconnected._
- **Why does `God Nodes (most connected - your core abstractions)` connect `Graph Report - project2  (2026-11-15)` to `Voice Profile Service`, `Voice Profile Service`, `Core Module 6`, `Core Module 7`, `Studio UI & Wave Canvas`, `SynthesisService`, `Audio DSP & Validation`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Are the 5 inferred relationships involving `DatabaseManager` (e.g. with `God Nodes (most connected - your core abstractions)` and `God Nodes (most connected - your core abstractions)`) actually correct?**
  _`DatabaseManager` has 5 INFERRED edges - model-reasoned connections that need verification._
- **Should `Studio UI & Wave Canvas` be split into smaller, more focused modules?**
  _Cohesion score 0.11840120663650075 - nodes in this community are weakly interconnected._