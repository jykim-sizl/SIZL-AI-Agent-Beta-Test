"use client";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

// 세로선 + 채워지는 동그라미 스텝퍼. 스크롤을 따라오도록 sticky.
export function ProgressStepper({
  sections,
  completed,
}: {
  sections: readonly { id: string; title: string }[];
  completed: Record<string, boolean>;
}) {
  const doneCount = sections.filter((s) => completed[s.id]).length;

  return (
    <div className="hidden lg:block">
      <Card className="sticky top-6">
        <h3 className="mb-5 font-semibold">진행 상황</h3>
        <ol className="relative flex flex-col gap-5">
          {/* 동그라미들을 잇는 세로선 */}
          <span className="absolute bottom-3 left-3 top-3 w-px -translate-x-1/2 bg-border" aria-hidden />
          {sections.map((s) => {
            const done = completed[s.id];
            return (
              <li key={s.id} className="relative flex items-center gap-3">
                <span
                  className={cn(
                    "z-10 flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full border-2 text-[11px] transition-colors",
                    done
                      ? "border-sizl-success bg-sizl-success text-white"
                      : "border-border bg-white text-transparent",
                  )}
                >
                  ✓
                </span>
                <span className={cn("text-sm", done ? "font-medium text-foreground" : "text-muted-foreground")}>
                  {s.title}
                </span>
              </li>
            );
          })}
        </ol>
        <div className="mt-6 border-t border-border pt-4 text-xs text-muted-foreground">
          {doneCount} / {sections.length} 작성됨
        </div>
      </Card>
    </div>
  );
}
