class GithubApiError(Exception):
    pass


class MemberNotRegisteredError(Exception):
    """폼 제출 이메일이 Members.xlsx에 없음. 비활성 컬럼이 없으므로 미등재 = 거부(403)."""

    def __init__(self, email: str) -> None:
        self.email = email
        super().__init__(f"등록되지 않은 베타 테스터입니다: {email}")


class LLMNotApplicableError(Exception):
    pass


class PRCreationError(Exception):
    pass


class SheetSyncError(Exception):
    pass


class WebhookVerificationError(Exception):
    pass
