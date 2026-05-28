"use client";

import { Card } from "@/components/ui/card";
import { Mermaid } from "@/components/mermaid";

// 전체 흐름 — 이슈 제출부터 자동 마무리까지.
const SYSTEM_FLOW = `flowchart TD
    A[베타 테스터: 폼 제출<br/>버그/개선] --> B{이메일 검증<br/>Members.xlsx}
    B -->|등록 미확인| Z[403 차단]
    B -->|확인| C[GitHub 이슈 생성<br/>bug ~or~ enhance]
    C --> D[구글 시트 기록<br/>Raw Issues / Enhancement]
    C --> E{bug 라벨?}
    E -->|버그| F[자동 분석 PR 생성<br/>auto/issue-N branch<br/>LLM이 본문 작성]
    E -->|개선| G[검토 상태 대기]
    F --> H{PR 처리}
    H -->|merge| I[이슈 코멘트 게시 + 이슈 close<br/>시트 처리상태: 완료]
    H -->|close ~unmerged~| J[이슈 코멘트 게시 + 이슈 close<br/>시트 처리상태: 철회]
    G --> K{이슈 close}
    K -->|completed| L[시트: 검토완료 · 반영]
    K -->|not_planned| M[시트: 검토완료 · 미반영]

    classDef ok fill:#dcfce7,stroke:#16a34a,color:#14532d
    classDef warn fill:#fef3c7,stroke:#f59e0b,color:#78350f
    classDef no fill:#fee2e2,stroke:#dc2626,color:#7f1d1d
    class I,L ok
    class J,M warn
    class Z no
`;

