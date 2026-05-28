from __future__ import annotations

from google import genai
from google.genai import types

from src.core.logging import logger
from src.models.analysis_result import AnalysisResult
from src.models.bug_report import BugReport
from src.services.llm.port import IssueOpenContext, LLMPort, PRCloseContext

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

_SYSTEM_PROMPT_PR_OPEN = """\
당신은 베타테스트 자동화 도구의 분석 봇입니다.
사용자가 올린 이슈를 보고, 개발자가 작업을 시작할 수 있도록 \
**분석 PR(빈 PR, 코드 변경 없음)의 본문**을 한국어 마크다운으로 작성하세요.

코드 자체를 보지 못하므로 **추측은 반드시 '추정/가설'로 명시**합니다.
거짓 fact 절대 생성 금지. 정보가 부족하면 '정보 부족' 이라고 적으세요.

형식 (이 섹션 순서 그대로):
## 📌 이슈 요약
> 3~5 줄. 사용자가 무엇을 했고, 무엇을 기대했고, 무엇이 일어났는지.

## 🔍 추정 원인
가설 1~3개. 각 가설은 '가설 N: ...' 으로 시작. 근거(이슈 본문의 어떤 단서)도 같이.

## 🛠 점검 포인트
의심되는 영역/모듈/시점. 코드 모르므로 일반적 도메인 표현으로.

## ✅ 재현 시나리오
이슈 본문에서 추출한 단계. 명시되지 않았으면 '추가 정보 필요' 한 줄.

## 📝 다음 작업 (작업자용)
2~4개 액션 아이템. 체크박스(- [ ]) 형식.

---
끝에 '> 이 본문은 LLM이 자동 생성한 분석 초안입니다. 사람 검토·수정 필수.' 한 줄 + \
'> 관련 이슈: <URL>' 한 줄 (URL 은 user 메시지에서 받음).
"""


class GeminiAdapter(LLMPort):
    """Google AI Studio (Gemini Flash) 기반 LLM. PR 본문(open) + 마무리 코멘트(close) 풍부화."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash") -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def _generate(self, system: str, user: str, *, max_tokens: int) -> str | None:
        try:
            resp = self._client.models.generate_content(
                model=self._model,
                contents=user,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    temperature=0.3,
                    max_output_tokens=max_tokens,
                ),
            )
            text = (resp.text or "").strip()
            return text or None
        except Exception as exc:  # noqa: BLE001 - LLM 실패가 호출 흐름을 막지 않게
            logger.warning("gemini_call_failed", error=str(exc))
            return None

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
        text = self._generate(
            _SYSTEM_PROMPT_CLOSE, self._build_close_prompt(ctx), max_tokens=600
        )
        if text:
            logger.info("gemini_close_generated", issue=ctx.issue_number, chars=len(text))
        return text

    def draft_pr_body(self, ctx: IssueOpenContext) -> str | None:
        text = self._generate(
            _SYSTEM_PROMPT_PR_OPEN, self._build_open_prompt(ctx), max_tokens=1200
        )
        if text:
            logger.info("gemini_pr_body_generated", issue=ctx.issue_number, chars=len(text))
        return text

    @staticmethod
    def _build_close_prompt(ctx: PRCloseContext) -> str:
        state = "merged" if ctx.merged else "closed without merge"
        sha = f" (commit {ctx.merge_commit_sha})" if ctx.merge_commit_sha else ""
        pr_ref = f"PR #{ctx.pr_number}" if ctx.pr_number else "분석 PR"
        issue_body = (ctx.issue_body or "")[:4000]
        pr_body = (ctx.pr_body or "")[:2000]
        return (
            f"[이슈 #{ctx.issue_number}] {ctx.issue_title}\n"
            f"{issue_body}\n\n"
            f"[{pr_ref}] {ctx.pr_title} ({state}{sha})\n"
            f"URL: {ctx.pr_url}\n"
            f"{pr_body}"
        )

    @staticmethod
    def _build_open_prompt(ctx: IssueOpenContext) -> str:
        issue_body = (ctx.issue_body or "")[:6000]
        return (
            f"[이슈 #{ctx.issue_number}] {ctx.issue_title}\n"
            f"이슈 URL: {ctx.issue_url}\n\n"
            f"{issue_body}"
        )
