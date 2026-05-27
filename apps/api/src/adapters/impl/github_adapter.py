from __future__ import annotations

from pathlib import Path

from github import Auth, GithubIntegration
from github.Repository import Repository

from src.core.logging import logger
from src.models.issue_draft import IssueDraft
from src.services.github.port import GitHubPort


class GitHubAppAdapter(GitHubPort):
    """GitHubPort 실구현. GitHub App(설치 토큰)으로 이슈를 생성/종료한다.

    이슈는 App이 설치된 issue_repo에 만든다. 빈 PR 생성(create_empty_pr)은
    Playwright 재현 게이팅 + 공동 target repo 대상이라 별도 단계에서 구현한다(ADR).
    """

    def __init__(self, app_id: str, private_key_path: str, issue_repo: str) -> None:
        self._repo_full = issue_repo
        private_key = Path(private_key_path).read_text(encoding="utf-8")
        self._integration = GithubIntegration(auth=Auth.AppAuth(int(app_id), private_key))

    def _repo(self) -> Repository:
        owner, name = self._repo_full.split("/", 1)
        installation = self._integration.get_repo_installation(owner, name)
        gh = self._integration.get_github_for_installation(installation.id)
        return gh.get_repo(self._repo_full)

    def create_issue(self, draft: IssueDraft) -> int:
        issue = self._repo().create_issue(title=draft.title, body=draft.body, labels=draft.labels)
        logger.info("github_issue_created", number=issue.number, repo=self._repo_full)
        return issue.number

    def create_empty_pr(self, issue_number: int, title: str, body: str) -> int:
        # 이슈와 같은 repo에 빈 브랜치 + 빈 PR(코드 없음) 생성. (ADR: 베타 PR=이 repo)
        repo = self._repo()
        owner = self._repo_full.split("/", 1)[0]
        branch = f"auto/issue-{issue_number}"

        # 웹훅 재전송 대비 멱등: 같은 head로 이미 PR이 있으면 그 번호 반환.
        existing = list(repo.get_pulls(state="all", head=f"{owner}:{branch}"))
        if existing:
            return existing[0].number

        default = repo.default_branch
        base_commit = repo.get_git_commit(repo.get_branch(default).commit.sha)
        # base 트리를 그대로 쓰는 빈 커밋 → 브랜치 (PR에 diff 없음)
        empty_commit = repo.create_git_commit(
            message=f"chore: open analysis PR for issue #{issue_number}",
            tree=base_commit.tree,
            parents=[base_commit],
        )
        repo.create_git_ref(ref=f"refs/heads/{branch}", sha=empty_commit.sha)
        pull = repo.create_pull(title=title, body=body, base=default, head=branch)
        logger.info(
            "github_pr_created", number=pull.number, issue=issue_number, repo=self._repo_full
        )
        return pull.number

    def close_issue(self, issue_number: int) -> None:
        self._repo().get_issue(issue_number).edit(state="closed")
        logger.info("github_issue_closed", number=issue_number, repo=self._repo_full)
