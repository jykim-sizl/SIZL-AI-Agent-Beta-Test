"use client";

import { useEffect, useState } from "react";

// 베타 기간 임시 클라이언트 인증. 백엔드 연동 전까지 localStorage에 사용자 보관.
// 실제 이메일 검증(Members.xlsx)은 백엔드 연동 task에서 추가된다.
export interface User {
  email: string;
  name: string;
  team?: string;
}

const KEY = "sizl-beta-user";

export function getUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as User;
  } catch {
    return null;
  }
}

export function setUser(user: User): void {
  window.localStorage.setItem(KEY, JSON.stringify(user));
}

export function clearUser(): void {
  window.localStorage.removeItem(KEY);
}

// 로그인 상태를 구독하는 훅. status로 SSR/CSR 불일치를 피한다.
export function useUser() {
  const [user, setUserState] = useState<User | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setUserState(getUser());
    setReady(true);
  }, []);

  return { user, ready };
}
