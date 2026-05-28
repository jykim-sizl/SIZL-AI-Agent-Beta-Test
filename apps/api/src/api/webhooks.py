import json
import re
from typing import Annotated, Any

from fastapi import APIRouter, Header, Request

from src.api.deps import GitHubDep, PRServiceDep, SheetDep
from src.core.config import settings
from src.core.exceptions import WebhookVerificationError
from src.core.logging import logger
from src.core.security import verify_github_signature
from src.services.github import GitHubPort
from src.services.pr import PRService
from src.services.sheet import SheetPort

router = APIRouter()

_AUTO_BRANCH = re.compile(r"^auto/issue-(\d+)$")


@router.post("/webhooks")
async def receive_webhook(
    request: Request,
    pr: PRServiceDep,
    sheet: SheetDep,
    github: GitHubDep,
    x_hub_signature_256: Annotated[str | None, Header()] = None,
    x_github_event: Annotated[str | None, Header()] = None,
    x_github_delivery: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    # GitHub App webhook 수신: HMAC 검증 → 이벤트 라우팅. 핸들러 예외는 200을 막지 않는다.
    body = await request.body()
    if not verify_github_signature(body, x_hub_signature_256, settings.github_webhook_secret):
        raise WebhookVerificationError("invalid or missing X-Hub-Signature-256")

    payload: dict[str, Any] = {}
    try:
        parsed = json.loads(body)
        if isinstance(parsed, dict):
            payload = parsed
    except json.JSONDecodeError:
        pass

    action = payload.get("action")
    logger.info(
        "github_webhook_received",
        event_type=x_github_event,
        action=action,
        delivery=x_github_delivery,
    )

    try:
        if x_github_event == "issues" and action == "opened":
            _handle_issue_opened(payload, pr)
        elif x_github_event == "pull_request" and action == "closed":
            _handle_pr_closed(payload, sheet, github)
    except Exception as exc:  # noqa: BLE001 - 핸들러 실패가 웹훅 ACK(200)을 막지 않게
        logger.error(
            "github_webhook_handler_failed",
            event_type=x_github_event,
            action=action,
            error=str(exc),
        )

    return {"status": "received"}


def _handle_issue_opened(payload: dict[str, Any], pr: PRService) -> None:
    # ADR-006: bug 라벨이면 모두 분석 PR 대상 (P4 포함 — 사용자 결정 2026-05-27).
    issue = payload.get("issue") or {}
    labels = {lbl.get("name") for lbl in issue.get("labels", []) if isinstance(lbl, dict)}
    if "bug" not in labels:
        return
    number = issue.get("number")
    if not isinstance(number, int):
        return
    pr.create_for_bug(number, str(issue.get("title", "")))


def _handle_pr_closed(payload: dict[str, Any], sheet: SheetPort, github: GitHubPort) -> None:
    # 우리가 만든 auto/issue-N 브랜치의 PR 만 처리.
    # - merge 됨   → 이슈에 '완료' 코멘트 + 시트 '완료' + 이슈 close
    # - merge 안됨 → 이슈에 '철회' 코멘트 + 시트 '철회' + 이슈 close (ADR)
    # (LLM 풍부 요약은 Stage 2 — 현재는 템플릿)
    pull = payload.get("pull_request") or {}
    ref = (pull.get("head") or {}).get("ref", "")
    match = _AUTO_BRANCH.match(ref if isinstance(ref, str) else "")
    if not match:
        return
    issue_number = int(match.group(1))
    merged = bool(pull.get("merged"))
    status = "완료" if merged else "철회"
    pr_number = pull.get("number")
    pr_url = pull.get("html_url") or ""
    merge_sha = (pull.get("merge_commit_sha") or "")[:7]
    comment = _format_close_comment(issue_number, merged, pr_number, pr_url, merge_sha)
    github.add_comment(issue_number, comment)
    # 같은 텍스트를 시트 '조치 내용'에도 미러링 (Stage 2 에서 LLM 요약으로 교체)
    sheet.update_pr_status(issue_number, status, action_text=comment)
    github.close_issue(issue_number)


def _format_close_comment(
    issue_number: int, merged: bool, pr_number: Any, pr_url: str, merge_sha: str
) -> str:
    pr_ref = f"PR #{pr_number}" if pr_number else "분석 PR"
    pr_link = f"\n- 링크: {pr_url}" if pr_url else ""
    if merged:
        commit_line = f"\n- 머지 커밋: `{merge_sha}`" if merge_sha else ""
        return (
            f"✅ #{issue_number} 처리 완료 — {pr_ref} 머지됨.{commit_line}{pr_link}\n\n"
            f"운영자가 시트 '조치 내용'에 상세 결과(원인·수정 내용·재테스트 안내)를 정리해 주세요. "
            f"_(자동 분석 본문은 Stage 2에서 LLM이 채울 예정)_"
        )
    return (
        f"⚠️ #{issue_number} 철회 — {pr_ref} 가 머지 없이 닫혔습니다.{pr_link}\n\n"
        f"분석 PR이 폐기되어 이 이슈는 '철회' 상태가 되었습니다. "
        f"재현이 어려웠거나 다른 경로로 해결되었을 수 있어요. "
        f"필요하다면 새 이슈로 재제출 부탁드립니다."
    )
