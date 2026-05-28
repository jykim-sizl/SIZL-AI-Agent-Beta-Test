"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FormField, Input } from "@/components/ui/field";
import { setUser } from "@/lib/auth";
import { verifyMember, SubmitError } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!email || !name) {
      setError("이메일과 이름을 모두 입력해주세요.");
      return;
    }
    if (!email.includes("@")) {
      setError("올바른 이메일 주소를 입력해주세요.");
      return;
    }

    // Members.xlsx 대조 — 미등재면 여기서 막힌다. 이름/팀은 명단 값으로 채운다.
    setLoading(true);
    try {
      const member = await verifyMember(email.trim());
      setUser({ email: member.email, name: member.name, team: member.team });
      router.push("/select");
    } catch (err) {
      // 미등록(403) → 등록 페이지로 이동 (이메일·이름 넘김). 그 외는 에러 표시.
      if (err instanceof SubmitError && err.status === 403) {
        const q = new URLSearchParams({ email: email.trim(), name: name.trim() });
        router.push(`/register?${q.toString()}`);
        return;
      }
      setError(err instanceof SubmitError ? err.message : "로그인 중 오류가 발생했습니다.");
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-sizl-surface p-4">
      <Card className="w-full max-w-md">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-lg bg-primary">
            <span className="text-2xl font-bold text-white">S</span>
          </div>
          <h1 className="mb-2 text-2xl font-bold">SIZL Beta Feedback System</h1>
          <p className="text-sm text-muted-foreground">사내 베타테스트 피드백 도구</p>
        </div>

        {error && (
          <div className="mb-4 rounded-md border border-destructive bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <FormField label="회사 이메일" htmlFor="email" required>
            <Input
              id="email"
              type="email"
              placeholder="name@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </FormField>

          <FormField label="이름 (확인용)" htmlFor="name" required>
            <Input
              id="name"
              type="text"
              placeholder="홍길동"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </FormField>

          <Button type="submit" fullWidth className="mt-2" disabled={loading}>
            {loading ? "확인 중..." : "시작하기"}
          </Button>
        </form>

        <p className="mt-4 text-center text-xs text-muted-foreground">
          회사 구성원만 이용 가능합니다.
        </p>
      </Card>
    </div>
  );
}
