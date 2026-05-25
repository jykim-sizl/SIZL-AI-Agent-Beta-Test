# REVIEW NEEDED — Phase 1 시니어 리뷰 항목

`feat/phase1-schemas-and-ports` 브랜치 작업 중 내린 결정 가운데, 시니어 리뷰가 필요한 항목.

## 1. ~~Port 위치~~ ✅ **해소 (2026-05-26)**

ADR 채택 후 `src/services/<domain>/port.py`로 이동 완료. `adapters/ports/` 폐기.

- ADR: Notion DB "의사결정 로그(ADR)" — "Port ABC는 services/<domain>/port.py에 위치 (도메인 주도)"
- 변경 커밋: `da11ddc refactor(ports): move Port ABCs into services/<domain>/port.py`

## 2. SheetPort에서 `verify_member` 제거 → `MemberPort` 신설

원래 명세는 `SheetPort.verify_member(email) -> MemberVerify | None`이었으나, **ADR > PRD** 원칙에 따라 다음 ADR을 우선 적용했다:
- **ADR-001 / PRD v4.0**: Members 검증은 Google Sheet가 아니라 **로컬 `Members.xlsx`** 기반.
- **ADR-003**: SheetPort에 `append_bug` / `append_enhancement` 분리.

따라서 `verify_member`는 SheetPort 책임이 아니라고 판단하여 제거하고, 별도 **`MemberPort` 신설을 W1 후반으로 연기**.

**리뷰 포인트:** MemberPort + ExcelMemberAdapter 도입 시점·시그니처 확정 필요.

## 3. ~~`BugReport.test_environment` 단일 `str`~~ ✅ **해소 (2026-05-26)**

사용자 결정: PRD에서 명시한 환경 정보(OS·브라우저·디바이스·네트워크)는 폼에서 자동 수집되어 이슈 본문에만 표시. **Google Sheets 컬럼으로는 들어가지 않음** — 개발자 디버깅 정보 용도.

현재 구현(단일 `str`) 그대로 유지. 폼 단계에서 자동 감지된 값을 단일 텍스트로 합쳐 백엔드에 전달.

## 4. ~~`MemberVerify.position` Optional 처리~~ ✅ **해소 (2026-05-26)**

사용자 결정: position(직급)은 Members.xlsx에만 존재하는 메타데이터이고 시스템 구현에서 사용할 일 없음. **MemberVerify에서 제거**.

- 변경 커밋: `28b0527 refactor(models): drop MemberVerify.position field`
- 테스트는 "extra field 거부" 케이스로 교체해 `extra=forbid` 정책을 명시적으로 검증.

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

## 빠른 결정 요청 (남은 항목)

해소된 #1·#3·#4 외에 작업 흐름에 영향을 주는 순서:
1. **#2 MemberPort 신설** — W1 후반의 폼 라우트(`POST /issues`) 멤버 검증 구현 시 즉시 영향. 우선 결정 필요.
2. **#5 Severity P1~P4** — 라벨 운영 정책 (P4의 의미 명문화) 정도. W3까지 미뤄도 됨.
3. **#6 Dummy vs NoOpLLMProvider 명명** — W3 LLM 구현 시 결정.
4. **#7 CHANGELOG 위치** — apps/web 추가 시점에 재검토.
