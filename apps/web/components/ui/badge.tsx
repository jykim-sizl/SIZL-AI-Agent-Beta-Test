import { cn } from "@/lib/utils";

export type Priority = "P1" | "P2" | "P3" | "P4";

// 색만으로 심각도/우선순위를 구분 (버그 심각도·개선 우선순위 공통).
const priorityConfig: Record<Priority, string> = {
  P1: "bg-red-100 text-red-900",
  P2: "bg-orange-100 text-orange-900",
  P3: "bg-yellow-100 text-yellow-900",
  P4: "bg-gray-100 text-gray-600",
};

export function PriorityBadge({
  priority,
  className,
}: {
  priority: Priority;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        priorityConfig[priority],
        className,
      )}
    >
      {priority}
    </span>
  );
}

// 버그: received(접수) → in_progress(재현O·PR생성) / cannot_reproduce(재현X·closed)
//        → completed / withdrawn(분석 PR 폐기, ADR 2026-05-28)
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

const statusConfig: Record<IssueStatus, { label: string; className: string }> = {
  received: { label: "접수", className: "text-sky-600" },
  in_progress: { label: "진행중", className: "text-orange-600" },
  cannot_reproduce: { label: "재현 불가", className: "text-gray-500" },
  completed: { label: "완료", className: "text-green-600" },
  withdrawn: { label: "철회", className: "text-purple-600" },
  reviewing: { label: "검토", className: "text-blue-600" },
  reviewed_rejected: { label: "검토완료 · 미반영", className: "text-gray-500" },
  reviewed_accepted: { label: "검토완료 · 반영", className: "text-green-600" },
};

export function StatusBadge({
  status,
  className,
}: {
  status: IssueStatus;
  className?: string;
}) {
  const config = statusConfig[status];
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border border-border bg-gray-50 px-2.5 py-0.5 text-xs font-medium",
        config.className,
        className,
      )}
    >
      {config.label}
    </span>
  );
}
