from __future__ import annotations

import uuid
from pathlib import Path

from github import Auth, GithubException, GithubIntegration
from github.Repository import Repository

from src.core.logging import logger
from src.models.issue_draft import IssueDraft
from src.services.github.port import GitHubPort


class GitHubAppAdapter(GitHubPort):
    """GitHubPort 실구현. GitHub App(설치 토큰)으로 이슈/ PR을 처리한다.

    이슈는 issue_repo(이 repo)에, PR/빈 브랜치는 pr_repo(타깃 repo)에 만든다.
    App은 두 repo 모두에 설치돼 있어야 한다(repo별 설치 토큰을 각각 발급).
    """

    def __init__(self, app_id: str, private_key_path: str, issue_repo: str, pr_repo: str) -> None:
        self._issue_repo = issue_repo
        self._pr_repo = pr_repo
        private_key = Path(private_key_path).read_text(encoding="utf-8")
        self._integration = GithubIntegration(auth=Auth.AppAuth(int(app_id), private_key))

    def _repo(self, full_name: str) -> Repository:
        owner, name = full_name.split("/", 1)
        installation = self._integration.get_repo_installation(owner, name)
        gh = self._integration.get_github_for_installation(installation.id)
        return gh.get_repo(full_name)

    def create_issue(self, draft: IssueDraft) -> int:
        repo = self._repo(self._issue_repo)
        issue = repo.create_issue(title=draft.title, body=draft.body, labels=draft.labels)
        logger.info("github_issue_created", number=issue.number, repo=self._issue_repo)
        return issue.number

    def get_issue(self, issue_number: int) -> dict[str, str]:
        issue = self._repo(self._issue_repo).get_issue(issue_number)
        return {"title": issue.title or "", "body": issue.body or ""}

    def update_issue(self, issue_number: int, title: str, body: str) -> None:
        self._repo(self._issue_repo).get_issue(issue_number).edit(title=title, body=body)
        logger.info("github_issue_updated", number=issue_number, repo=self._issue_repo)

    def add_comment(self, issue_number: int, body: str) -> None:
        self._repo(self._issue_repo).get_issue(issue_number).create_comment(body)
        logger.info("github_issue_commented", number=issue_number, repo=self._issue_repo)

    def create_empty_pr(self, issue_number: int, title: str, body: str) -> int:
        # 타깃 repo(pr_repo)에 빈 브랜치 + 빈 PR(코드 없음) 생성. (App이 pr_repo에 설치됨)
        repo = self._repo(self._pr_repo)
        owner = self._pr_repo.split("/", 1)[0]
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
        logger.info("github_pr_created", number=pull.number, issue=issue_number, repo=self._pr_repo)
        return pull.number

    def upload_image(self, filename: str, content: bytes) -> str:
        # 공개 issue_repo의 'assets' 브랜치에 커밋 → raw URL 반환(이슈 본문에서 렌더).
        repo = self._repo(self._issue_repo)
        branch = "assets"
        try:
            repo.get_branch(branch)
        except GithubException:
            base_sha = repo.get_branch(repo.default_branch).commit.sha
            repo.create_git_ref(ref=f"refs/heads/{branch}", sha=base_sha)

        safe = filename.replace("/", "_").strip() or "image.png"
        path = f"issue-assets/{uuid.uuid4().hex}-{safe}"
        repo.create_file(
            path=path, message=f"chore: upload asset {safe}", content=content, branch=branch
        )
        owner, name = self._issue_repo.split("/", 1)
        url = f"https://raw.githubusercontent.com/{owner}/{name}/{branch}/{path}"
        logger.info("github_image_uploaded", path=path, repo=self._issue_repo)
        return url

    def close_issue(self, issue_number: int) -> None:
        self._repo(self._issue_repo).get_issue(issue_number).edit(state="closed")
        logger.info("github_issue_closed", number=issue_number, repo=self._issue_repo)
