"use client";

import { useEffect, useMemo, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FormField, Input, Textarea } from "@/components/ui/field";
import { PriorityBadge, StatusBadge } from "@/components/ui/badge";
import { BugIcon, SparkleIcon } from "@/components/icons";
import { cn } from "@/lib/utils";
import { fetchIssues, fetchIssueDetail, updateIssue } from "@/lib/api";
import { getUser } from "@/lib/auth";
import { type Issue, type IssueStatus, type IssueType } from "@/lib/mock-issues";

const TYPE_FILTERS: { value: IssueType | "all"; label: string }[] = [
  { value: "all", label: "전체" },
  { value: "bug", label: "🐞 버그" },
  { value: "enhancement", label: "✨ 개선" },
];

const STATUS_LABEL: Record<IssueStatus, string> = {
  received: "접수",
  in_progress: "진행중",
  cannot_reproduce: "재현 불가",
  completed: "완료",
  withdrawn: "철회",
  reviewing: "검토",
  reviewed_rejected: "검토완료 · 미반영",
  reviewed_accepted: "검토완료 · 반영",
};

const BUG_STATUSES: IssueStatus[] = [
  "received",
  "in_progress",
  "cannot_reproduce",
  "withdrawn",
  "completed",
];
const ENH_STATUSES: IssueStatus[] = ["reviewing", "reviewed_rejected", "reviewed_accepted"];

function statusesForType(type: IssueType): IssueStatus[] {
  return type === "bug" ? BUG_STATUSES : ENH_STATUSES;
}

