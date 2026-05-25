# SIZL Agentic Brain — 베타테스트 자동화 도구

SIZL Agentic Brain 사내 베타테스트의 피드백 루프를 자동화하는 시스템입니다.

베타 테스터가 회사 이메일로 웹 폼에 접근하면, 시스템이 **Members 시트**에서 해당 이메일을 검증해 등록된 직원만 제출을 허용합니다. 제출된 이슈는 GitHub Issue로 자동 등록되고, 빈 브랜치와 PR이 자동 생성됩니다. LLM(Claude)은 이슈를 분석해 원인 가설을 PR 본문에 남기며, 실제 코드 수정은 개발자가 직접 합니다. 등록자 이름·팀 등 직원 정보는 Members 시트에서 자동으로 가져와 Raw Issues 시트에 채워집니다. 처리 현황은 Google Sheets 대시보드에 실시간으로 반영되고, 매일 17시에 Slack으로 요약이 발송됩니다.

---

## 주요 기능

| 기능 | 설명 |
|---|---|
| 직원 인증 | 폼 제출 시 이메일을 Members 시트와 대조해 등록된 직원만 허용 |
| 이슈 제출 폼 | 회사 이메일 한 줄로 접근, 클립보드 이미지 붙여넣기 지원 |
| GitHub Issue 자동 생성 | 폼 제출 즉시 라벨 포함 Issue 등록. 등록자 이름·팀은 Members 시트에서 자동 조회 |
| LLM 분석 + 빈 PR 자동 생성 | Issue 생성 시 빈 브랜치와 PR을 자동 생성. LLM이 원인 가설을 PR 본문에 기재. 코드 수정은 개발자가 직접 |
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
│   │   │   │   ├── llm/            # LLM 이슈 분석 (원인 가설 생성)
│   │   │   │   ├── pr/             # 빈 브랜치 + 빈 PR 생성
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

## Google Sheets 구조

하나의 스프레드시트에 4개의 시트로 운영됩니다.

| 시트명 | 용도 | 관리 주체 |
|---|---|---|
| **Members** | 직원 디렉토리 (이메일·이름·팀·직급·활성 여부) | 운영자가 수동 관리 |
| **Raw Issues** | 이슈 원장. 자동 컬럼(A–K, Q–R, T–AC) + 수작업 컬럼(L–P, S) | 자동화 + 운영자 |
| **Daily Snapshot** | 매일 17시 통계 1행 누적 | 자동화 |
| **Dashboard** | KPI 위젯 + 차트. Raw Issues / Daily Snapshot 기반 | 자동 계산 |

> **Members 시트 컬럼:** A(이메일) · B(이름) · C(팀) · D(직급) · E(활성: TRUE/FALSE)
> 퇴사자는 삭제하지 않고 E열을 FALSE로 변경하면 즉시 접근이 차단됩니다.

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
| Phase 1 | 데이터 모델 (Pydantic 스키마) | ✅ 완료 |
| Phase 2 | Backend 코어 | 🔲 예정 |
| Phase 3 | Port 인터페이스 정의 (구현체는 W2) | ✅ 완료 |
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