export default function HelpPage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold">도움말</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          이 도구는 베타 테스터의 의견을 자동으로 GitHub · 구글 시트 · 분석 PR 로 흐르게
          연결합니다. 아래 다이어그램과 기능 설명을 먼저 확인해주세요.
        </p>
      </header>

      <Card className="mb-8">
        <h2 className="mb-3 text-lg font-semibold">시스템 흐름</h2>
        <p className="mb-4 text-xs text-muted-foreground">
          이슈를 제출하면 다음 단계로 자동 진행됩니다.
        </p>
        <Mermaid chart={SYSTEM_FLOW} />
      </Card>

      <h2 className="mb-4 text-lg font-semibold">기능 소개</h2>
      <div className="flex flex-col gap-4">
        <Section emoji="🐞" title="버그 신고 (/bug-report)">
          <p>실제 동작이 이상하거나 오류가 난 경우 사용. 다음 정보가 GitHub 이슈로 들어갑니다:</p>
          <ul className="ml-5 mt-2 list-disc text-sm text-gray-700">
            <li><strong>제목</strong>: 이슈 카드/표에 표시될 한 줄 요약</li>
            <li><strong>발생 화면 URL</strong>: 어디서 났는지 (필수)</li>
            <li><strong>심각도 P1~P4</strong>: P1 치명적 → P4 낮음</li>
            <li><strong>재현 절차</strong>: Enter 누르면 다음 단계로 자동 추가</li>
            <li><strong>첨부</strong>: 스크린샷은 Ctrl+V 로도 붙여넣기 가능, 문서 파일도 OK</li>
          </ul>
          <p className="mt-2 text-xs text-muted-foreground">
            제출 시 자동으로 GitHub 이슈가 생성되고, 약 3-5초 후 분석 PR 까지 자동 생성됩니다.
          </p>
        </Section>

        <Section emoji="✨" title="개선 의견 (/enhancement)">
          <p>새로운 기능이나 UX 개선 제안. 버그와 달리 자동 PR 은 생성되지 않고 검토 상태로 대기합니다.</p>
          <p className="mt-2 text-xs text-muted-foreground">
            검토 결과는 운영자가 GitHub 이슈를 close 할 때 자동으로 반영(completed) /
            미반영(not_planned) 으로 시트에 기록됩니다.
          </p>
        </Section>

        <Section emoji="📄" title="내가 제출한 이슈 (/my-issues)">
          <ul className="ml-5 list-disc text-sm text-gray-700">
            <li>상단에 KPI(전체/버그/개선) + 완료율 + 상태별 분포</li>
            <li>검색 · 타입/상태 필터 · 정렬 토글 (최신 수정순 / 번호순)</li>
            <li><strong>수정</strong>: GitHub 본문이 자동으로 prefill 됩니다. 본문 편집 시
              즉시 GitHub 이슈에 반영. 추가 의견·첨부는 본문 끝에 섹션으로 append.</li>
            <li><strong>닫기</strong>: GitHub 이슈가 not_planned 로 close → 시트
              상태가 자동으로 ‘철회’(버그) 또는 ‘검토완료 · 미반영’(개선) 으로 바뀝니다.</li>
          </ul>
        </Section>

        <Section emoji="📊" title="대시보드 (/status)">
          <ul className="ml-5 list-disc text-sm text-gray-700">
            <li>전체 이슈 통계 (KPI + 도넛 2개 + 영역별 막대)</li>
            <li>전체 이슈 표 (제보자 포함) · 정렬 토글 · 페이지네이션 10개씩</li>
            <li><strong>구글 시트 다운로드 (.xlsx)</strong>: 운영자가 직접 시트를 .xlsx 로 받음.
              구글 계정으로 해당 시트에 접근 권한이 있어야 합니다.</li>
          </ul>
        </Section>

        <Section emoji="🤖" title="자동화 (Webhook + LLM)">
          <p>다음 자동 처리는 백엔드(Cloud Run)가 GitHub Webhook 을 받아 수행합니다:</p>
          <ul className="ml-5 mt-2 list-disc text-sm text-gray-700">
            <li><strong>이슈 등록 (버그)</strong> → 빈 분석 PR 생성 + 본문을 Gemini 2.5 Flash 가 작성
              (📌 이슈 요약 / 🔍 추정 원인 / 🛠 점검 포인트 / ✅ 재현 시나리오)</li>
            <li><strong>PR merge</strong> → 이슈에 ✅ 완료 코멘트 + 시트 상태 ‘완료’ + 이슈 close</li>
            <li><strong>PR close (unmerged)</strong> → 이슈에 ⚠️ 철회 코멘트 + 시트 ‘철회’ + 이슈 close</li>
            <li><strong>개선 이슈 close</strong> → state_reason 에 따라 시트 ‘반영’ / ‘미반영’</li>
          </ul>
          <p className="mt-2 text-xs text-muted-foreground">
            LLM 호출이 실패해도 안전한 템플릿 코멘트로 fallback — 시스템이 멈추지 않습니다.
          </p>
        </Section>

        <Section emoji="❓" title="FAQ">
          <p className="font-medium text-gray-900">Q. 제출했는데 내 이슈 목록에 안 보여요.</p>
          <p className="mb-3 text-sm text-gray-700">
            서버 응답이 첫 호출에 느릴 수 있어요(콜드 스타트, 최대 ~10초). 로딩 상태가
            계속 보이면 새로고침. 그래도 안 뜨면 운영자(@jy_kim) 에게 문의.
          </p>
          <p className="font-medium text-gray-900">Q. 자동 PR 본문이 이상해요.</p>
          <p className="mb-3 text-sm text-gray-700">
            LLM(Gemini) 이 작성한 추정 분석입니다. 사람 검토·수정 필수입니다. 잘못된 추측이면
            직접 본문을 고쳐주세요.
          </p>
          <p className="font-medium text-gray-900">Q. 이슈를 잘못 올렸어요.</p>
          <p className="text-sm text-gray-700">
            ‘닫기’ 버튼으로 닫으면 시트가 ‘철회’ / ‘미반영’ 으로 자동 기록됩니다. 새 이슈를
            다시 제출해주세요.
          </p>
        </Section>
      </div>
    </div>
  );
}

function Section({
  emoji,
  title,
  children,
}: {
  emoji: string;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <Card>
      <h3 className="mb-2 flex items-center gap-2 font-semibold">
        <span aria-hidden>{emoji}</span>
        {title}
      </h3>
      <div className="text-sm text-gray-700">{children}</div>
    </Card>
  );
}
