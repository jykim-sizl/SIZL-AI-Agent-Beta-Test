from __future__ import annotations

from pathlib import Path

import openpyxl
import pytest

from src.adapters.impl import ExcelMemberAdapter
from src.services.member import MemberPort


def _make_xlsx(path: Path, rows: list[tuple[str, str, str]]) -> None:
    """헤더 순서를 실제 파일과 동일하게 (이름/이메일/팀) 둔 테스트용 xlsx 생성."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(("이름", "이메일", "팀"))
    for r in rows:
        ws.append(r)
    wb.save(path)


@pytest.fixture
def members_file(tmp_path: Path) -> Path:
    path = tmp_path / "Members.xlsx"
    _make_xlsx(
        path,
        [
            ("김정연", "jy_kim@sizl.co.kr", "Neo Lab"),
            ("김관호", "khkim@sizl.co.kr ", "Neo Lab"),  # 의도적 trailing space
        ],
    )
    return path


def test_member_port_is_abstract() -> None:
    with pytest.raises(TypeError):
        MemberPort()  # type: ignore[abstract]


def test_verify_returns_member_for_registered(members_file: Path) -> None:
    adapter = ExcelMemberAdapter(members_file)
    m = adapter.verify("jy_kim@sizl.co.kr")
    assert m is not None
    assert m.name == "김정연"
    assert m.team == "Neo Lab"


def test_verify_normalizes_case_and_whitespace(members_file: Path) -> None:
    adapter = ExcelMemberAdapter(members_file)
    # 입력 대소문자/공백 + 파일 측 trailing space 모두 정규화되어 매칭된다.
    assert adapter.verify("  KHKIM@sizl.co.kr ") is not None


def test_verify_returns_none_for_unregistered(members_file: Path) -> None:
    adapter = ExcelMemberAdapter(members_file)
    assert adapter.verify("nobody@sizl.co.kr") is None


def test_missing_required_column_raises(tmp_path: Path) -> None:
    path = tmp_path / "Bad.xlsx"
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(("이름", "메일", "팀"))  # '이메일' 아님
    ws.append(("홍길동", "hong@sizl.co.kr", "QA"))
    wb.save(path)
    with pytest.raises(ValueError, match="필수 컬럼 누락"):
        ExcelMemberAdapter(path).verify("hong@sizl.co.kr")


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        ExcelMemberAdapter(tmp_path / "nope.xlsx").verify("a@b.co")


def test_cache_avoids_reload_within_ttl(members_file: Path) -> None:
    adapter = ExcelMemberAdapter(members_file, cache_ttl_seconds=300.0)
    assert adapter.verify("jy_kim@sizl.co.kr") is not None
    # TTL 안에서 파일을 지워도 캐시된 결과로 응답한다.
    members_file.unlink()
    assert adapter.verify("jy_kim@sizl.co.kr") is not None
