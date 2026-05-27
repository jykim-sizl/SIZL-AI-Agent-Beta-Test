import json
import re
from typing import Annotated, Any

from fastapi import APIRouter, Header, Request

from src.api.deps import PRServiceDep, SheetDep
from src.core.config import settings
from src.core.exceptions import WebhookVerificationError
from src.core.logging import logger
from src.core.security import verify_github_signature
from src.services.pr import PRService
from src.services.sheet import SheetPort

router = APIRouter()

_AUTO_BRANCH = re.compile(r"^auto/issue-(\d+)$")


@router.post("/webhooks")
async def receive_webhook(
    request: Request,
    pr: PRServiceDep,
    sheet: SheetDep,
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
            _handle_pr_closed(payload, sheet)
    except Exception as exc:  # noqa: BLE001 - 핸들러 실패가 웹훅 ACK(200)을 막지 않게
        logger.error(
            "github_webhook_handler_failed",
            event_type=x_github_event,
            action=action,
            error=str(exc),
        )

    return {"status": "received"}


def _handle_issue_opened(payload: dict[str, Any], pr: PRService) -> None:
    # ADR-006: bug 라벨만 분석 PR. priority:P4는 자동 PR 대상에서 제외.
    issue = payload.get("issue") or {}
    labels = {lbl.get("name") for lbl in issue.get("labels", []) if isinstance(lbl, dict)}
    if "bug" not in labels or "priority:P4" in labels:
        return
    number = issue.get("number")
    if not isinstance(number, int):
        return
    pr.create_for_bug(number, str(issue.get("title", "")))


def _handle_pr_closed(payload: dict[str, Any], sheet: SheetPort) -> None:
    # 우리가 만든 auto/issue-N 브랜치의 PR이 merge되면 해당 이슈 처리상태를 완료로.
    pull = payload.get("pull_request") or {}
    ref = (pull.get("head") or {}).get("ref", "")
    match = _AUTO_BRANCH.match(ref if isinstance(ref, str) else "")
    if match and pull.get("merged"):
        sheet.update_pr_status(int(match.group(1)), "완료")
