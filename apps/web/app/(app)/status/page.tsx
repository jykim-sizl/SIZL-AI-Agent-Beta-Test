"use client";

import { useEffect, useMemo, useState } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PriorityBadge, StatusBadge } from "@/components/ui/badge";
import { DonutChart } from "@/components/donut-chart";
import { BugIcon, SparkleIcon } from "@/components/icons";
import { cn } from "@/lib/utils";
import { fetchIssues } from "@/lib/api";
import { type Issue, type IssueStatus, type IssueType } from "@/lib/mock-issues";

// CSV/xlsx 다운로드는 구글 시트 export 로 위임 — STATUS_LABEL 은 더 이상 쓰지 않음.

const TYPE_FILTERS: { value: IssueType | "all"; label: string }[] = [
  { value: "all", label: "전체" },
  { value: "bug", label: "🐞 버그" },
  { value: "enhancement", label: "✨ 개선" },
];

// 운영 시트(원본) — 다운로드 버튼이 이 시트를 .xlsx 로 export 한다.
// 시트는 Google 로그인 + 접근 권한 있는 사람만 받을 수 있음(운영자 그룹).
// TODO: env 로 빼고 싶으면 NEXT_PUBLIC_GOOGLE_SHEET_ID 추가.
const GOOGLE_SHEET_ID = "1PSTO5GFT0RljdTy_uJrl-JTHohspoXMy4-Lybhg9HtA";
const GOOGLE_SHEET_EXPORT_URL = `https://docs.google.com/spreadsheets/d/${GOOGLE_SHEET_ID}/export?format=xlsx`;

