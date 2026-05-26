# apps/api CHANGELOG

본 파일은 Backend(`apps/api/`) 패키지의 변경 이력만 추적합니다.
Frontend(`apps/web/`)와 인프라 변경은 별도 CHANGELOG 또는 루트에서 관리합니다.

# Changelog

이 프로젝트의 주요 변경 사항을 기록합니다. 형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를 따르고, 버저닝은 [SemVer](https://semver.org/lang/ko/)를 사용합니다.

## [Unreleased]

### Added

- **Pydantic 스키마 4종** (`apps/api/src/models/`)
  - `BugReport` (Severity P1~P4 Enum, EmailStr, extra=forbid)
  - `EnhancementRequest`
  - `MemberVerify` (`is_eligible()` 메서드, `position` Optional)
  - `AnalysisResult` (PRD B-5 양식, `confidence` 제외)
- **Port ABC 4종** (`apps/api/src/adapters/ports/`): `LLMPort`, `SheetPort`, `GitHubPort`, `IssuePort`
- **Dummy 어댑터 4종** (`apps/api/src/adapters/impl/`) — 모든 메서드 `NotImplementedError("W2에서 구현")`
- **단위 테스트 19건** (`apps/api/tests/test_schemas.py`, `test_ports.py`)
- **GitHub Actions CI**: `apps/api/**` 변경 시 ruff + pytest 자동 실행
- `pydantic[email]` extra 추가 (EmailStr 검증용)

### Changed

- `SheetPort`를 ADR-003에 정렬: 단일 `append_issue(dict)` → `append_bug(row)` + `append_enhancement(row)` 분리. ADR-001/PRD v4.0에 따라 `verify_member`는 제거 (Members는 로컬 xlsx 기반, 별도 `MemberPort` 신설 예정).
- README 릴리스 계획표 갱신 (Phase 1 ✅, Phase 3 Port 정의 ✅), PRD 표기 v3.0 → v4.0.
- `Severity`를 `class(str, Enum)` → `class(StrEnum)` (Py 3.12 권장 형태).
- **Port ABC 위치 컨벤션 정렬** — 새 ADR 채택 후 `src/adapters/ports/<x>_port.py` → `src/services/<x>/port.py`로 이동. `adapters/ports/` 디렉토리 폐기. (Hexagonal 컨벤션·CLAUDE.md와 일치)
- `MemberVerify.position` 필드 제거 — 시스템 구현에서 사용 안 함이 확인되어 모델에서 빼고, 테스트는 extra-field 거부 검증으로 교체.

### Notes

- LLM 어댑터 본 구현은 Anthropic API 키 발급 후 W3로 연기. 현재는 Dummy로 stub만 유지.
- 시니어 리뷰가 필요한 결정은 `docs/REVIEW_NEEDED.md` 참조.
