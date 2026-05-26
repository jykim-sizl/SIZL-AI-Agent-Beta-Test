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

## 5. Severity 라벨 범위 P1~P4 ✅ **해소 (2026-05-26)**

- PRD v4.1로 minor 패치하여 §4.1.2에 Severity 라벨을 P1~P4로 명시.
- 운영 정책(LLM 분석 실행 여부, SLA 등)은 PRD에 직접 명시하지 않고 
  `docs/operations/severity_policy.md`로 분리. 운영 정책 변경 시 
  PRD 버전 업이 발생하지 않도록 위임 구조 채택.
- PRD v4.1에서 §4.1을 "FR 우선순위(§4.1.1)"와 "이슈 Severity(§4.1.2)"로 
  분리하여 동일 표기(P1~P3)의 모호성 제거.

**구현 영향:** 
B-3(LLM 분석 제외), B-4(분석 PR 제외)에 P4 분기가 추가됨. W3 LLM 어댑터 
구현 시 services/issue/ 레이어에서 severity==P4 분기 처리 필요.

## 6. Dummy(NotImplementedError) vs ADR NoOpLLMProvider ✅ **해소 (2026-05-26)**

명명과 도입 시점 결정:
- `DummyLLMAdapter`: 현 이름 유지. W2 종료 시 `tests/` 또는 
  `tests/stubs/`로 이동하여 **테스트 전용**임을 명확히 한다.
- `NoOpLLMProvider`: W3 시작 시 첫 PR(LLM 어댑터 도입)에서 
  `RealLLMProvider`와 함께 신설. ADR "LLM 후순위화"의 폴백 시나리오 구현체.
- DI 분기는 `core/container.py` 또는 FastAPI Depends에서 
  `settings.ANTHROPIC_API_KEY` 유무에 따라 결정.

W3 첫 PR 제목 권장: 
`feat(llm): add RealLLMProvider and NoOpLLMProvider fallback`

## 7. CHANGELOG.md 위치 ✅ **해소 (2026-05-26)**

`apps/api/CHANGELOG.md`로 이동. 모노레포 표준 컨벤션(앱별 CHANGELOG) 적용.

- `apps/web/` 추가 시 별도 `apps/web/CHANGELOG.md` 신설.
- 인프라/모노레포 자체 변경이 누적되면 추후 루트 CHANGELOG 도입 재검토.

## 8. P4 자동 처리 제외 분기 ⏳ **W3 구현 시 반영**

PRD v4.1 B-3, B-4 변경에 따라 P4 이슈는 LLM 분석 및 분석 PR 생성 
대상에서 제외된다.

구현 위치 후보:
- `services/issue/`: severity==P4 분기 → 분석 PR 생성 스킵
- `services/llm/`: P4 호출 자체를 차단할지, 호출은 하되 PR만 안 만들지 결정 필요

**권장:** services/issue/ 레이어에서 분기 (LLM 어댑터는 호출되면 
항상 동작하도록 단순화 — 운영 정책 변경 시 issue 레이어만 수정).

---

## 빠른 결정 요청 (남은 항목)

해소된 #1, #3, #4, #5, #6, #7 외 작업 흐름 영향 순서:

1. **#2 MemberPort 신설** — W1 후반의 폼 라우트(`POST /issues`) 
   멤버 검증 구현 시 즉시 영향. 우선 결정 필요.
2. **#8 P4 자동 처리 제외 분기** — W3 LLM 어댑터 구현 시 함께 반영.
