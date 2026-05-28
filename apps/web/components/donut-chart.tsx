// 외부 라이브러리 없이 conic-gradient로 그리는 도넛 차트.
export interface DonutSegment {
  label: string;
  value: number;
  color: string; // CSS 색상
}

export function DonutChart({ segments, size = 132 }: { segments: DonutSegment[]; size?: number }) {
  const total = segments.reduce((sum, s) => sum + s.value, 0);

  let acc = 0;
  const stops = segments
    .filter((s) => s.value > 0)
    .map((s) => {
      const start = (acc / total) * 100;
      acc += s.value;
      const end = (acc / total) * 100;
      return `${s.color} ${start}% ${end}%`;
    })
    .join(", ");
  const background = total > 0 ? `conic-gradient(${stops})` : "#f3f4f6";
  const hole = Math.round(size * 0.58);

  return (
    <div className="flex items-center gap-5">
      <div className="relative shrink-0" style={{ width: size, height: size }}>
        <div className="h-full w-full rounded-full" style={{ background }} />
        <div
          className="absolute inset-0 m-auto flex flex-col items-center justify-center rounded-full bg-white"
          style={{ width: hole, height: hole }}
        >
          <span className="text-xl font-bold">{total}</span>
          <span className="text-[10px] text-muted-foreground">건</span>
        </div>
      </div>
      <ul className="flex flex-col gap-1.5 text-sm">
        {segments.map((s) => (
          <li key={s.label} className="flex items-center gap-2">
            <span className="h-3 w-3 rounded-sm" style={{ background: s.color }} aria-hidden />
            <span className="text-gray-700">{s.label}</span>
            <span className="ml-2 font-medium text-gray-900">{s.value}</span>
            <span className="text-xs text-muted-foreground">
              {total > 0 ? `${Math.round((s.value / total) * 100)}%` : "0%"}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