export default function StatusPage() {
  const [issues, setIssues] = useState<Issue[] | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [query, setQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<IssueType | "all">("all");
  const [sort, setSort] = useState<"updated" | "number">("updated");

  // 실데이터: 백엔드 GET /issues → 전체 이슈. null = 로딩, [] = 에러/0건.
  useEffect(() => {
    let cancelled = false;
    setIssues(null);
    setLoadError(false);
    fetchIssues().then((all) => {
      if (cancelled) return;
      if (all === null) {
        setLoadError(true);
        setIssues([]);
        return;
      }
      setIssues(all);
    });
    return () => {
      cancelled = true;
    };
  }, [reloadKey]);

  const issuesList = useMemo(() => issues ?? [], [issues]);
  const loading = issues === null;

  const stats = useMemo(() => {
    const bug = issuesList.filter((i) => i.type === "bug");
    const enh = issuesList.filter((i) => i.type === "enhancement");
    const by = (arr: Issue[], s: IssueStatus) => arr.filter((i) => i.status === s).length;
    const resolved = by(bug, "completed") + by(enh, "reviewed_accepted");
    return {
      total: issuesList.length,
      resolved,
      rate: issuesList.length ? Math.round((resolved / issuesList.length) * 100) : 0,
      inProgress: by(bug, "in_progress"),
      pending: by(bug, "received") + by(enh, "reviewing"),
      bugSegments: [
        { label: "접수", value: by(bug, "received"), color: "#0ea5e9" },
        { label: "진행중", value: by(bug, "in_progress"), color: "#f59e0b" },
        { label: "재현 불가", value: by(bug, "cannot_reproduce"), color: "#9ca3af" },
        { label: "완료", value: by(bug, "completed"), color: "#10b981" },
      ],
      enhSegments: [
        { label: "검토", value: by(enh, "reviewing"), color: "#3b82f6" },
        { label: "미반영", value: by(enh, "reviewed_rejected"), color: "#9ca3af" },
        { label: "반영", value: by(enh, "reviewed_accepted"), color: "#10b981" },
      ],
    };
  }, [issuesList]);

  const areaBars = useMemo(() => {
    const m = new Map<string, number>();
    issuesList.forEach((i) => m.set(i.area, (m.get(i.area) ?? 0) + 1));
    const entries = [...m.entries()].sort((a, b) => b[1] - a[1]);
    const max = Math.max(...entries.map(([, c]) => c), 1);
    return { entries, max };
  }, [issuesList]);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    const matched = issuesList.filter((i) => {
      if (typeFilter !== "all" && i.type !== typeFilter) return false;
      if (!q) return true;
      return (
        i.title.toLowerCase().includes(q) ||
        i.area.toLowerCase().includes(q) ||
        (i.reporter ?? "").toLowerCase().includes(q) ||
        `#${i.number}`.includes(q)
      );
    });
    // 최신이 위로. 'updated' = 수정일 desc(동률이면 번호 desc), 'number' = 번호 desc.
    const cmp = (a: Issue, b: Issue): number => {
      if (sort === "updated") {
        const d = b.updatedAt.localeCompare(a.updatedAt);
        return d !== 0 ? d : b.number - a.number;
      }
      return b.number - a.number;
    };
    return [...matched].sort(cmp);
  }, [issuesList, query, typeFilter, sort]);

  // 페이지네이션 (10개씩). 필터·검색·정렬 바뀌면 1페이지로 리셋.
  const PAGE_SIZE = 10;
  const [page, setPage] = useState(0);
  const pageCount = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const pageItems = filtered.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  useEffect(() => {
    setPage(0);
  }, [query, typeFilter, sort]);

  return (
    <div className="mx-auto max-w-6xl px-6 py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-bold">대시보드</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          베타테스트 전체 진행 현황입니다. (개별 상세 내용은 GitHub에서 확인)
        </p>
      </header>

      {/* KPI */}
      <div className="mb-6 grid grid-cols-2 gap-3 lg:grid-cols-4">
        <KpiCard label="전체 등록" value={stats.total} />
        <KpiCard label="완료율" value={`${stats.rate}%`} sub={`완료·반영 ${stats.resolved}건`} accent />
        <KpiCard label="진행중" value={stats.inProgress} />
        <KpiCard label="처리 대기" value={stats.pending} sub="접수 · 검토" />
      </div>

      {/* 도넛 2개 */}
      <div className="mb-6 grid gap-4 md:grid-cols-2">
        <Card>
          <h3 className="mb-4 flex items-center gap-2 font-semibold">
            <BugIcon className="h-4 w-4 text-red-600" /> 버그 처리 현황
          </h3>
          <DonutChart segments={stats.bugSegments} />
        </Card>
        <Card>
          <h3 className="mb-4 flex items-center gap-2 font-semibold">
            <SparkleIcon className="h-4 w-4 text-yellow-600" /> 개선 검토 현황
          </h3>
          <DonutChart segments={stats.enhSegments} />
        </Card>
      </div>

      {/* 영역별 분포 */}
      <Card className="mb-6">
        <h3 className="mb-4 font-semibold">영역별 이슈 수</h3>
        <div className="flex flex-col gap-2">
          {areaBars.entries.map(([area, count]) => (
            <div key={area} className="flex items-center gap-3 text-sm">
              <span className="w-32 shrink-0 truncate text-gray-700">{area}</span>
              <div className="h-4 flex-1 overflow-hidden rounded bg-gray-100">
                <div
                  className="h-full rounded bg-primary/70"
                  style={{ width: `${(count / areaBars.max) * 100}%` }}
                />
              </div>
              <span className="w-6 shrink-0 text-right font-medium text-gray-900">{count}</span>
            </div>
          ))}
        </div>
      </Card>

      {/* 전체 이슈 목록 */}
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
        <h3 className="font-semibold">전체 이슈</h3>
        <Button variant="secondary" onClick={() => window.open(GOOGLE_SHEET_EXPORT_URL, "_blank")}>
          📥 구글 시트 다운로드 (.xlsx)
        </Button>
      </div>

      <div className="mb-4 flex flex-col gap-3">
        <input
          type="text"
          placeholder="제목, 영역, 제보자, #번호로 검색..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-full rounded-md border border-border bg-input-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-ring"
        />
        <div className="flex flex-wrap items-center gap-2">
          {TYPE_FILTERS.map((f) => (
            <button
              key={f.value}
              type="button"
              onClick={() => setTypeFilter(f.value)}
              className={cn(
                "rounded-full border px-3 py-1 text-xs transition-colors",
                typeFilter === f.value
                  ? "border-primary bg-primary/10 font-medium text-primary"
                  : "border-border bg-white text-gray-600 hover:bg-gray-50",
              )}
            >
              {f.label}
            </button>
          ))}
          {/* 정렬 (오른쪽 끝) — 최신이 위로 */}
          <span className="ml-auto text-xs text-muted-foreground">정렬</span>
          {[
            { value: "updated" as const, label: "최신 수정순" },
            { value: "number" as const, label: "번호순" },
          ].map((s) => (
            <button
              key={s.value}
              type="button"
              onClick={() => setSort(s.value)}
              className={cn(
                "rounded-full border px-3 py-1 text-xs transition-colors",
                sort === s.value
                  ? "border-primary bg-primary/10 font-medium text-primary"
                  : "border-border bg-white text-gray-600 hover:bg-gray-50",
              )}
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {loading ? (
        <Card className="py-12 text-center text-sm text-muted-foreground">
          이슈를 불러오는 중…
        </Card>
      ) : loadError ? (
        <Card className="flex flex-col items-center gap-3 py-12 text-sm">
          <span className="text-destructive">
            이슈 목록을 불러오지 못했습니다 (서버 응답 실패).
          </span>
          <Button variant="secondary" onClick={() => setReloadKey((k) => k + 1)}>
            다시 시도
          </Button>
        </Card>
      ) : filtered.length === 0 ? (
        <Card className="py-12 text-center text-sm text-muted-foreground">조건에 맞는 이슈가 없습니다.</Card>
      ) : (
        <div className="overflow-hidden rounded-lg border border-border">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 text-xs text-muted-foreground">
              <tr>
                <th className="px-3 py-2 font-medium">#</th>
                <th className="px-3 py-2 font-medium">유형</th>
                <th className="px-3 py-2 font-medium">제목</th>
                <th className="px-3 py-2 font-medium">영역</th>
                <th className="px-3 py-2 font-medium">우선순위</th>
                <th className="px-3 py-2 font-medium">상태</th>
                <th className="px-3 py-2 font-medium">제보자</th>
                <th className="px-3 py-2 font-medium whitespace-nowrap">등록일</th>
              </tr>
            </thead>
            <tbody>
              {pageItems.map((issue) => (
                <tr key={issue.number} className="border-t border-border hover:bg-gray-50">
                  <td className="px-3 py-2 text-muted-foreground">
                    <a href={issue.githubUrl} target="_blank" rel="noreferrer" className="text-primary hover:underline">
                      #{issue.number}
                    </a>
                  </td>
                  <td className="px-3 py-2">{issue.type === "bug" ? "🐞" : "✨"}</td>
                  <td className="max-w-xs truncate px-3 py-2 text-gray-900">{issue.title}</td>
                  <td className="px-3 py-2 text-gray-600">{issue.area}</td>
                  <td className="px-3 py-2"><PriorityBadge priority={issue.priority} /></td>
                  <td className="px-3 py-2"><StatusBadge status={issue.status} /></td>
                  <td className="px-3 py-2 text-gray-600">{issue.reporter}</td>
                  <td className="px-3 py-2 text-gray-500 whitespace-nowrap">{issue.createdAt}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {!loading && !loadError && filtered.length > PAGE_SIZE && (
        <Pagination page={page} pageCount={pageCount} onPage={setPage} total={filtered.length} />
      )}
    </div>
  );
}

function Pagination({
  page,
  pageCount,
  onPage,
  total,
}: {
  page: number;
  pageCount: number;
  onPage: (p: number) => void;
  total: number;
}) {
  return (
    <div className="mt-4 flex items-center justify-center gap-2 text-sm">
      <button
        type="button"
        onClick={() => onPage(page - 1)}
        disabled={page === 0}
        className="rounded-md border border-border px-3 py-1 text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
      >
        ← 이전
      </button>
      <span className="px-2 text-muted-foreground">
        {page + 1} / {pageCount} <span className="text-xs">({total}건)</span>
      </span>
      <button
        type="button"
        onClick={() => onPage(page + 1)}
        disabled={page >= pageCount - 1}
        className="rounded-md border border-border px-3 py-1 text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
      >
        다음 →
      </button>
    </div>
  );
}

function KpiCard({
  label,
  value,
  sub,
  accent,
}: {
  label: string;
  value: string | number;
  sub?: string;
  accent?: boolean;
}) {
  return (
    <Card className="py-4">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className={cn("mt-1 text-2xl font-bold", accent ? "text-green-600" : "text-gray-900")}>{value}</div>
      {sub && <div className="mt-0.5 text-xs text-muted-foreground">{sub}</div>}
    </Card>
  );
}
