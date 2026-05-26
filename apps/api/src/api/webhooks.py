from typing import Annotated

from fastapi import APIRouter, Header, Request

from src.core.config import settings
from src.core.exceptions import WebhookVerificationError
from src.core.security import verify_github_signature

router = APIRouter()


@router.post("/webhooks")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: Annotated[str | None, Header()] = None,
) -> dict[str, str]:
    # GitHub App webhook 수신. HMAC 서명 검증 후 수락. 이벤트 라우팅은 W2.
    body = await request.body()
    if not verify_github_signature(body, x_hub_signature_256, settings.github_webhook_secret):
        raise WebhookVerificationError("invalid or missing X-Hub-Signature-256")
    return {"status": "received"}
