# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is a **documentation-only** repository containing design artifacts for the **SIZL Agentic Brain Beta Test Automation Tool**. All files are in `docs/` as `.docx` and `.pdf`. There is no source code here; the implementation lives in a separate monorepo (`sizl-beta-tool`).

The target GitHub repository for issues is `Sizl-Neolab/SIZL-Agentic-Brain-Issue-Track`.

## What This System Does

Automates the feedback loop for an internal AI product beta test:

1. Beta testers enter their company email on the web form. The backend looks up the email in the **Members sheet** — unregistered emails are rejected (403). Name and team are fetched automatically from the same sheet.
2. Backend creates a **GitHub Issue** automatically with structured labels. Submitter name and team are populated from the Members sheet lookup.
3. A **Webhook triggers**: an empty branch and empty PR are created automatically. LLM (Claude API) analyzes the issue and writes a root-cause hypothesis into the PR body. **No code changes are made automatically** — developers fill in the code themselves.
4. Issue/PR state is **mirrored to Google Sheets** (Raw Issues + Daily Snapshot) in near-real-time and fully reconciled at 17:00 KST daily.
5. A **Slack summary** is posted daily at 17:05 KST; failures alert within 5 minutes.

## Document Index

| File | Contents |
|---|---|
| `PRD_v3.0` | Product requirements, user stories, feature list (P1–P3), release plan (W1–W4) |
| `시스템_아키텍처_상세설계서_v1.0` | Component specs, data models, sequence diagrams, API contracts, deployment topology |
| `기술스택_명세서_v1.0` | Per-component tech selection with rationale and rejected alternatives |
| `베타테스트_도구_구현계획서_v2.0` | Weekly delivery plan (W0–W4), directory structure, pre-conditions |
| `베타테스트_도구_개발계획서_v2.0` | Earlier overview covering components, data flow, Sheets schema |
| `docs/history/` | Superseded drafts (v1.1, v2.0 PRD; v1.0 implementation plan) |

## Planned System Architecture

The implementation follows **Hexagonal (Ports & Adapters)** combined with **Event-Driven** design.

### Layer Structure (strict top-down dependency)

```
Frontend (Next.js)
    └── API Layer (FastAPI routers)
            └── Service Layer (business logic, depends only on ABCs)
                    └── Adapter Layer (concrete external integrations)
```

### Monorepo Layout (`sizl-beta-tool/`)

```
apps/
  api/src/
    api/          # FastAPI routers: issues.py, webhooks.py, health.py
    services/     # issue/, llm/, sheet/, github/ — each isolatable as a worker
    adapters/     # github_adapter.py, anthropic_adapter.py, sheets_adapter.py
    core/         # config.py, logging.py, auth.py, exceptions.py
    models/       # Pydantic schemas / DTOs
  web/            # Next.js form UI
packages/
  shared-schemas/ # Pydantic + Zod schemas (kept in sync)
infra/
  github-actions/ # deploy-api.yml, deploy-web.yml, daily-sync.yml (17:00 KST cron)
```

### Key Architectural Rules

- **Service Layer never imports a concrete adapter.** All external systems (GitHub, Claude, Sheets, Slack) are injected via ABC interfaces (`GitHubPort`, `LLMPort`, `SheetPort`, `NotifierPort`). This enables unit testing with mocks and future worker extraction.
- **Operator-written columns (L–P, S) in Google Sheets are never overwritten by automation.** Auto-managed columns are A–K, Q–R, T–AC.
- **Member validation happens before everything else.** Every form submission is checked against the Members sheet. Inactive or unregistered emails are rejected immediately.
- **Auto-generated PRs are always empty branches** — the system never writes code automatically. LLM analysis (root-cause hypothesis) is written into the PR body as context for the developer.
- **Auto-generated PRs require at least one human review before merge** (GitHub branch protection rule).

### Core Services

| Service | Responsibility |
|---|---|
| `MemberService` | Look up member by email in Members sheet. Returns name/team/position or raises 403 if not found or inactive |
| `IssueService` | Form + member info → GitHub Issue body (Markdown) + label assignment |
| `LLMService` | Claude API → root-cause hypothesis → write analysis into PR body |
| `PRService` | Empty branch + empty PR creation with LLM analysis in body |
| `SheetService` | Row append/update with in-memory index cache; idempotent. Never overwrites operator columns (L–P, S) |
| `SyncService` | Daily full reconciliation of GitHub ↔ Sheets + Daily Snapshot append |

### Tech Stack Summary

| Area | Choice |
|---|---|
| Backend | Python 3.12 + FastAPI 0.115 + Pydantic v2 + uvicorn |
| HTTP client | httpx (async/sync, used for Slack & supplemental GitHub calls) |
| GitHub | PyGithub 2.5 + httpx for Tree API / GraphQL |
| LLM | `anthropic` SDK 0.40+; default model `claude-sonnet-4-6` |
| Sheets | `google-api-python-client` 2.150 (batchUpdate required; gspread alone insufficient) |
| Package mgr | `uv` (Python), `pnpm` workspaces (Node) |
| Linting | `ruff` + `mypy` (Python); ESLint + Prettier (TypeScript) |
| Tests | `pytest` + `pytest-asyncio`; adapters are mocked via ABC |
| Frontend | Next.js 15 (App Router) + TypeScript 5.6 + Tailwind 4 + React Hook Form + Zod |
| Hosting | Cloud Run (Backend, min 1 instance) + Vercel (Frontend) |
| Secrets | Google Secret Manager — never in code or logs |
| Scheduler | GitHub Actions cron (`daily-sync.yml`) → calls `/sync` endpoint |
| DB | None in MVP; SQLite added in W4 for event log + row-index cache |

### Release Plan

| Release | Week | Key deliverables |
|---|---|---|
| R1 | W1 | Email-only form access, bug/enhancement form types, Raw Issues sheet |
| R2 | W2 | Env capture, clipboard image paste, GitHub Issue auto-creation, PR status sync |
| R3 | W3 | LLM analysis, empty branch + PR auto-creation, LLM analysis written to PR body |
| R4 | W4 | Full daily sync, Daily Snapshot, Dashboard, Slack daily report, rollback toggles |
| R5 | W4+1 | Public beta open to all testers |

## Working With This Repo

The documents are in Korean. To extract text for editing or review, use Python's `zipfile` module (DOCX files are ZIP archives):

```bash
python3 -c "
import zipfile, re
with zipfile.ZipFile('docs/<file>.docx', 'r') as z:
    with z.open('word/document.xml') as f:
        text = re.sub(r'<[^>]+>', ' ', f.read().decode('utf-8'))
        print(re.sub(r'\s+', ' ', text).strip())
"
```

PDF reading requires `poppler` (`brew install poppler`), which may not be installed.
