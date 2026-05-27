from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class IssueDraft(BaseModel):
    """GitHub Issue 생성 직전의 완성된 초안.

    IssueService가 BugReport/EnhancementRequest + 회원 메타데이터로부터 만들어내며,
    GitHubAdapter(GitHubPort)는 이 초안을 그대로 GitHub API에 전달하는 I/O만 담당한다.
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    labels: list[str] = Field(default_factory=list)
