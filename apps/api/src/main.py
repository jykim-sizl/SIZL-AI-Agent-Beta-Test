from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.health import router as health_router
from src.api.issues import router as issues_router
from src.api.members import router as members_router
from src.api.webhooks import router as webhooks_router
from src.core.config import settings
from src.core.exceptions import MemberNotRegisteredError, WebhookVerificationError
from src.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging(settings.log_level)
    yield


app = FastAPI(
    title="SIZL Beta API",
    version="0.1.0",
    lifespan=lifespan,
)

# Phase A: 로컬 웹(Next.js dev :3000)에서의 폼 제출 허용 (ADR-001)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(WebhookVerificationError)
async def webhook_verification_error_handler(
    request: Request, exc: WebhookVerificationError
) -> JSONResponse:
    return JSONResponse(status_code=401, content={"detail": str(exc)})


@app.exception_handler(MemberNotRegisteredError)
async def member_not_registered_error_handler(
    request: Request, exc: MemberNotRegisteredError
) -> JSONResponse:
    return JSONResponse(status_code=403, content={"detail": str(exc)})


app.include_router(health_router)
app.include_router(webhooks_router)
app.include_router(members_router)
app.include_router(issues_router)
