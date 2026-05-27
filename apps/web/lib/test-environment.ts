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

export interface TestEnv {
  os: string;
  browser: string;
  device: string;
  network: string;
}

// OS / 브라우저 / 기기 / 네트워크를 개별 필드로 자동 감지한다.
export function detectEnv(): TestEnv {
  if (typeof window === "undefined") {
    return { os: "", browser: "", device: "", network: "" };
  }
  const ua = navigator.userAgent;
  // 일부 브라우저에만 있는 Network Information API
  const conn = (navigator as Navigator & { connection?: { effectiveType?: string } }).connection;
  return {
    os: detectOS(ua),
    browser: detectBrowser(ua),
    device: detectDevice(ua),
    network: conn?.effectiveType ? conn.effectiveType.toUpperCase() : "Unknown",
  };
}

function detectDevice(ua: string): string {
  if (/iPad|Tablet/.test(ua)) return "Tablet";
  if (/(iPhone|Android|Mobile)/.test(ua)) return "Mobile";
  return "Desktop";
}
