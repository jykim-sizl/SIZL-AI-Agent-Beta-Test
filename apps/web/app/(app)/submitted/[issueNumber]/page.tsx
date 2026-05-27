"use client";

import { use } from "react";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const ISSUE_REPO =
  process.env.NEXT_PUBLIC_GITHUB_ISSUE_REPO ?? "jykim-sizl/SIZL-AI-Agent-Beta-Test";

export default function SubmittedPage({
  params,
}: {
  params: Promise<{ issueNumber: string }>;
}) {
  const { issueNumber } = use(params);
  const githubUrl = `https://github.com/${ISSUE_REPO}/issues/${issueNumber}`;

  return (
    <div className="flex min-h-[80vh] items-center justify-center p-4">
      <Card className="w-full max-w-md text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-sizl-success/10 text-3xl">
          ✅
        </div>
        <h1 className="mb-2 text-2xl font-bold">제출 완료!</h1>
        <p className="mb-1 text-3xl font-bold text-primary">#{issueNumber}</p>
        <p className="mb-6 text-sm text-muted-foreground">
          이슈가 정상적으로 등록되었습니다.
        </p>
        <div className="flex flex-col gap-2">
          <Link href="/my-issues">
            <Button fullWidth>내가 제출한 이슈 보기</Button>
          </Link>
          <Link href="/select">
            <Button variant="secondary" fullWidth>
              새 이슈 등록하기
            </Button>
          </Link>
        </div>
        <a
          href={githubUrl}
          target="_blank"
          rel="noreferrer"
          className="mt-4 inline-block text-sm text-primary hover:underline"
        >
          GitHub에서 보기 →
        </a>
      </Card>
    </div>
  );
}
