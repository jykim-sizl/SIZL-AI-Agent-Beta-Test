"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { AppSidebar } from "@/components/app-sidebar";
import { useUser } from "@/lib/auth";

// 로그인한 사용자만 접근하는 영역. 좌측 사이드바 + 본문.
export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, ready } = useUser();
  const router = useRouter();

  useEffect(() => {
    if (ready && !user) {
      router.replace("/");
    }
  }, [ready, user, router]);

  if (!ready || !user) {
    return null;
  }

  return (
    <div className="flex h-screen overflow-hidden">
      <AppSidebar user={user} />
      {/* main만 세로 스크롤 → 사이드바 고정 + 본문 내 sticky(진행 스텝퍼/하단 바) 정상 동작 */}
      <main className="flex-1 overflow-y-auto">{children}</main>
    </div>
  );
}
