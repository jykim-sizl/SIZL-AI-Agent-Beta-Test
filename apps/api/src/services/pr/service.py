from __future__ import annotations

from src.services.github.port import GitHubPort
from src.services.sheet.port import SheetPort


class PRService:
    """버그 이슈 → 빈 브랜치 + 러프 PR 생성, 시트 처리상태를 '진행중'으로.

    현재 PR 본문은 러프 안내(코드 없음)이며, Playwright 재현 요약 / LLM 원인가설은
    후속 단계에서 본문에 채운다(ADR: Playwright 재현 게이팅). GitHubPort/SheetPort에만 의존.
    """

    def __init__(self, github: GitHubPort, sheet: SheetPort, issue_repo: str) -> None:
        self._github = github
        self._sheet = sheet
        self._issue_repo = issue_repo  # PR과 이슈가 다른 repo라 본문에 풀 링크로

    def create_for_bug(self, issue_number: int, issue_title: str) -> int:
        title = f"[자동 분석] #{issue_number} {issue_title}".strip()
        issue_url = f"https://github.com/{self._issue_repo}/issues/{issue_number}"
        body = (
            f"이슈 자동 분석용 PR입니다. (코드 없음 / 빈 PR)\n\n"
            "- 🔬 Playwright 재현 요약 — *후속 단계에서 추가*\n"
            "- 🤖 LLM 원인 가설 — *후속 단계에서 추가*\n\n"
            "사람 검토 후 작업을 시작하세요. (브랜치 보호: main 병합엔 리뷰 필요)\n"
            f"\n관련 이슈: {issue_url}"
        )
        number = self._github.create_empty_pr(issue_number, title, body)
        self._sheet.update_pr_status(issue_number, "진행중")
        return number
