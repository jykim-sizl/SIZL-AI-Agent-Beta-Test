"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";

// 접을 수 있는 폼 섹션 카드.
export function Section({
  title,
  defaultOpen = true,
  children,
}: {
  title: string;
  defaultOpen?: boolean;
  children: React.ReactNode;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <Card>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center justify-between"
      >
        <h2 className="text-lg font-semibold">{title}</h2>
        <span className="text-muted-foreground">{open ? "▴" : "▾"}</span>
      </button>
      {open && <div className="mt-4 flex flex-col gap-4">{children}</div>}
    </Card>
  );
}
