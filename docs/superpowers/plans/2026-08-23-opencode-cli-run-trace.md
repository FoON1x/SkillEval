# opencode CLI Run + Trace Capture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let users run a real opencode CLI skill from a frontend page with custom prompt + skill selection, streaming live events via SSE, then persist the captured trace and navigate to its detail page.

**Architecture:** Rewrite the opencode ingest adapter to consume opencode's real JSONL event stream (`opencode run --format json`) as the single source of truth for event→Trace mapping. Add an SSE runner endpoint that spawns the CLI subprocess, streams events, then enriches the final Trace via `opencode export`. Add a React RunPage that POSTs to the SSE endpoint and renders the live event stream.

**Tech Stack:** Python 3.12 / FastAPI / Pydantic v2 / SQLAlchemy (backend); React 19 / TS / Vite / Tailwind v4 (frontend); opencode CLI 1.18.21 (`opencode run --format json`); SSE over `text/event-stream`.

## Global Constraints

- Backend tests run in `apps/api` with `uv run pytest` (pythonpath=`["."]`). TDD: failing test → impl → pass → commit.
- Frontend tests run in `apps/web` with `npm test` (vitest). No lint script; typecheck via `npx tsc -b`.
- Schema single source of truth: `apps/api/skill_eval/core/schema.py` (Pydantic). Never hand-edit `apps/web/src/api/types.generated.ts`.
- OpenAPI sync flow (manual): `uv run python scripts/export_openapi.py ../web/openapi.json` then `npx openapi-typescript openapi.json -o src/api/types.generated.ts`.
- opencode real JSONL event types: `step_start`, `text`, `tool_use`, `step_finish`. `timestamp` is epoch ms. `tool_use.part.state` has `status/input/output/metadata{exit}/title/time{start,end}`. Failed tools still report `status:"completed"`; error is in `metadata.exit!=0`.
- `opencode export <sessionID>` returns JSON `{info:{id,title,agent,model:{id,providerID},cost,tokens,time{created,updated},version}}`.
- No SSE infrastructure exists yet in the codebase; introduce `StreamingResponse`.

---

## File Structure

**Backend (apps/api/skill_eval/):**
- `ingest/adapters/opencode.py` — **rewrite**: `OpencodeImporter.parse(raw)` consumes real JSONL; new `TraceBuilder` class for incremental feeding. One file, two entry points sharing one mapping core.
- `runner/opencode.py` — **rewrite**: `OpencodeRunner.run_stream(ctx, emit)` spawns subprocess, reads JSONL lines, feeds builder, runs export, returns Trace.
- `runner/base.py` — **modify**: add `run_stream` to `BaseRunner` (default raises NotImplementedError); add `skill_name`, `cwd`, `auto`, `timeout` to `RunContext`.
- `runner/api.py` — **modify**: add `POST /api/runner/run/stream` (SSE) + `GET /api/runner/skills`.
- `runner/skills.py` — **create**: scan skill dirs, parse SKILL.md frontmatter.
- `tests/fixtures/opencode_ls.jsonl` — **created** (real-ish JSONL fixture).
- `tests/fixtures/opencode_export.json` — **created** (export fixture).
- `tests/test_ingest.py` — **modify**: replace `TestOpencodeAdapter` with real-format tests.
- `tests/test_runner.py` — **modify**: replace 501 test with run_stream + SSE tests.

**Frontend (apps/web/src/):**
- `pages/RunPage.tsx` — **create**: form (skill/agent/cwd/auto/prompt) + live SSE event view.
- `pages/RunPage.test.tsx` — **create**: vitest for form + streaming.
- `router.tsx` — **modify**: add `/run` route.
- `App.tsx` — **modify**: add nav entry "运行".

**Docs:**
- `docs/SCHEMA.md` §7, `docs/PROGRESS.md`, `README.md`, `AGENTS.md` — **modify**: reflect real format + landed feature.

---

### Task 1: Rewrite OpencodeImporter for real JSONL + TraceBuilder

**Files:**
- Rewrite: `apps/api/skill_eval/ingest/adapters/opencode.py`
- Modify: `apps/api/tests/test_ingest.py` (replace `TestOpencodeAdapter`)
- Test fixtures: `tests/fixtures/opencode_ls.jsonl`, `tests/fixtures/opencode_export.json`

