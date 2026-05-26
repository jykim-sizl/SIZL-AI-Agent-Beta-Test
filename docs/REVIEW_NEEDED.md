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