export default function MyIssuesPage() {
  const [issues, setIssues] = useState<Issue[]>([]);
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<IssueType | "all">("all");
  const [statusFilter, setStatusFilter] = useState<IssueStatus | "all">("all");
  const [sort, setSort] = useState<"updated" | "number">("updated");
  const [editing, setEditing] = useState<Issue | null>(null);
  const [editComment, setEditComment] = useState("");
  const [editLoading, setEditLoading] = useState(false); // 본문 prefill 중
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState("");

  // 실데이터: 백엔드 GET /issues → 내가 제출한 것(등록자=로그인 이름)만
  useEffect(() => {
    const user = getUser();
    fetchIssues().then((all) => {
      setIssues(user ? all.filter((i) => i.reporter === user.name) : all);
    });
  }, []);

  const kpi = useMemo(() => {
    const bug = issues.filter((i) => i.type === "bug");
    const enh = issues.filter((i) => i.type === "enhancement");
    const countBy = (arr: Issue[], s: IssueStatus) => arr.filter((i) => i.status === s).length;
    const bugDone = countBy(bug, "completed");
    const enhAccepted = countBy(enh, "reviewed_accepted");
    const resolved = bugDone + enhAccepted; // 완료 + 반영
    return {
      total: issues.length,
      bug: bug.length,
      enh: enh.length,
      bugReceived: countBy(bug, "received"),
      bugProgress: countBy(bug, "in_progress"),
      bugCannot: countBy(bug, "cannot_reproduce"),
      bugDone,
      enhReviewing: countBy(enh, "reviewing"),
      enhRejected: countBy(enh, "reviewed_rejected"),
      enhAccepted,
      resolved,
      rate: issues.length ? Math.round((resolved / issues.length) * 100) : 0,
    };
  }, [issues]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const matched = issues.filter((i) => {
      if (typeFilter !== "all" && i.type !== typeFilter) return false;
      if (statusFilter !== "all" && i.status !== statusFilter) return false;
      if (!q) return true;
      return (
        i.title.toLowerCase().includes(q) ||
        i.area.toLowerCase().includes(q) ||
        `#${i.number}`.includes(q)
      );
    });
    // 최신이 위로. 'updated' 는 수정일 desc(동률이면 번호 desc), 'number' 는 번호 desc.
    const cmp = (a: Issue, b: Issue): number => {
      if (sort === "updated") {
        const d = b.updatedAt.localeCompare(a.updatedAt);
        return d !== 0 ? d : b.number - a.number;
      }
      return b.number - a.number;
    };
    return [...matched].sort(cmp);
  }, [issues, query, typeFilter, statusFilter, sort]);

  const statusFilterOptions = typeFilter === "all" ? [] : statusesForType(typeFilter);

  const changeType = (t: IssueType | "all") => {
    setTypeFilter(t);
    setStatusFilter("all");
  };

  const removeIssue = (issue: Issue) => {
    if (window.confirm(`#${issue.number} "${issue.title}" 이슈를 삭제할까요?`)) {
      setIssues((prev) => prev.filter((i) => i.number !== issue.number));
    }
  };

  const openEdit = (issue: Issue) => {
    // 우선 메타만 채워 모달 띄우고 본문은 백엔드에서 비동기로 가져와 prefill.
    setEditing({ ...issue, body: issue.body ?? "" });
    setEditComment("");
    setEditError("");
    setEditLoading(true);
    fetchIssueDetail(issue.number).then((detail) => {
      if (detail) {
        setEditing((cur) =>
          cur && cur.number === issue.number
            ? { ...cur, title: detail.title || cur.title, body: detail.body }
            : cur,
        );
      } else {
        setEditError("본문을 불러오지 못했어요. GitHub 본문 없이 저장하면 빈 본문이 됩니다.");
      }
      setEditLoading(false);
    });
  };

  const saveEdit = async () => {
    if (!editing) return;
    setEditSaving(true);
    setEditError("");
    const ok = await updateIssue(editing.number, {
      title: editing.title,
      body: editing.body ?? "",
      comment: editComment.trim() || undefined,
    });
    if (!ok) {
      setEditError("저장 실패 — GitHub 반영에 실패했어요. 잠시 후 다시 시도해주세요.");
      setEditSaving(false);
      return;
    }
    const today = new Date().toISOString().slice(0, 10);
    setIssues((prev) =>
      prev.map((i) =>
        i.number === editing.number
          ? { ...i, title: editing.title, body: editing.body, updatedAt: today }
          : i,
      ),
    );
    setEditSaving(false);
    setEditing(null);
  };

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold">내가 제출한 이슈</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          내가 제출한 버그 신고와 개선 의견의 현황입니다.
        </p>
      </header>

      {/* KPI 요약 */}
      <div className="mb-4 grid grid-cols-3 gap-3">
        <KpiCard label="전체" value={kpi.total} />
        <KpiCard label="🐞 버그" value={kpi.bug} />
        <KpiCard label="✨ 개선" value={kpi.enh} />
      </div>

      {/* 완료율 (완료 · 반영) */}
      <Card className="mb-4 flex flex-wrap items-center gap-x-4 gap-y-2 py-4">
        <span className="whitespace-nowrap text-sm font-medium text-gray-700">완료율 (완료 · 반영)</span>
        <div className="h-2.5 min-w-[120px] flex-1 overflow-hidden rounded-full bg-gray-100">
          <div className="h-full rounded-full bg-green-500 transition-all" style={{ width: `${kpi.rate}%` }} />
        </div>
        <span className="whitespace-nowrap text-sm font-semibold text-green-600">
          {kpi.rate}% · {kpi.resolved}/{kpi.total}건
        </span>
      </Card>

      {/* 상태별 분포 (버그 / 개선 따로) */}
      <Card className="mb-6 flex flex-col gap-3 py-4">
        <div className="flex flex-wrap items-center gap-x-5 gap-y-1">
          <span className="w-12 text-sm font-medium text-gray-700">버그</span>
          <StatusCount label="접수" value={kpi.bugReceived} className="text-sky-600" />
          <StatusCount label="진행중" value={kpi.bugProgress} className="text-orange-600" />
          <StatusCount label="재현 불가" value={kpi.bugCannot} className="text-gray-500" />
          <StatusCount label="완료" value={kpi.bugDone} className="text-green-600" />
        </div>
        <div className="flex flex-wrap items-center gap-x-5 gap-y-1 border-t border-border pt-3">
          <span className="w-12 text-sm font-medium text-gray-700">개선</span>
          <StatusCount label="검토" value={kpi.enhReviewing} className="text-blue-600" />
          <StatusCount label="미반영" value={kpi.enhRejected} className="text-gray-500" />
          <StatusCount label="반영" value={kpi.enhAccepted} className="text-green-600" />
        </div>
      </Card>

      {/* 검색 + 필터 */}
      <div className="mb-4 flex flex-col gap-3">
        <input
          type="text"
          placeholder="제목, 영역, #번호로 검색..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full rounded-md border border-border bg-input-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring"
        />
        <div className="flex flex-wrap items-center gap-2">
          {TYPE_FILTERS.map((f) => (
            <Chip key={f.value} active={typeFilter === f.value} onClick={() => changeType(f.value)}>
              {f.label}
            </Chip>
          ))}
          {statusFilterOptions.length > 0 && <span className="mx-1 h-4 w-px bg-border" />}
          <Chip
            active={statusFilter === "all"}
            onClick={() => setStatusFilter("all")}
            hidden={statusFilterOptions.length === 0}
          >
            전체
          </Chip>
          {statusFilterOptions.map((s) => (
            <Chip key={s} active={statusFilter === s} onClick={() => setStatusFilter(s)}>
              {STATUS_LABEL[s]}
            </Chip>
          ))}
          {/* 정렬 (오른쪽 끝) — 최신이 위로 */}
          <span className="ml-auto text-xs text-muted-foreground">정렬</span>
          <Chip active={sort === "updated"} onClick={() => setSort("updated")}>
            최신 수정순
          </Chip>
          <Chip active={sort === "number"} onClick={() => setSort("number")}>
            번호순
          </Chip>
        </div>
      </div>

      {/* 목록 */}
      {filtered.length === 0 ? (
        <Card className="py-12 text-center text-sm text-muted-foreground">
          조건에 맞는 이슈가 없습니다.
        </Card>
      ) : (
        <div className="flex flex-col gap-3">
          {filtered.map((issue) => (
            <Card key={issue.number} className="transition-shadow hover:shadow-md">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <span className="text-sm font-semibold text-muted-foreground">#{issue.number}</span>
                <TypeChip type={issue.type} />
                <PriorityBadge priority={issue.priority} />
                <StatusBadge status={issue.status} className="ml-auto" />
              </div>
              <h3 className="mb-2 font-medium text-gray-900">{issue.title}</h3>
              <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                <span className="rounded bg-gray-100 px-2 py-0.5">{issue.area}</span>
                <span>등록 {issue.createdAt}</span>
                <span>· 수정 {issue.updatedAt}</span>
              </div>
              <div className="mt-3 flex flex-wrap items-center gap-4 border-t border-border pt-3 text-xs">
                <a href={issue.githubUrl} target="_blank" rel="noreferrer" className="text-primary hover:underline">
                  GitHub에서 보기 →
                </a>
                {issue.prNumber && issue.prUrl && (
                  <a
                    href={issue.prUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="text-primary hover:underline"
                  >
                    🔗 PR #{issue.prNumber} 보기
                  </a>
                )}
                <div className="ml-auto flex gap-1">
                  <button
                    type="button"
                    onClick={() => openEdit(issue)}
                    className="rounded-md border border-border px-2.5 py-1 text-gray-700 hover:bg-gray-50"
                  >
                    수정
                  </button>
                  <button
                    type="button"
                    onClick={() => removeIssue(issue)}
                    className="rounded-md border border-border px-2.5 py-1 text-destructive hover:bg-destructive/10"
                  >
                    삭제
                  </button>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* 수정 모달 */}
      {editing && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <Card className="max-h-[88vh] w-full max-w-lg overflow-auto">
            <div className="mb-4 flex items-start justify-between">
              <div>
                <h2 className="text-xl font-semibold">이슈 수정 · #{editing.number}</h2>
                <p className="text-sm text-muted-foreground">
                  제목·본문 수정은 GitHub 이슈에 즉시 반영. 추가 의견은 별도 코멘트로 게시.
                </p>
              </div>
              <button onClick={() => setEditing(null)} className="rounded p-2 hover:bg-gray-100" aria-label="닫기">✕</button>
            </div>

            {/* 읽기 전용 메타 (영역·우선순위·처리상태는 시트/운영자 관할) */}
            <div className="mb-4 flex flex-wrap items-center gap-2 rounded-md bg-sizl-surface px-3 py-2 text-xs">
              <span className="rounded bg-gray-100 px-2 py-0.5">{editing.area}</span>
              <PriorityBadge priority={editing.priority} />
              <StatusBadge status={editing.status} />
              <span className="text-muted-foreground">· 등록 {editing.createdAt}</span>
            </div>

            <div className="flex flex-col gap-4">
              <FormField label="제목" htmlFor="edit-title">
                <Input
                  id="edit-title"
                  value={editing.title}
                  onChange={(e) => setEditing({ ...editing, title: e.target.value })}
                  disabled={editLoading || editSaving}
                />
              </FormField>

              <FormField
                label="내용 (GitHub 본문)"
                htmlFor="edit-body"
                hint={editLoading ? "GitHub에서 본문 불러오는 중…" : "마크다운 그대로 편집됩니다."}
              >
                <Textarea
                  id="edit-body"
                  rows={10}
                  className="font-mono text-xs"
                  value={editing.body ?? ""}
                  onChange={(e) => setEditing({ ...editing, body: e.target.value })}
                  disabled={editLoading || editSaving}
                  placeholder={editLoading ? "불러오는 중…" : ""}
                />
              </FormField>

              <FormField
                label="추가 의견 (코멘트로 게시)"
                htmlFor="edit-comment"
                hint="입력하면 GitHub 이슈에 별도 코멘트로 등록됩니다. (본문 수정과 무관)"
              >
                <Textarea
                  id="edit-comment"
                  rows={3}
                  placeholder="추가로 남길 내용이 있다면 적어주세요..."
                  value={editComment}
                  onChange={(e) => setEditComment(e.target.value)}
                  disabled={editSaving}
                />
              </FormField>
            </div>

            {editError && (
              <div className="mt-4 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                {editError}
              </div>
            )}

            <div className="mt-6 flex justify-end gap-2">
              <Button variant="ghost" onClick={() => setEditing(null)} disabled={editSaving}>취소</Button>
              <Button onClick={saveEdit} disabled={editLoading || editSaving}>
                {editSaving ? "저장 중..." : "저장"}
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

function KpiCard({ label, value, accent }: { label: string; value: number; accent?: boolean }) {
  return (
    <Card className="py-4">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className={cn("mt-1 text-2xl font-bold", accent ? "text-green-600" : "text-gray-900")}>{value}</div>
    </Card>
  );
}

function StatusCount({ label, value, className }: { label: string; value: number; className?: string }) {
  return (
    <span className="flex items-center gap-1.5 text-sm">
      <span className={cn("font-semibold", className)}>{value}</span>
      <span className="text-muted-foreground">{label}</span>
    </span>
  );
}

function Chip({
  active,
  onClick,
  hidden,
  children,
}: {
  active: boolean;
  onClick: () => void;
  hidden?: boolean;
  children: React.ReactNode;
}) {
  if (hidden) return null;
  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "rounded-full border px-3 py-1 text-xs transition-colors",
        active
          ? "border-primary bg-primary/10 font-medium text-primary"
          : "border-border bg-white text-gray-600 hover:bg-gray-50",
      )}
    >
      {children}
    </button>
  );
}

function TypeChip({ type }: { type: IssueType }) {
  if (type === "bug") {
    return (
      <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2 py-0.5 text-xs font-medium text-red-700">
        <BugIcon className="h-3.5 w-3.5" /> 버그
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-yellow-50 px-2 py-0.5 text-xs font-medium text-yellow-700">
      <SparkleIcon className="h-3.5 w-3.5" /> 개선
    </span>
  );
}
