"use client";

import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import api from "@/lib/api";
import type { User } from "@/types";

export function useAuth(requireAuth = true) {
  const router = useRouter();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const logout = useCallback(() => {
    api.clearToken();
    setUser(null);
    router.push("/login");
  }, [router]);

  useEffect(() => {
    const token = api.getToken();
    if (!token) {
      setIsLoading(false);
      if (requireAuth) {
        router.push("/login");
      }
      return;
    }

    let isMounted = true;
    api.getMe()
      .then((data) => {
        if (isMounted) {
          setUser(data as User);
        }
      })
      .catch((err) => {
        console.error("Auth fetch failed:", err);
        if (isMounted) {
          // If token is invalid or expired
          logout();
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [router, requireAuth, logout]);

  return {
    user,
    isLoading,
    isAuthenticated: !!user,
    logout,
  };
}
export default useAuth;
