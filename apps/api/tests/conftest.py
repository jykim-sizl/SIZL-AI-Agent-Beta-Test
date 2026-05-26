import os

# 앱 import 시 Settings()가 요구하는 필수 env를 테스트용 더미로 채운다.
# (os.environ이 .env보다 우선하므로 GITHUB_WEBHOOK_SECRET은 테스트에서 결정적이다.)
_TEST_ENV = {
    "GITHUB_APP_ID": "test-app-id",
    "GITHUB_APP_PRIVATE_KEY_PATH": "test.pem",
    "GITHUB_WEBHOOK_SECRET": "test-secret",
    "GITHUB_TARGET_REPO": "owner/repo",
    "ANTHROPIC_API_KEY": "test-key",
    "GOOGLE_SERVICE_ACCOUNT_JSON_PATH": "test.json",
    "GOOGLE_SPREADSHEET_ID": "test-sheet",
    "SLACK_WEBHOOK_URL": "https://example.com/hook",
}
for _k, _v in _TEST_ENV.items():
    os.environ.setdefault(_k, _v)
