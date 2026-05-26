# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository State

This is the **monorepo for the SIZL Agentic Brain Beta Test Automation Tool**. The repo is mid-transition: design docs in `docs/` describe the full system, while `apps/api/` currently holds the Phase 1 (W1) skeleton: FastAPI app, Pydantic schemas, Port ABCs + dummy adapters, and a signature-verifying `POST /webhooks` receiver (HMAC-SHA256 + event logging). Issue-creation / Sheets / LLM business logic is W2+. `apps/web/` and `packages/` are reserved but not populated.

The automation uses **two different GitHub repos**: **Issues** are created in **this repo** (`jykim-sizl/SIZL-AI-Agent-Beta-Test`) — the GitHub App is installed here and `issues` webhooks fire from here. **PRs / empty branches** target the shared team repo **`Neolab-test/test`**, which is what `.env`'s `GITHUB_TARGET_REPO` points to. `config.py`'s default `github_target_repo` (`Sizl-Neolab/SIZL-Agentic-Brain-Issue-Track`) is just a placeholder overridden by `.env`. (When testing webhooks, create the test issue in *this* repo, not the PR target.)

The current PRD is `docs/PRD_v4_0.*`; v3.0 and earlier are in `docs/history/`.

## What This System Does

Automates the feedback loop for an internal AI product beta test:

1. Beta testers enter their company email on a web form. Backend looks up the email in **Members** — unregistered or inactive emails are rejected (403). Name/team are auto-filled from the lookup.
2. Backend creates a **GitHub Issue** with structured labels.
3. **Bug issues only**: a webhook creates an empty branch + empty PR, and the LLM (Claude API) writes a root-cause hypothesis into the PR body. No code is written automatically.
4. Issue/PR state is mirrored to Google Sheets (Raw Bugs / Raw Enhancements / Daily Snapshot) in near-real-time and fully reconciled at 17:00 KST daily.
5. Slack summary posts daily at 17:05 KST.

## Common Commands

All backend commands run from `apps/api/`:

```bash
cd apps/api

# Install dependencies (creates .venv/)
uv venv
uv pip install -e ".[dev]"

# Run dev server (hot reload on src/)
.venv/bin/uvicorn src.main:app --reload
# → http://localhost:8000/health, /docs

# Tests
.venv/bin/pytest                              # all tests (pytest-asyncio auto mode)
.venv/bin/pytest tests/test_foo.py::test_bar  # single test
.venv/bin/pytest -k "member"                  # by name pattern

# Lint + typecheck
.venv/bin/ruff check src/ tests/
.venv/bin/ruff format src/ tests/
.venv/bin/mypy src/                           # strict mode (see pyproject.toml)

# Docker (for parity with Phase B deploy target)
docker build -t sizl-beta-api .
docker run --env-file .env -p 8000:8000 sizl-beta-api
```

Required env vars are declared in `apps/api/src/core/config.py` (loaded via pydantic-settings from `apps/api/.env`). Missing any of them will fail app startup.

## Architecture

**Hexagonal (Ports & Adapters) + event-driven.** Strict top-down dependency:

```
api/        FastAPI routers — thin, only HTTP concerns
  ↓
services/   business logic; imports ABC ports only, never concrete adapters
  ↓
adapters/   concrete integrations (GitHub, Anthropic, Sheets, Slack)
```

Cross-cutting: `core/` (config, logging, exceptions), `models/` (Pydantic DTOs).

### Non-obvious rules (read before editing)

