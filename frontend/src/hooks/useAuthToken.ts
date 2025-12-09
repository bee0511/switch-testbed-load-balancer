import { useEffect, useState } from "react";

const STORAGE_KEY = "switch-testbed-api-token";

export function useAuthToken() {
  const [token, setTokenState] = useState<string | null>(() => {
    if (typeof window === "undefined") return null;
    const stored = window.localStorage.getItem(STORAGE_KEY);
    return stored || null;
  });

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (token) {
      window.localStorage.setItem(STORAGE_KEY, token);
    } else {
      window.localStorage.removeItem(STORAGE_KEY);
    }
  }, [token]);

  const setToken = (value: string) => {
    const trimmed = value.trim();
    setTokenState(trimmed ? trimmed : null);
  };

  const clearToken = () => setTokenState(null);

  return { token, setToken, clearToken };
}
