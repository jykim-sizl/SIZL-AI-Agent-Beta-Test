"use client";

import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";

export default function FormSelectionPage() {
  const router = useRouter();

  return (
    <div className="mx-auto max-w-4xl px-6 py-12">
      <h1 className="mb-8 text-3xl font-bold">어떤 의견을 남기시나요?</h1>

      <div className="grid gap-6 md:grid-cols-2">
        <Card
          className="cursor-pointer p-8 transition-all hover:border-primary hover:shadow-md"
          onClick={() => router.push("/bug-report")}
        >
          <div className="flex flex-col items-center gap-4 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-50 text-3xl">
              🐞
            </div>
            <h2 className="text-xl font-semibold">버그 신고하기</h2>
            <p className="text-sm text-muted-foreground">
              동작이 이상하거나 오류가 발생했을 때
            </p>
          </div>
        </Card>

        <Card
          className="cursor-pointer p-8 transition-all hover:border-primary hover:shadow-md"
          onClick={() => router.push("/enhancement")}
        >
          <div className="flex flex-col items-center gap-4 text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-yellow-50 text-3xl">
              ✨
            </div>
            <h2 className="text-xl font-semibold">개선 의견 내기</h2>
            <p className="text-sm text-muted-foreground">
              더 나은 기능이나 사용 경험을 제안할 때
            </p>
          </div>
        </Card>
      </div>
    </div>
  );
}
