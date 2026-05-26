from fastapi import APIRouter, Request

router = APIRouter()


@router.post("/webhooks")
async def receive_webhook(request: Request) -> dict[str, str]:
    # W0 스텁: GitHub App webhook ping 200 수신 확인용. HMAC 서명 검증·이벤트 라우팅은 W2.
    return {"status": "received"}
