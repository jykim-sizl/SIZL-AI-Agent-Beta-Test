import hashlib
import hmac


def verify_github_signature(body: bytes, signature_header: str | None, secret: str) -> bool:
    """X-Hub-Signature-256 헤더가 secret으로 계산한 본문 HMAC-SHA256과 일치하는지 검증."""
    if not signature_header or not signature_header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    received = signature_header.removeprefix("sha256=")
    return hmac.compare_digest(expected, received)
