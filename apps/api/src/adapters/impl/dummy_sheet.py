from __future__ import annotations

from typing import Any

from src.services.sheet.port import SheetPort


class DummySheetAdapter(SheetPort):
    def append_bug(self, row: dict[str, Any]) -> None:
        raise NotImplementedError("W2에서 구현")

    def append_enhancement(self, row: dict[str, Any]) -> None:
        raise NotImplementedError("W2에서 구현")

    def update_pr_status(
        self,
        issue_number: int,
        status: str,
        pr_number: int | None = None,
        pr_url: str | None = None,
    ) -> None:
        raise NotImplementedError("W2에서 구현")
