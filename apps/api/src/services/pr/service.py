from __future__ import annotations

from src.core.logging import logger
from src.services.github.port import GitHubPort
from src.services.llm.port import IssueOpenContext, LLMPort
from src.services.sheet.port import SheetPort


class PRService:
    """버그 이슈 → 빈 브랜치 + PR 생성, 시트 처리상태 '진행중'.

    PR 본문은 LLM(Gemini)이 이슈를 보고 작성한 분석 초안(요약/추정 원인/점검 포인트/
    재현 시나리오/다음 작업). LLM 없거나 실패 시 안전한 stub fallback.
    """

    def __init__(
        self,
        github: GitHubPort,
        sheet: SheetPort,
        llm: LLMPort,
        issue_repo: str,
        pr_repo: str,
    ) -> None:
        self._github = github
        self._sheet = sheet
        self._llm = llm
        self._issue_repo = issue_repo  # PR과 이슈가 다른 repo라 본문에 풀 링크로
        self._pr_repo = pr_repo  # 시트에 적을 PR 링크 구성용

    def create_for_bug(self, issue_number: int, issue_title: str) -> int:
        title = f"[자동 분석] #{issue_number} {issue_title}".strip()
        issue_url = f"https://github.com/{self._issue_repo}/issues/{issue_number}"
        # LLM 입력용 이슈 본문 fetch. 실패해도 stub 으로 진행.
        try:
            issue = self._github.get_issue(issue_number)
            issue_body = issue.get("body", "")
        except Exception as exc:  # noqa: BLE001
            logger.warning("issue_fetch_for_pr_open_failed", issue=issue_number, error=str(exc))
            issue_body = ""
        ctx = IssueOpenContext(
            issue_number=issue_number,
            issue_title=issue_title,
            issue_body=issue_body,
            issue_url=issue_url,
        )
        body = self._llm.draft_pr_body(ctx) or self._stub_body(issue_url)
        number = self._github.create_empty_pr(issue_number, title, body)
        pr_url = f"https://github.com/{self._pr_repo}/pull/{number}"
        self._sheet.update_pr_status(issue_number, "진행중", number, pr_url)
        return number

    @staticmethod
    def _stub_body(issue_url: str) -> str:
        return (
            "이슈 자동 분석용 PR입니다. (코드 없음 / 빈 PR)\n\n"
            "- 🤖 LLM 분석 초안 생성 실패 — 운영자가 직접 검토 시작 부탁드립니다.\n\n"
            "사람 검토 후 작업을 시작하세요. (브랜치 보호: main 병합엔 리뷰 필요)\n"
            f"\n관련 이슈: {issue_url}"
        )
