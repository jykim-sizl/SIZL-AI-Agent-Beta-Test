# REVIEW NEEDED — Phase 1 시니어 리뷰 항목

`feat/phase1-schemas-and-ports` 브랜치 작업 중 내린 결정 가운데, 시니어 리뷰가 필요한 항목.

## 1. Port 위치: `services/*` 대신 `adapters/ports/`

사용자 작업 명세에는 `apps/api/src/adapters/ports/`로 지정되어 있어 그대로 따랐다. 그러나:

- `CLAUDE.md` 아키텍처 섹션은 "GitHubPort, LLMPort, SheetPort, NotifierPort live alongside the services that consume them" 즉 `services/<domain>/` 안에 ABC를 두라고 명시.
- Notion Tasks v2의 "Service 인터페이스 정의" 체크리스트도 `services/` 내부 4폴더 생성으로 기록.

**리뷰 포인트:** Hexagonal Ports & Adapters 원칙상 둘 다 가능. 사용자 명세 우선이지만 다른 문서와 정합성 맞출지 결정 필요.

## 2. SheetPort에서 `verify_member` 제거 → `MemberPort` 신설

원래 명세는 `SheetPort.verify_member(email) -> MemberVerify | None`이었으나, **ADR > PRD** 원칙에 따라 다음 ADR을 우선 적용했다:
- **ADR-001 / PRD v4.0**: Members 검증은 Google Sheet가 아니라 **로컬 `Members.xlsx`** 기반.
- **ADR-003**: SheetPort에 `append_bug` / `append_enhancement` 분리.

따라서 `verify_member`는 SheetPort 책임이 아니라고 판단하여 제거하고, 별도 **`MemberPort` 신설을 W1 후반으로 연기**.

**리뷰 포인트:** MemberPort + ExcelMemberAdapter 도입 시점·시그니처 확정 필요.

## 3. `BugReport.test_environment` 단일 `str`

PRD A-4는 "OS, 브라우저, 디바이스, 네트워크 필수 입력. 일부는 자동 감지·수정 가능"이라고 명시. 본 작업에서는 사용자 명세의 `test_environment` 단일 필드를 단순 `str`로 받도록 했다.

**리뷰 포인트:** 폼 단계에서 4개 필드로 분리 입력받아 백엔드에서 단일 string으로 합칠지, 또는 `TestEnvironment` 서브모델을 만들지. 후자라면 시트의 어느 컬럼에 들어가는지도 결정 필요.

## 4. `MemberVerify.position` Optional 처리

- PRD v4.0: Members 컬럼은 `이메일, 이름, 팀, 직급` 4종.
- `CLAUDE.md`: "Schema: 이름 / 팀 / 이메일 (no 직급 in v4.1)" — v4.1에서 직급 제거 표기.
- 사용자 명세: `position` 필드 포함.

호환성 차원에서 `position: str | None = None`로 두었음.

**리뷰 포인트:** v4.1 적용 여부와 시점, 직급이 향후에도 필요한지 확정.

## 5. `Severity` 라벨 범위 P1~P4

- PRD §4.1: "P1~P3" 기준만 정의.
- Notion ADR "GitHub 라벨 세트를 bug·enhancement·priority:P1∼P4의 6개로 최소화": **P1~P4**.

ADR > PRD 원칙에 따라 P1~P4로 구현. **리뷰 포인트:** P4의 운영 의미(예: nice-to-have, 백로그)를 PRD/운영 문서에 명문화할 필요.

## 6. Dummy(NotImplementedError) vs ADR-002 NoOpLLMProvider

- 본 작업의 `DummyLLMAdapter`는 **테스트 stub**: 호출 시 즉시 `NotImplementedError("W2에서 구현")` → 실제 호출 경로에서 빠르게 실패시켜 W2 구현 누락을 잡는 용도.
- ADR-002 NoOpLLMProvider는 **운영용 폴백**: 키 미설정 시 PRD B-6 폴백 경로로 자연스럽게 흐르도록 "LLM 미설정" 사유를 반환.

두 컴포넌트는 역할이 다르므로 공존해야 함. **리뷰 포인트:** 어느 시점에 NoOpLLMProvider를 도입할지, Dummy와 어떻게 구분 명명할지.

## 7. CHANGELOG.md를 모노레포 루트에 둠

`apps/api/CHANGELOG.md`가 아니라 `/CHANGELOG.md`로 작성. 추후 `apps/web/`이 추가되면 별도 CHANGELOG로 분리할지 검토 필요.

---

## 빠른 결정 요청

위 6개 중 가장 시급한 결정 순서 (작업 흐름 영향도 기준):
1. **#2 MemberPort 신설** — W1 후반의 폼 라우트(`POST /issues`) 멤버 검증 구현 시 즉시 영향.
2. **#3 test_environment 구조** — 폼 화면(W2-W3) 설계에 영향.
3. 나머지는 기능에 미치는 영향 적음 — W2 진행 중 자연스럽게 결정 가능.
