import { useCallback, useEffect, useRef, useState } from "react";
import { fetchMachines } from "../api/devices";
import type { Machine } from "../types";

export function useMachineData(token: string | null, pollIntervalMs = 15000) {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [loading, setLoading] = useState<boolean>(true); // 初始讀取設為 true
  const [error, setError] = useState<string | null>(null);
  const isMounted = useRef(false);

  const loadData = useCallback(async (isPolling = false) => {
    if (!token) {
      // 沒有 token 就不用打 API
      if (isMounted.current) {
        setLoading(false);
        setError("請先輸入 API Token");
        setMachines([]);
      }
      return;
    }

    if (!isPolling) setLoading(true);
    setError(null);

    try {
      const data = await fetchMachines(token);
      if (isMounted.current) {
        setMachines(data);
      }
    } catch (err) {
      console.error(err);
      if (isMounted.current) {
        setError(
          err instanceof Error
            ? err.message
            : "無法連線至伺服器，請檢查網路或後端狀態。",
        );
      }
    } finally {
      if (isMounted.current && !isPolling) {
        setLoading(false);
      }
    }
  }, [token]);

  useEffect(() => {
    isMounted.current = true;
    loadData();

    const timer =
      token != null ? window.setInterval(() => loadData(true), pollIntervalMs) : null;

    return () => {
      isMounted.current = false;
      if (timer) clearInterval(timer);
    };
  }, [loadData, pollIntervalMs, token]);

  return { machines, loading, error, refresh: () => loadData(false) };
}
