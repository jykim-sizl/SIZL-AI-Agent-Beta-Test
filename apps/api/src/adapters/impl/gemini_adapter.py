from __future__ import annotations

from google import genai
from google.genai import types

from src.core.logging import logger
from src.models.analysis_result import AnalysisResult
from src.models.bug_report import BugReport
from src.services.llm.port import LLMPort, PRCloseContext

# 무료 tier 호환 + 한국어 답변 잘 함. 사용 모델은 settings.gemini_model 로 override 가능.
_SYSTEM_PROMPT_CLOSE = """\
당신은 베타테스트 자동화 도구의 마무리 봇입니다.
이슈와 그 분석 PR이 닫힌 상황을 보고, 제보자에게 이슈 페이지에 남길 \
'마무리 코멘트'를 한국어 마크다운으로 작성하세요.

형식 가이드:
- 첫 줄: ✅ (머지=완료) 또는 ⚠️ (언머지=철회) 한 줄 요약 + PR 번호
- 'Root cause' 또는 '추정 원인': 이슈 본문에서 합리적으로 추정 (확신 없으면 가설로 표시)
- 'Fix' 또는 '대응': PR 본문/타이틀에서 유추 (코드 변경 정보가 부족하면 그렇게 명시)
- 'Retest': 제보자가 다시 확인해야 할 1~2가지 안내
- 마지막: 'Closed without merge' 라면 새 이슈 재제출 부탁 한 줄

5~10 줄로 간결하게. 추측은 명시적으로 (가설/추정). 절대 거짓 fact 만들지 말 것.
GitHub Markdown 이라 ``` 코드 블록 사용 가능.
"""


class GeminiAdapter(LLMPort):
    """Google AI Studio (Gemini Flash) 기반 LLM. PR-close 코멘트 풍부화에 사용.

    bug 분석(analyze) 은 W3 본격 작업 전까지 미구현 상태로 둔다 — 현재는
    PR-close 코멘트만 LLM 으로 풍부화.
    """

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def analyze(self, bug_report: BugReport) -> AnalysisResult:
        raise NotImplementedError("Bug 분석은 W3 작업으로 보류 (Anthropic API 키 도착 후)")

    def is_healthy(self) -> bool:
        # 가벼운 ping — 빈 텍스트 생성으로 연결만 확인.
        try:
            self._client.models.generate_content(model=self._model, contents="ping")
            return True
        except Exception as exc:  # noqa: BLE001 - is_healthy 는 진단용
            logger.warning("gemini_unhealthy", error=str(exc))
            return False

    def summarize_pr_close(self, ctx: PRCloseContext) -> str | None:
        # GitHub PR/이슈 본문이 길 수 있으니 보호적으로 잘라 보냄.
        user = self._build_user_prompt(ctx)
        try:
            resp = self._client.models.generate_content(
                model=self._model,
                contents=user,
                config=types.GenerateContentConfig(
                    system_instruction=_SYSTEM_PROMPT_CLOSE,
                    temperature=0.3,
                    max_output_tokens=600,
                ),
            )
            text = (resp.text or "").strip()
            if not text:
                logger.warning("gemini_empty_response", issue=ctx.issue_number)
                return None
            logger.info("gemini_summary_generated", issue=ctx.issue_number, chars=len(text))
            return text
        except Exception as exc:  # noqa: BLE001 - LLM 실패가 웹훅 200 을 막지 않게
            logger.warning("gemini_call_failed", issue=ctx.issue_number, error=str(exc))
            return None

    @staticmethod
    def _build_user_prompt(ctx: PRCloseContext) -> str:
        state = "merged" if ctx.merged else "closed without merge"
        sha = f" (commit {ctx.merge_commit_sha})" if ctx.merge_commit_sha else ""
        pr_ref = f"PR #{ctx.pr_number}" if ctx.pr_number else "분석 PR"
        # 본문 길이 cap — 토큰 안정성
        issue_body = (ctx.issue_body or "")[:4000]
        pr_body = (ctx.pr_body or "")[:2000]
        return (
            f"[이슈 #{ctx.issue_number}] {ctx.issue_title}\n"
            f"{issue_body}\n\n"
            f"[{pr_ref}] {ctx.pr_title} ({state}{sha})\n"
            f"URL: {ctx.pr_url}\n"
            f"{pr_body}"
        )
