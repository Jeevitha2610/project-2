---
name: voice-studio-graphify
description: Reusable project skill to inspect VoiceStudio architecture, update nodes and edges in graphify, detect missing connections, and regenerate graph reports.
---

# voice-studio-graphify

## Purpose
This skill maintains the project knowledge graph representing VoiceStudio's components, services, models, database entities, and tests.

## Instructions

1. **Scan Project Modules**:
   Search for all new or modified code files across:
   - `frontend/src/`
   - `backend/app/`
   - `ml/`
   - `tests/`

2. **Update Nodes (`graphify/nodes/nodes.json`)**:
   Add or update node entries:
   ```json
   {
     "id": "<unique_snake_case_id>",
     "category": "<UI Page | Component | Route | Service | ML | Entity | Test>",
     "name": "<Human Readable Name>",
     "file": "<relative/file/path>"
   }
   ```

3. **Update Edges (`graphify/edges/edges.json`)**:
   Map interactions using allowed relation types:
   - `USES`, `CALLS`, `DEPENDS_ON`, `READS`, `WRITES`, `VALIDATES`, `GENERATES`, `TESTED_BY`, `CONFIGURED_BY`, `PERSISTS_TO`.

4. **Consistency Verification**:
   - Ensure every `source` and `target` in `edges.json` exists in `nodes.json`.
   - Ensure no node has degree 0 (orphan node).
   - Ensure every API route connects to a backend service and has a corresponding test.

5. **Regenerate Report**:
   Compile summary statistics, hub nodes, and verification findings into `graphify/graphify_report.md`.
