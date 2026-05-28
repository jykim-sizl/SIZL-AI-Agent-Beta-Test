from __future__ import annotations

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from src.adapters.impl import ExcelMemberAdapter, GitHubAppAdapter, GoogleSheetAdapter
from src.core.config import settings
from src.services.github import GitHubPort
from src.services.issue import IssueService
from src.services.member import MemberService
from src.services.pr import PRService
from src.services.sheet import SheetPort


@lru_cache
def _member_service() -> MemberService:
    # 어댑터를 싱글턴으로 재사용해 5분 메모리 캐시(NFR-12)가 요청 간 유지되도록 한다.
    return MemberService(ExcelMemberAdapter(settings.members_xlsx_path))


def get_member_service() -> MemberService:
    return _member_service()


MemberServiceDep = Annotated[MemberService, Depends(get_member_service)]


@lru_cache
def _github() -> GitHubPort:
    return GitHubAppAdapter(
        settings.github_app_id,
        settings.github_app_private_key_path,
        settings.github_issue_repo,
        settings.github_target_repo,
    )


@lru_cache
def _issue_service() -> IssueService:
    return IssueService(_github())


def get_issue_service() -> IssueService:
    return _issue_service()


IssueServiceDep = Annotated[IssueService, Depends(get_issue_service)]


@lru_cache
def _sheet() -> SheetPort:
    return GoogleSheetAdapter(
        settings.google_service_account_json_path, settings.google_spreadsheet_id
    )


def get_sheet() -> SheetPort:
    return _sheet()


SheetDep = Annotated[SheetPort, Depends(get_sheet)]


@lru_cache
def _pr_service() -> PRService:
    return PRService(_github(), _sheet(), settings.github_issue_repo)


def get_pr_service() -> PRService:
    return _pr_service()


PRServiceDep = Annotated[PRService, Depends(get_pr_service)]
