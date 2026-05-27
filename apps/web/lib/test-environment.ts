// 브라우저 정보로 test_environment 문자열을 자동 구성한다.
// (이슈 템플릿 "테스트 환경"은 웹 폼에서 자동 채움 — OS / 브라우저 / 해상도 / 타임존)
export function detectTestEnvironment(): string {
  if (typeof window === "undefined") return "";
  const ua = navigator.userAgent;
  const browser = detectBrowser(ua);
  const os = detectOS(ua);
  const resolution = `${window.screen.width}×${window.screen.height}`;
  const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  return [os, browser, resolution, timezone].filter(Boolean).join(" / ");
}

function detectBrowser(ua: string): string {
  if (/Edg\//.test(ua)) return matchVersion(ua, /Edg\/([\d.]+)/, "Edge");
  if (/Chrome\//.test(ua)) return matchVersion(ua, /Chrome\/([\d.]+)/, "Chrome");
  if (/Firefox\//.test(ua)) return matchVersion(ua, /Firefox\/([\d.]+)/, "Firefox");
  if (/Safari\//.test(ua)) return matchVersion(ua, /Version\/([\d.]+)/, "Safari");
  return "Unknown browser";
}

function detectOS(ua: string): string {
  if (/Mac OS X/.test(ua)) return "macOS";
  if (/Windows NT/.test(ua)) return "Windows";
  if (/Android/.test(ua)) return "Android";
  if (/(iPhone|iPad|iPod)/.test(ua)) return "iOS";
  if (/Linux/.test(ua)) return "Linux";
  return "Unknown OS";
}

function matchVersion(ua: string, re: RegExp, name: string): string {
  const m = ua.match(re);
  return m ? `${name} ${m[1]}` : name;
}
