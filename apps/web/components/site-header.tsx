import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="border-b border-gray-200 bg-white">
      <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4">
        <Link href="/" className="text-base font-semibold text-gray-900">
          SIZL 베타테스트 피드백
        </Link>
        <nav className="flex gap-4 text-sm text-gray-600">
          <Link href="/bug-report" className="hover:text-gray-900">
            버그 리포트
          </Link>
          <Link href="/enhancement" className="hover:text-gray-900">
            개선 사항
          </Link>
        </nav>
      </div>
    </header>
  );
}
