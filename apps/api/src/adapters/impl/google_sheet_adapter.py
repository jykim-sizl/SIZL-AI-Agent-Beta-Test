from __future__ import annotations

import re
from typing import Any

from google.oauth2 import service_account
from googleapiclient.discovery import build

from src.core.logging import logger
from src.services.sheet.port import SheetPort

_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# 실제 시트 탭/헤더 순서. 자동화는 이 순서대로 행을 append 하고,
# 운영자 수기 컬럼(담당자/조치/원인 등)은 빈 문자열로 두어 절대 덮어쓰지 않는다.
BUG_SHEET = "Raw Issues"
BUG_COLUMNS = [
    "Issue ID",
    "등록일",
    "등록자",
    "팀",
    "테스트 계정",
    "테스트 영역",
    "세부 기능",
    "발생 화면",
    "테스트 시나리오",
    "발생 증상",
    "재현 여부",
    "발생 빈도",
    "우선순위",
    "원인 유형",
    "원인 상세",
    "테스트 담당자",
    "조치 내용",
    "조치예정일",
    "처리일자",
    "처리 상태",
    "배포 여부",
    "종료 여부",
    "# github issue",
    "비고",
]

ENH_SHEET = "Enhancement"
ENH_COLUMNS = [
    "Issue ID",
    "등록일",
    "등록자",
    "팀",
    "테스트 영역",
    "세부 기능",
    "발생 화면",
    "우선순위",
    "테스트 담당자",
    "조치 내용",
    "조치예정일",
    "처리일자",
    "처리 상태",
    "배포 여부",
    "종료 여부",
    "비고",
]

_ISSUE_COL = "# github issue"  # 행 식별용 컬럼 (Raw Issues)
_STATUS_COL = "처리 상태"


class GoogleSheetAdapter(SheetPort):
    """SheetPort 실구현. google-api-python-client로 Raw Issues / Enhancement 탭에 기록.

    멱등성: append는 새 행을 추가하므로 재제출 시 중복될 수 있다. 중복 방지는
    Issue ID / # github issue 기준 upsert로 W2 후반에 보강한다(현재는 append).
    운영자 컬럼은 항상 빈칸으로 두어 사람이 채운 값을 보존한다(CLAUDE.md).
    """

    def __init__(self, service_account_json_path: str, spreadsheet_id: str) -> None:
        self._sid = spreadsheet_id
        creds = service_account.Credentials.from_service_account_file(  # type: ignore[no-untyped-call]
            service_account_json_path, scopes=_SCOPES
        )
        self._sheets = build(
            "sheets", "v4", credentials=creds, cache_discovery=False
        ).spreadsheets()
        self._values = self._sheets.values()
        self._sheet_ids: dict[str, int] = {}

    def _sheet_id(self, title: str) -> int:
        if not self._sheet_ids:
            meta = self._sheets.get(spreadsheetId=self._sid).execute()
            self._sheet_ids = {
                s["properties"]["title"]: s["properties"]["sheetId"] for s in meta["sheets"]
            }
        return self._sheet_ids[title]

    def append_bug(self, row: dict[str, Any]) -> None:
        self._append(BUG_SHEET, BUG_COLUMNS, row)

    def append_enhancement(self, row: dict[str, Any]) -> None:
        self._append(ENH_SHEET, ENH_COLUMNS, row)

    def _append(self, sheet: str, columns: list[str], row: dict[str, Any]) -> None:
        values = [[str(row.get(col, "")) for col in columns]]
        result = self._values.append(
            spreadsheetId=self._sid,
            range=f"'{sheet}'!A1",
            valueInputOption="RAW",
            insertDataOption="INSERT_ROWS",
            body={"values": values},
        ).execute()
        # 새 행은 윗행 서식(연두색)을 물려받으므로 흰 배경으로 정리한다.
        updated_range = result.get("updates", {}).get("updatedRange", "")
        self._whiten_row(sheet, updated_range, len(columns))
        logger.info("sheet_row_appended", sheet=sheet, issue=row.get(_ISSUE_COL))

    def _whiten_row(self, sheet: str, updated_range: str, ncols: int) -> None:
        match = re.search(r"![A-Za-z]+(\d+)", updated_range)
        if not match:
            return
        row = int(match.group(1))
        self._sheets.batchUpdate(
            spreadsheetId=self._sid,
            body={
                "requests": [
                    {
                        "repeatCell": {
                            "range": {
                                "sheetId": self._sheet_id(sheet),
                                "startRowIndex": row - 1,
                                "endRowIndex": row,
                                "startColumnIndex": 0,
                                "endColumnIndex": ncols,
                            },
                            "cell": {
                                "userEnteredFormat": {
                                    "backgroundColor": {"red": 1, "green": 1, "blue": 1}
                                }
                            },
                            "fields": "userEnteredFormat.backgroundColor",
                        }
                    }
                ]
            },
        ).execute()

    def update_pr_status(self, issue_number: int, status: str) -> None:
        # Raw Issues 의 '# github issue' 컬럼에서 행을 찾아 '처리 상태'만 갱신.
        col_idx = BUG_COLUMNS.index(_ISSUE_COL)
        status_idx = BUG_COLUMNS.index(_STATUS_COL)
        col_letter = chr(ord("A") + col_idx)
        status_letter = chr(ord("A") + status_idx)

        resp = self._values.get(
            spreadsheetId=self._sid, range=f"'{BUG_SHEET}'!{col_letter}2:{col_letter}"
        ).execute()
        rows = resp.get("values", [])
        for offset, cell in enumerate(rows):
            value = cell[0].strip().lstrip("#") if cell else ""
            if value == str(issue_number):
                row_num = offset + 2  # 데이터는 2행부터
                self._values.update(
                    spreadsheetId=self._sid,
                    range=f"'{BUG_SHEET}'!{status_letter}{row_num}",
                    valueInputOption="RAW",
                    body={"values": [[status]]},
                ).execute()
                logger.info("sheet_status_updated", issue=issue_number, status=status)
                return
        logger.warning("sheet_status_row_not_found", issue=issue_number)
