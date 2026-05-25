from __future__ import annotations

from src.services.sheet.port import SheetPort


class DummySheetAdapter(SheetPort):
    def append_bug(self, row: dict) -> None:
        raise NotImplementedError("W2에서 구현")

    def append_enhancement(self, row: dict) -> None:
        raise NotImplementedError("W2에서 구현")

    def update_pr_status(self, issue_number: int, status: str) -> None:
        raise NotImplementedError("W2에서 구현")