**Interfaces:**
- Produces: `OpencodeImporter.parse(raw: dict) -> Trace` where `raw = {session_id?, skill_name?, events: [jsonl_line_dict...]}`.
- Produces: `OpencodeImporter.new_builder(skill_name: str | None) -> TraceBuilder` where `TraceBuilder.feed(event: dict) -> dict | None` (returns canonical event dict for SSE) and `TraceBuilder.finalize(export_info: dict | None = None) -> Trace`.

- [ ] **Step 1: Write failing tests** replacing `TestOpencodeAdapter` in `test_ingest.py` using the JSONL fixture.

- [ ] **Step 2: Run tests to verify they fail** — `uv run pytest tests/test_ingest.py -v`

- [ ] **Step 3: Rewrite `opencode.py`** with real JSONL mapping + `TraceBuilder`.

- [ ] **Step 4: Run tests to verify pass**

- [ ] **Step 5: Commit** — `feat(ingest): rewrite opencode adapter for real JSONL event stream`

### Task 2: Rewrite OpencodeRunner.run_stream()

**Files:**
- Rewrite: `apps/api/skill_eval/runner/opencode.py`
- Modify: `apps/api/skill_eval/runner/base.py` (RunContext fields + run_stream)
- Modify: `apps/api/tests/test_runner.py`

**Interfaces:**
- Produces: `OpencodeRunner.run_stream(ctx: RunContext, emit: Callable[[dict], None]) -> Trace`.
- Produces: `RunContext` gains `skill_name: str|None`, `auto: bool=True`, `timeout: int=300`.

- [ ] **Step 1: Write failing tests** with monkeypatched subprocess + export.

- [ ] **Step 2: Run to verify fail**

- [ ] **Step 3: Implement run_stream + base.py changes**

- [ ] **Step 4: Run to verify pass**

- [ ] **Step 5: Commit** — `feat(runner): implement opencode run_stream with subprocess + export enrich`

### Task 3: Add SSE endpoint + skills endpoint

**Files:**
- Modify: `apps/api/skill_eval/runner/api.py`
- Create: `apps/api/skill_eval/runner/skills.py`
- Modify: `apps/api/tests/test_runner.py`

**Interfaces:**
- Produces: `POST /api/runner/run/stream` (StreamingResponse, SSE frames `data: {json}\n\n`).
- Produces: `GET /api/runner/skills` → `{skills: [{name, description, source}]}`.

- [ ] **Step 1: Write failing tests** for SSE (TestClient) + skills list.

- [ ] **Step 2: Run to verify fail**

- [ ] **Step 3: Implement SSE endpoint + skills scanner**

- [ ] **Step 4: Run to verify pass**

- [ ] **Step 5: Commit** — `feat(runner): add SSE run endpoint + skills list`

### Task 4: Regenerate OpenAPI types

**Files:**
- Regenerate: `apps/web/openapi.json`, `apps/web/src/api/types.generated.ts`

- [ ] **Step 1: Export OpenAPI** — `uv run python scripts/export_openapi.py ../web/openapi.json`
- [ ] **Step 2: Generate TS types** — `npx openapi-typescript openapi.json -o src/api/types.generated.ts`
- [ ] **Step 3: Commit** — `chore: regenerate openapi types for runner SSE/skills`

### Task 5: Frontend RunPage + route + nav

**Files:**
- Create: `apps/web/src/pages/RunPage.tsx`, `apps/web/src/pages/RunPage.test.tsx`
- Modify: `apps/web/src/router.tsx`, `apps/web/src/App.tsx`

- [ ] **Step 1: Write failing RunPage test** (form render + mock SSE).
- [ ] **Step 2: Run to verify fail** — `npm test`
- [ ] **Step 3: Implement RunPage + route + nav**
- [ ] **Step 4: Run to verify pass** — `npm test` + `npx tsc -b`
- [ ] **Step 5: Commit** — `feat(web): add Run page with live opencode SSE streaming`

### Task 6: Update docs + full verification

- [ ] Update `docs/SCHEMA.md` §7, `docs/PROGRESS.md`, `README.md`, `AGENTS.md`
- [ ] `uv run pytest` (full backend) + `npm test` + `npx tsc -b`
- [ ] Commit — `docs: update for opencode CLI run + real JSONL format`
