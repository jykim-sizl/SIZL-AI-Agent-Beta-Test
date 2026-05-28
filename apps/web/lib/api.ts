// 백엔드(FastAPI) 호출 클라이언트. Phase A 기본값은 로컬 :8000.
import type { Issue } from "@/lib/mock-issues";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// GET /issues → 구글 시트 기반 실제 이슈 목록.
// 실패는 null 로 구분 (호출자가 '에러' vs '0건' 구분 가능하게).
export async function fetchIssues(): Promise<Issue[] | null> {
  try {
    const res = await fetch(`${API_BASE}/issues`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as Issue[];
  } catch {
    return null;
  }
}

// GET /issues/{n} → GitHub 본문(title + body) — 수정 모달 prefill 용.
export async function fetchIssueDetail(
  number: number,
): Promise<{ title: string; body: string } | null> {
  try {
    const res = await fetch(`${API_BASE}/issues/${number}`, { cache: "no-store" });
    if (!res.ok) return null;
    return (await res.json()) as { title: string; body: string };
  } catch {
    return null;
  }
}

// POST /issues/{n}/close — '닫기' 버튼. 'not_planned' 로 close (= 미반영/철회).
// webhook 이 시트 동기화·자동 코멘트 처리.
export async function closeIssue(number: number): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/issues/${number}/close`, { method: "POST" });
    return res.ok;
  } catch {
    return false;
  }
}

// PATCH /issues/{n} — title/body 갱신 + 추가 의견·첨부를 본문 끝 섹션으로 append.
// (추가 의견은 GitHub 코멘트가 아니라 본문 섹션으로 들어감 — 사용자 결정.)
export async function updateIssue(
  number: number,
  patch: {
    title?: string;
    body?: string;
    additionalComment?: string;
    attachments?: { name: string; dataUrl: string }[];
  },
): Promise<boolean> {
  try {
    const res = await fetch(`${API_BASE}/issues/${number}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch),
    });
    return res.ok;
  } catch {
    return false;
  }
}

export class SubmitError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "SubmitError";
  }
}

// POST /members/verify → { email, name, team }. 미등재면 SubmitError(403).
export async function verifyMember(
  email: string,
): Promise<{ email: string; name: string; team: string }> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/members/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
  } catch {
    throw new SubmitError(0, "서버에 연결할 수 없습니다. 백엔드가 실행 중인지 확인해주세요.");
  }
  if (!res.ok) {
    let detail = "등록되지 않은 계정입니다. 운영자에게 문의해주세요.";
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") detail = body.detail;
    } catch {
      /* ignore */
    }
    throw new SubmitError(res.status, detail);
  }
  return res.json();
}

// POST /members/register → { email, name, team }. (자가등록, 베타)
export async function registerMember(payload: {
  name: string;
  team: string;
  email: string;
}): Promise<{ email: string; name: string; team: string }> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/members/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new SubmitError(0, "서버에 연결할 수 없습니다. 백엔드가 실행 중인지 확인해주세요.");
  }
  if (!res.ok) {
    let detail = `등록에 실패했습니다 (${res.status}).`;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") detail = body.detail;
      else if (res.status === 422) detail = "입력값을 확인해주세요.";
    } catch {
      /* ignore */
    }
    throw new SubmitError(res.status, detail);
  }
  return res.json();
}

// POST /issues → { issueNumber }. 실패 시 SubmitError(status, detail).
export async function submitIssue(
  payload: Record<string, unknown>,
): Promise<{ issueNumber: number }> {
  let res: Response;
  try {
    res = await fetch(`${API_BASE}/issues`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    throw new SubmitError(0, "서버에 연결할 수 없습니다. 백엔드가 실행 중인지 확인해주세요.");
  }

  if (!res.ok) {
    let detail = `요청에 실패했습니다 (${res.status}).`;
    try {
      const body = await res.json();
      if (typeof body?.detail === "string") detail = body.detail;
      else if (res.status === 422) detail = "입력값을 다시 확인해주세요.";
    } catch {
      /* ignore parse error */
    }
    throw new SubmitError(res.status, detail);
  }

  const data = await res.json();
  return { issueNumber: data.issue_number };
}
