# SIZL Agentic Brain — 베타테스트 자동화 도구

SIZL Agentic Brain 사내 베타테스트의 피드백 루프를 자동화하는 시스템입니다.

베타 테스터가 웹 폼으로 이슈를 제출하면, 시스템이 GitHub Issue를 자동 생성하고 LLM(Claude)이 원인을 분석해 PR 초안을 만듭니다. 처리 현황은 Google Sheets 대시보드에 실시간으로 반영되고, 매일 17시에 Slack으로 요약이 발송됩니다.

---

## 주요 기능

| 기능 | 설명 |
|---|---|
| 이슈 제출 폼 | 회사 이메일 한 줄로 접근, 클립보드 이미지 붙여넣기 지원 |
| GitHub Issue 자동 생성 | 폼 제출 즉시 라벨 포함 Issue 등록 |
| LLM 자동 분석 + PR 생성 | Claude API로 원인 분석 → confidence ≥ 0.5이면 PR 초안 자동 생성 |
| Google Sheets 동기화 | Webhook 실시간 반영 + 매일 17시 전수 동기화 |
| 일일 Slack 보고 | 매일 17:05 KST 운영 채널에 통계 요약 자동 발송 |

---

## 프로젝트 구조

```
SIZL-AI-Agent-Beta-Test/
│
├── apps/
│   ├── api/                        # FastAPI 백엔드
│   │   ├── src/
│   │   │   ├── main.py             # FastAPI 앱 진입점
│   │   │   ├── api/                # HTTP 라우터 (issues, webhooks, health)
│   │   │   ├── services/           # 비즈니스 로직
│   │   │   │   ├── issue/          # 폼 → GitHub Issue 변환
│   │   │   │   ├── llm/            # LLM 분석 + diff 생성
│   │   │   │   ├── pr/             # PR 생성
│   │   │   │   ├── sheet/          # Google Sheets 동기화
│   │   │   │   └── sync/           # 일일 전수 동기화
│   │   │   ├── adapters/           # 외부 시스템 연동 (GitHub, Claude, Sheets, Slack)
│   │   │   ├── models/             # Pydantic 스키마 (BugReport, EnhancementRequest 등)
│   │   │   └── core/               # 설정, 로깅, 예외
│   │   ├── tests/
│   │   ├── Dockerfile
│   │   ├── pyproject.toml
│   │   └── .env.example
│   │
│   └── web/                        # Next.js 프론트엔드 (예정)
│
├── packages/                       # 공유 스키마/타입 (예정)
├── infra/
│   └── github-actions/             # CI/CD, 일일 cron
├── docs/                           # 설계 문서 (PRD, 아키텍처, 기술스택)
├── .github/
│   └── PULL_REQUEST_TEMPLATE.md
├── CLAUDE.md
└── README.md
```

---

## 기술 스택

| 영역 | 기술 |
|---|---|
| Backend | Python 3.12 + FastAPI + Pydantic v2 |
| LLM | Anthropic Claude API (`claude-sonnet-4-6`) |
| GitHub 연동 | PyGithub + GitHub App Webhook |
| Sheets 연동 | google-api-python-client |
| Frontend | Next.js 15 + TypeScript + Tailwind CSS (예정) |
| 배포 | Google Cloud Run (Backend) + Vercel (Frontend) |
| 패키지 관리 | uv (Python), pnpm (Node.js) |

---

## 개발 시작하기

### 1. 의존성 설치

```bash
cd apps/api
uv venv
uv pip install -e .
```

### 2. 환경변수 설정

```bash
cp .env.example .env
# .env 파일을 열어 각 항목 채우기
```

### 3. 서버 실행

```bash
cd apps/api
.venv/bin/uvicorn src.main:app --reload
```

### 4. 동작 확인

```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

API 문서: `http://localhost:8000/docs`

---

## 릴리스 계획

| Phase | 내용 | 상태 |
|---|---|---|
| Phase 0 | 프로젝트 스캐폴딩 | ✅ 완료 |
| Phase 1 | 데이터 모델 (Pydantic 스키마) | 🔲 예정 |
| Phase 2 | Backend 코어 | 🔲 예정 |
| Phase 3 | Adapter 인터페이스 + 구현체 | 🔲 예정 |
| Phase 4 | Service Layer | 🔲 예정 |
| Phase 5 | API Routes | 🔲 예정 |
| Phase 6 | Frontend | 🔲 예정 |

---

## 문서

설계 문서는 `docs/` 폴더에 있습니다.

| 문서 | 내용 |
|---|---|
| `PRD_v3.0` | 제품 요구사항, 기능 목록, 릴리스 계획 |
| `시스템_아키텍처_상세설계서_v1.0` | 컴포넌트 명세, 데이터 모델, API 계약 |
| `기술스택_명세서_v1.0` | 기술 선정 이유 및 대안 비교 |
| `베타테스트_도구_구현계획서_v2.0` | 주차별 작업 계획 (W0~W4) |
