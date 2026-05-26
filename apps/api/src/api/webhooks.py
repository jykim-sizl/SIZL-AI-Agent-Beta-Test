import json
from typing import Annotated

from fastapi import APIRouter, Header, Request

from src.core.config import settings
from src.core.exceptions import WebhookVerificationError
from src.core.logging import logger
from src.core.security import verify_github_signature

router = APIRouter()


@router.post("/webhooks")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: Annotated[str | None, Header()] = None,
    x_github_event: Annotated[str | None, Header()] = None,
    x_github_delivery: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    # GitHub App webhook 수신. HMAC 서명 검증 후 이벤트 종류를 로그로 남긴다. 라우팅/처리는 W2.
    body = await request.body()
    if not verify_github_signature(body, x_hub_signature_256, settings.github_webhook_secret):
        raise WebhookVerificationError("invalid or missing X-Hub-Signature-256")

    action: str | None = None
    try:
        payload = json.loads(body)
        if isinstance(payload, dict):
            action = payload.get("action")
    except json.JSONDecodeError:
        pass

    logger.info(
        "github_webhook_received",
        event_type=x_github_event,
        action=action,
        delivery=x_github_delivery,
    )
    return {"status": "received"}
