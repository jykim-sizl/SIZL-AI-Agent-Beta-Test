"use client";

import { useEffect, useId, useState } from "react";

// 가벼운 Mermaid 래퍼. mermaid (~250KB) 는 client-side 에서 dynamic import → /help 진입 시에만 로드.
// 입력: chart (Mermaid DSL 문자열). 출력: 렌더된 SVG.
export function Mermaid({ chart }: { chart: string }) {
  const id = useId().replace(/:/g, "");
  const [svg, setSvg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const mermaid = (await import("mermaid")).default;
        mermaid.initialize({ startOnLoad: false, theme: "default", securityLevel: "loose" });
        const { svg } = await mermaid.render(`mmd-${id}`, chart);
        if (!cancelled) setSvg(svg);
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "다이어그램 렌더 실패");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [chart, id]);

  if (error) {
    return (
      <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-xs text-destructive">
        다이어그램 렌더 실패: {error}
      </div>
    );
  }
  if (!svg) {
    return (
      <div className="rounded-md border border-border bg-gray-50 p-6 text-center text-sm text-muted-foreground">
        다이어그램 불러오는 중…
      </div>
    );
  }
  return (
    <div
      className="overflow-x-auto rounded-md border border-border bg-white p-4"
      // mermaid 가 sanitize 한 SVG. securityLevel:'loose' 라 신뢰. 외부 입력 아님(상수).
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