- **Services depend on ABCs, never on adapters.** `GitHubPort`, `LLMPort`, `SheetPort`, `NotifierPort` live alongside the services that consume them. Adapters implement them. This is what makes unit tests possible (mocks injected via the ABC) and lets services be extracted as workers later.
- **Member validation runs first on every form submission.** Reject before any other side effect. Inactive members (E column = FALSE) are treated the same as unregistered.
- **Members lookup is from a local `apps/api/data/Members.xlsx` for the beta period**, not from Google Sheets. Schema: 이름 / 팀 / 이메일 (no 직급 in v4.1). The file is gitignored (`*.xlsx`); see `apps/api/data/readmd.md`.
- **Enhancement-type issues skip the LLM and PR pipeline entirely.** Only `bug` label triggers LLM analysis + empty-branch PR creation. Enhancements are recorded to the sheet and that's it. (ADR-006)
- **Auto-generated PRs are always empty.** The LLM writes a root-cause hypothesis into the PR body — never into code. Branch protection requires at least one human review before merge.
- **Operator columns in Google Sheets are never overwritten.** In Raw Bugs / Raw Enhancements, columns L–P and S are human-edited; automation only touches A–K, Q–R, T–AC. Sheet writes must be idempotent.
- **Four sheets, not one Raw Issues.** Per ADR-003: `Raw Bugs`, `Raw Enhancements`, `Daily Snapshot`, `Dashboard`. The `SheetPort` exposes `append_bug` / `append_enhancement` separately rather than a single `append_issue`.
- **Phase A vs Phase B deployment.** Phase A (current, through W3) = local docker / `pnpm dev`. Phase B (W3+) = Cloud Run + Vercel. Don't add Cloud Run-specific config to Phase A code paths. (ADR-001)
- **Anthropic API key is not yet issued.** W3 LLM work must run with a stub `LLMPort` implementation; don't gate work on the real key.
- **`main` is branch-protected.** PRs into `main` must pass two required status checks — `API · ruff + pytest` and `API · docker build` (`.github/workflows/ci.yml` runs ruff + mypy + pytest + docker build). Renaming a CI job breaks the required-check mapping — update the protection contexts (`PUT /repos/.../branches/main/protection`) too. PRs are squash-merged.

### Core services

| Service | Responsibility |
|---|---|
| `MemberService` | Email → name/team from local Members.xlsx; raises 403 if missing/inactive |
| `IssueService` | Form + member → GitHub Issue body + labels |
| `LLMService` | Claude API → root-cause hypothesis (bug only); stubbed until key arrives |
| `PRService` | Empty branch + empty PR with LLM analysis in body (bug only) |
| `SheetService` | Idempotent append/update against Raw Bugs / Raw Enhancements; preserves operator columns |
| `SyncService` | Daily 17:00 KST reconciliation GitHub ↔ Sheets + Daily Snapshot append |

### Tech stack (locked-in choices)

- Python 3.12 + FastAPI + Pydantic v2; `uv` for env/deps
- `anthropic` SDK, default model `claude-sonnet-4-6`
- `PyGithub` + `httpx` (httpx needed for Tree API / GraphQL paths PyGithub doesn't cover)
- `google-api-python-client` (gspread alone is insufficient — `batchUpdate` is required for sheet writes)
- `structlog` JSON logger (configured in `core/logging.py`)
- `pytest` + `pytest-asyncio` (auto mode); adapters mocked via ABC
- Frontend (not yet scaffolded): Next.js 15 App Router + Zod + React Hook Form
- Scheduler: GitHub Actions cron (`infra/github-actions/daily-sync.yml`) hits `/sync`

## Working with the design docs

`docs/` contains `.docx` and `.pdf` (Korean). DOCX is a ZIP — extract text with:

```bash
python3 -c "
import zipfile, re
with zipfile.ZipFile('docs/<file>.docx', 'r') as z:
    with z.open('word/document.xml') as f:
        text = re.sub(r'<[^>]+>', ' ', f.read().decode('utf-8'))
        print(re.sub(r'\s+', ' ', text).strip())
"
```

PDF reading needs `poppler` (`brew install poppler`), which may not be installed.

| Doc | Contents |
|---|---|
| `PRD_v4_0` | Current product requirements, feature list, release plan |
| `시스템_아키텍처_상세설계서_v1.0` | Component specs, data models, sequence diagrams, API contracts |
| `기술스택_명세서_v1.0` | Tech choices with rationale and rejected alternatives |
| `베타테스트_도구_구현계획서_v2.0` | Weekly delivery plan (W0–W4) |
| `베타테스트_도구_개발계획서_v2.0` | Earlier overview: components, data flow, Sheets schema |
| `docs/history/` | Superseded drafts (PRD v1.1/v2.0/v3.0; impl plan v1.0) |
