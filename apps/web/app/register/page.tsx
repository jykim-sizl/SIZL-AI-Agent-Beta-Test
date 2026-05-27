"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { FormField, Input } from "@/components/ui/field";
import { setUser } from "@/lib/auth";
import { registerMember, SubmitError } from "@/lib/api";

function RegisterForm() {
  const router = useRouter();
  const params = useSearchParams();
  const [email, setEmail] = useState(params.get("email") ?? "");
  const [name, setName] = useState(params.get("name") ?? "");
  const [team, setTeam] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (!name.trim() || !team.trim() || !email.trim()) {
      setError("이름, 팀, 이메일을 모두 입력해주세요.");
      return;
    }
    if (!email.includes("@")) {
      setError("올바른 이메일 주소를 입력해주세요.");
      return;
    }
    setLoading(true);
    try {
      const member = await registerMember({
        name: name.trim(),
        team: team.trim(),
        email: email.trim(),
      });
      setUser({ email: member.email, name: member.name, team: member.team });
      router.push("/select");
    } catch (err) {
      setError(err instanceof SubmitError ? err.message : "등록 중 오류가 발생했습니다.");
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-sizl-surface p-4">
      <Card className="w-full max-w-md">
        <div className="mb-6 text-center">
          <h1 className="mb-2 text-2xl font-bold">베타 테스터 등록</h1>
          <p className="text-sm text-muted-foreground">
            등록되지 않은 계정입니다. 정보를 입력하면 등록 후 바로 시작합니다.
          </p>
        </div>

        {error && (
          <div className="mb-4 rounded-md border border-destructive bg-destructive/10 px-4 py-3 text-sm text-destructive">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <FormField label="이름" htmlFor="name" required>
            <Input id="name" placeholder="홍길동" value={name} onChange={(e) => setName(e.target.value)} />
          </FormField>
          <FormField label="팀" htmlFor="team" required>
            <Input id="team" placeholder="예: Neo Lab" value={team} onChange={(e) => setTeam(e.target.value)} />
          </FormField>
          <FormField label="회사 이메일" htmlFor="email" required>
            <Input id="email" type="email" placeholder="name@company.com" value={email} onChange={(e) => setEmail(e.target.value)} />
          </FormField>
          <Button type="submit" fullWidth className="mt-2" disabled={loading}>
            {loading ? "등록 중..." : "등록하고 시작하기"}
          </Button>
        </form>

        <p className="mt-4 text-center text-xs text-muted-foreground">
          이미 등록된 계정이라면{" "}
          <Link href="/" className="text-primary hover:underline">
            로그인으로 돌아가기
          </Link>
        </p>
      </Card>
    </div>
  );
}

export default function RegisterPage() {
  return (
    <Suspense fallback={null}>
      <RegisterForm />
    </Suspense>
  );
}
