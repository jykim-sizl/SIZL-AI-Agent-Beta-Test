from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, EmailStr, Field

from src.api.deps import MemberServiceDep
from src.core.logging import logger

router = APIRouter()


class VerifyRequest(BaseModel):
    email: EmailStr


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1)
    team: str = Field(min_length=1)
    email: EmailStr


class VerifyResponse(BaseModel):
    email: str
    name: str
    team: str


@router.post("/members/verify", response_model=VerifyResponse)
def verify_member(req: VerifyRequest, members: MemberServiceDep) -> VerifyResponse:
    """로그인 게이트. Members.xlsx 미등재 이메일이면 MemberService가 403을 발생시킨다.
    등재면 이름/팀을 돌려주어 프론트가 세션에 채운다(이름은 명단이 진실).
    """
    member = members.verify(str(req.email))
    logger.info("member_verified", email=member.email, team=member.team)
    return VerifyResponse(email=member.email, name=member.name, team=member.team)


@router.post("/members/register", response_model=VerifyResponse)
def register_member(req: RegisterRequest, members: MemberServiceDep) -> VerifyResponse:
    """자가등록(베타). Members.xlsx에 추가하고 등록된 회원을 반환한다."""
    member = members.register(name=req.name, email=str(req.email), team=req.team)
    logger.info("member_registered", email=member.email, team=member.team)
    return VerifyResponse(email=member.email, name=member.name, team=member.team)
