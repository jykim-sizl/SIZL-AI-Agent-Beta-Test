"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { clearUser, type User } from "@/lib/auth";

const navItems = [
  { href: "/select", label: "이슈 제출", icon: "✏️", match: ["/select", "/bug-report", "/enhancement"] },
  { href: "/my-issues", label: "내가 제출한 이슈", icon: "📄", match: ["/my-issues"] },
  { href: "/status", label: "대시보드", icon: "📊", match: ["/status"] },
  { href: "/help", label: "도움말", icon: "📖", match: ["/help"] },
];

export function AppSidebar({ user }: { user: User }) {
  const pathname = usePathname();
  const router = useRouter();

  const handleLogout = () => {
    clearUser();
    router.replace("/");
  };

  return (
    <aside className="flex w-60 shrink-0 flex-col border-r border-border bg-white">
      <Link href="/select" className="flex items-center gap-2 px-5 py-5">
        <span className="flex h-8 w-8 items-center justify-center rounded bg-primary text-sm font-bold text-white">
          S
        </span>
        <span className="text-lg font-semibold">SIZL Beta</span>
      </Link>

      <nav className="flex flex-1 flex-col gap-1 px-3">
        {navItems.map((item) => {
          const active = item.match.some(
            (m) => pathname === m || pathname.startsWith(`${m}/`),
          );
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors",
                active
                  ? "bg-primary/10 font-medium text-primary"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900",
              )}
            >
              <span aria-hidden>{item.icon}</span>
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-border px-5 py-4">
        <div className="mb-2 truncate text-sm font-medium">{user.name}</div>
        <div className="mb-3 truncate text-xs text-muted-foreground">{user.email}</div>
        <button
          onClick={handleLogout}
          className="w-full rounded-md border border-border px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900"
        >
          로그아웃
        </button>
      </div>
    </aside>
  );
}
