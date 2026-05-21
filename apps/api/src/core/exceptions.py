class GithubApiError(Exception):
    pass


class LLMNotApplicableError(Exception):
    pass


class PRCreationError(Exception):
    pass


class SheetSyncError(Exception):
    pass


class WebhookVerificationError(Exception):
    pass
