// 백엔드 연동 전 화면 확인용 목업 데이터. (실제 데이터는 전체 이슈 목록 API로 교체)
export type IssueType = "bug" | "enhancement";

// 버그: received(접수) → in_progress(재현O·PR생성) / cannot_reproduce(재현X·closed) → completed
//       또는 withdrawn(분석 PR이 머지 없이 닫힘, ADR 2026-05-28)
// 개선: reviewing / reviewed_rejected / reviewed_accepted
export type IssueStatus =
  | "received"
  | "in_progress"
  | "cannot_reproduce"
  | "completed"
  | "withdrawn"
  | "reviewing"
  | "reviewed_rejected"
  | "reviewed_accepted";

export type Priority = "P1" | "P2" | "P3" | "P4";

export interface Issue {
  number: number;
  type: IssueType;
  title: string;
  area: string;
  priority: Priority; // 버그=심각도, 개선=우선순위 (공통 P1~P4)
  status: IssueStatus;
  body?: string; // GitHub Issue 본문 (목업 전용; 실데이터 목록엔 없음)
  reporter?: string; // 제보자 (등록자)
  createdAt: string;
  updatedAt: string;
  prNumber?: number;
  prUrl?: string;
  githubUrl: string;
}

export const MOCK_MY_ISSUES: Issue[] = [
  {
    number: 142,
    type: "bug",
    title: "Research agent 응답 중 간헐적으로 빈 결과 반환",
    area: "Research agent",
    priority: "P1",
    status: "in_progress",
    body: "## 요약\n- 테스트 계정: test@company.com\n- 발생 화면: https://app.example.com/agents/research\n\n## 재현 방법\n1. Research agent에 동일 질의를 반복 입력\n2. 5회 중 1~2회 빈 응답 반환\n\n## 예상 / 실제\n- 예상: 항상 검색 결과 반환\n- 실제: 간헐적으로 빈 결과",
    createdAt: "2026-05-26",
    updatedAt: "2026-05-27",
    prNumber: 45,
    githubUrl: "https://github.com/Neolab-test/test/issues/142",
  },
  {
    number: 138,
    type: "bug",
    title: "문서 업로드 시 한글 파일명이 깨짐",
    area: "Document agent",
    priority: "P2",
    status: "received",
    body: "## 요약\n- 발생 화면: https://app.example.com/agents/document\n\n## 재현 방법\n1. 한글 파일명 PDF 업로드\n2. 목록에 파일명이 `??????`로 표시됨",
    createdAt: "2026-05-25",
    updatedAt: "2026-05-25",
    githubUrl: "https://github.com/Neolab-test/test/issues/138",
  },
  {
    number: 124,
    type: "bug",
    title: "특정 PDF 열람 시 멈춤 현상 (재현 시도했으나 실패)",
    area: "Document agent",
    priority: "P3",
    status: "cannot_reproduce",
    body: "## 요약\n- 특정 PDF에서만 멈춘다고 제보되었으나, Playwright 자동 재현에서 동일 증상 확인 불가.\n- 제보자 환경/파일 추가 정보 필요.",
    createdAt: "2026-05-23",
    updatedAt: "2026-05-24",
    githubUrl: "https://github.com/Neolab-test/test/issues/124",
  },
  {
    number: 131,
    type: "enhancement",
    title: "채팅 입력창에 전송 단축키(Cmd+Enter) 추가 요청",
    area: "Chat",
    priority: "P3",
    status: "reviewing",
    body: "## 개선 요청\n- 현재: 전송하려면 마우스로 버튼 클릭해야 함\n- 기대: Cmd+Enter(또는 Ctrl+Enter)로 전송\n\n## 기대 효과\n반복 입력이 많은 사용자의 작업 속도 향상",
    createdAt: "2026-05-24",
    updatedAt: "2026-05-24",
    githubUrl: "https://github.com/Neolab-test/test/issues/131",
  },
  {
    number: 119,
    type: "enhancement",
    title: "ETL 처리 진행률을 % 로 표시했으면 함",
    area: "ETL",
    priority: "P4",
    status: "reviewed_accepted",
    body: "## 개선 요청\n- 현재: 처리 중 스피너만 표시\n- 기대: 0~100% 진행률 표시\n\n## 검토 결과\n반영 예정 (다음 스프린트)",
    createdAt: "2026-05-20",
    updatedAt: "2026-05-23",
    githubUrl: "https://github.com/Neolab-test/test/issues/119",
  },
  {
    number: 115,
    type: "enhancement",
    title: "다크 모드 지원 요청",
    area: "기타",
    priority: "P3",
    status: "reviewed_rejected",
    body: "## 개선 요청\n- 다크 모드 테마 지원\n\n## 검토 결과\n베타 기간 중에는 미반영 (정식 출시 후 재검토)",
    createdAt: "2026-05-19",
    updatedAt: "2026-05-22",
    githubUrl: "https://github.com/Neolab-test/test/issues/115",
  },
  {
    number: 112,
    type: "bug",
    title: "긴 문서 요약 시 마지막 문단이 잘림",
    area: "Document agent",
    priority: "P3",
    status: "completed",
    body: "## 요약\n- 발생 화면: https://app.example.com/agents/document\n\n## 재현 방법\n1. 20페이지 이상 문서 요약 요청\n2. 마지막 문단이 출력에서 누락\n\n## 처리\nPR #30 으로 토큰 한도 처리 수정",
    createdAt: "2026-05-18",
    updatedAt: "2026-05-21",
    prNumber: 30,
    githubUrl: "https://github.com/Neolab-test/test/issues/112",
  },
];

