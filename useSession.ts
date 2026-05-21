"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { auth, api } from "@/lib/api";

export function useSession({ redirectIfUnauth = true }: { redirectIfUnauth?: boolean } = {}) {
  const router = useRouter();
  const [state, setState] = useState<{
    loading: boolean;
    authed: boolean;
    username: string | null;
  }>({ loading: true, authed: false, username: null });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const token = auth.getToken();
      if (!token) {
        if (!cancelled) setState({ loading: false, authed: false, username: null });
        if (redirectIfUnauth) router.replace("/login");
        return;
      }
      try {
        const me = await api.me();
        if (!cancelled) setState({ loading: false, authed: true, username: me.username });
      } catch {
        auth.clear();
        if (!cancelled) setState({ loading: false, authed: false, username: null });
        if (redirectIfUnauth) router.replace("/login");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [router, redirectIfUnauth]);

  function logout() {
    auth.clear();
    router.replace("/login");
  }

  return { ...state, logout };
}
