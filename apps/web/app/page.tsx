import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-col gap-8">
      <section className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold text-gray-900">베타테스트 피드백 제출</h1>
        <p className="text-sm text-gray-600">
          SIZL Agentic Brain 사용 중 발견한 버그나 개선 아이디어를 알려주세요. 제출 내용은
          GitHub 이슈로 기록되어 처리됩니다.
        </p>
      </section>

      <div className="grid gap-4 sm:grid-cols-2">
        <Link
          href="/bug-report"
          className="flex flex-col gap-2 rounded-lg border border-gray-200 bg-white p-5 transition hover:border-gray-900"
        >
          <span className="text-lg font-medium text-gray-900">🐞 버그 리포트</span>
          <span className="text-sm text-gray-600">
            동작이 의도와 다르거나 오류가 발생한 경우 제보해주세요.
          </span>
        </Link>
        <Link
          href="/enhancement"
          className="flex flex-col gap-2 rounded-lg border border-gray-200 bg-white p-5 transition hover:border-gray-900"
        >
          <span className="text-lg font-medium text-gray-900">✨ 개선 사항</span>
          <span className="text-sm text-gray-600">
            더 편리하거나 강력해질 수 있는 아이디어를 제안해주세요.
          </span>
        </Link>
      </div>

      <p className="rounded-md bg-amber-50 px-4 py-3 text-xs text-amber-800">
        사내 직원만 이용 가능합니다. 제출 시 입력하신 이메일이 구성원 명단과 대조됩니다.
      </p>
    </div>
  );
}