// 전체 이슈(다른 사람 제보 포함) — 대시보드/전체 이슈 목록용
const OTHER_ISSUES: Issue[] = [
  {
    number: 141,
    type: "bug",
    title: "Chat 응답이 중간에 끊김",
    area: "Chat",
    priority: "P1",
    status: "in_progress",
    body: "## 요약\n장문 응답 중 스트리밍이 중단됨.",
    reporter: "김민수 · 데이터팀",
    createdAt: "2026-05-26",
    updatedAt: "2026-05-27",
    prNumber: 44,
    githubUrl: "https://github.com/Neolab-test/test/issues/141",
  },
  {
    number: 140,
    type: "bug",
    title: "ETL 스케줄러가 자정에 두 번 실행됨",
    area: "ETL",
    priority: "P2",
    status: "received",
    body: "## 요약\n자정 크론이 중복 트리거됨.",
    reporter: "이서연 · 플랫폼팀",
    createdAt: "2026-05-26",
    updatedAt: "2026-05-26",
    githubUrl: "https://github.com/Neolab-test/test/issues/140",
  },
  {
    number: 135,
    type: "enhancement",
    title: "검색 결과에 출처 링크 표시",
    area: "Research agent",
    priority: "P2",
    status: "reviewing",
    body: "## 개선 요청\n응답 근거가 된 문서 링크를 함께 표시.",
    reporter: "박지훈 · AI팀",
    createdAt: "2026-05-25",
    updatedAt: "2026-05-25",
    githubUrl: "https://github.com/Neolab-test/test/issues/135",
  },
  {
    number: 133,
    type: "bug",
    title: "로그인 실패 시 에러 메시지가 영어로 나옴",
    area: "Login",
    priority: "P3",
    status: "completed",
    body: "## 요약\n에러 토스트가 i18n 미적용.",
    reporter: "최유나 · 디자인팀",
    createdAt: "2026-05-24",
    updatedAt: "2026-05-26",
    prNumber: 41,
    githubUrl: "https://github.com/Neolab-test/test/issues/133",
  },
  {
    number: 129,
    type: "enhancement",
    title: "Document agent에 파일 다중 업로드 지원",
    area: "Document agent",
    priority: "P3",
    status: "reviewed_accepted",
    body: "## 개선 요청\n여러 문서를 한 번에 업로드.",
    reporter: "김민수 · 데이터팀",
    createdAt: "2026-05-22",
    updatedAt: "2026-05-24",
    githubUrl: "https://github.com/Neolab-test/test/issues/129",
  },
  {
    number: 121,
    type: "bug",
    title: "Research agent 영역에서 새로고침 시 입력 초기화",
    area: "Research agent",
    priority: "P3",
    status: "received",
    body: "## 요약\n새로고침하면 작성 중이던 질의가 사라짐.",
    reporter: "이서연 · 플랫폼팀",
    createdAt: "2026-05-21",
    updatedAt: "2026-05-21",
    githubUrl: "https://github.com/Neolab-test/test/issues/121",
  },
];

export const MOCK_ALL_ISSUES: Issue[] = [
  ...MOCK_MY_ISSUES.map((i) => ({ ...i, reporter: "나" })),
  ...OTHER_ISSUES,
];

