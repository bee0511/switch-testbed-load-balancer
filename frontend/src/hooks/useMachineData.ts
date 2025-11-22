import { useCallback, useEffect, useRef, useState } from "react";
import { fetchMachines } from "../api/devices";
import type { Machine } from "../types";

export function useMachineData(pollIntervalMs = 15000) {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [loading, setLoading] = useState<boolean>(true); // 初始讀取設為 true
  const [error, setError] = useState<string | null>(null);
  const isMounted = useRef(false);

  const loadData = useCallback(async (isPolling = false) => {
    if (!isPolling) setLoading(true);
    setError(null);

    try {
      const data = await fetchMachines();
      if (isMounted.current) {
        setMachines(data);
      }
    } catch (err) {
      console.error(err);
      if (isMounted.current) {
        setError("無法連線至伺服器，請檢查網路或後端狀態。");
      }
    } finally {
      if (isMounted.current && !isPolling) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    isMounted.current = true;
    loadData();

    const timer = setInterval(() => loadData(true), pollIntervalMs);

    return () => {
      isMounted.current = false;
      clearInterval(timer);
    };
  }, [loadData, pollIntervalMs]);

  return { machines, loading, error, refresh: () => loadData(false) };
}