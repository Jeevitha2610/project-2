# VoiceStudio — Graphify Knowledge Graph & Skill Documentation

## 1. Overview
VoiceStudio maintains a persistent Graphify architectural knowledge graph under `graphify/` detailing:
- Every UI view and interactive component
- Every FastAPI route and controller
- Every backend application service
- The local ML inference engine and model adapter
- Audio DSP and evaluation modules
- Database tables and storage locations
- Automated unit, integration, and E2E test suites

## 2. Reusable Skill: `voice-studio-graphify`

### Location:
`skills/voice-studio-graphify/SKILL.md`

### Scanning and Updating Workflow:
1. **Module Discovery**: Scan `backend/app/`, `frontend/src/`, `ml/`, and `tests/` for newly created or refactored files.
2. **Node Creation**: Add JSON object with `id`, `category`, `name`, and `file` to `graphify/nodes/nodes.json`.
3. **Edge Mapping**: Register dependencies (`USES`, `CALLS`, `PERSISTS_TO`, `TESTED_BY`) in `graphify/edges/edges.json`.
4. **Validation Check**: Verify that every referenced source and target exists; verify zero orphan nodes.
5. **Regenerate Report**: Update `graphify/graphify_report.md` with connectivity statistics and centrality hubs.
