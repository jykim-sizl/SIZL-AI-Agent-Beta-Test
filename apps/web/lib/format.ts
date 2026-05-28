// 시점 문자열 포맷터.
// 입력: ISO date ("YYYY-MM-DD") 또는 ISO datetime ("YYYY-MM-DDTHH:MM" / ":SS")
// 출력: 'YYYY-MM-DD HH:MM' 또는 'YYYY-MM-DD' (시간 없으면 날짜만)

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "";
  const s = String(iso).trim();
  if (!s) return "";
  // datetime: 'YYYY-MM-DDTHH:MM' 의 T 를 공백으로, 초/타임존은 잘라냄.
  if (s.includes("T")) {
    const [d, rest] = s.split("T", 2);
    const hhmm = (rest ?? "").slice(0, 5); // 'HH:MM'
    return hhmm ? `${d} ${hhmm}` : d;
  }
  return s; // 'YYYY-MM-DD' 그대로 (옛 데이터)
}
