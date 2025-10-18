import { useCallback, useEffect, useRef, useState } from "react";
import type { Machine, MachineListResponse } from "../types";

const API_PATH = "/machines";
const DEFAULT_BASE_URL = "http://10.192.194.121:8000";
async function fetchMachines(): Promise<Machine[]> {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_BASE_URL;
  const response = await fetch(`${baseUrl}${API_PATH}`);

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  const payload = (await response.json()) as MachineListResponse | Machine[];
  if (Array.isArray(payload)) {
    return payload;
  }

  return payload.machines ?? [];
}

export function useMachines(pollIntervalMs?: number) {
  const [machines, setMachines] = useState<Machine[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const mountedRef = useRef(false);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const loadMachines = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await fetchMachines();
      if (!mountedRef.current) {
        return;
      }
      setMachines(data);
    } catch (err) {
      console.error(err);
      if (!mountedRef.current) {
        return;
      }
      setError("無法載入機器列表，請稍後再試。");
      setMachines([]);
    } finally {
      if (mountedRef.current) {
        setLoading(false);
      }
    }
  }, []);

  useEffect(() => {
    loadMachines();
  }, [loadMachines]);

  useEffect(() => {
    if (!pollIntervalMs) {
      return;
    }

    const timer = setInterval(() => {
      loadMachines();
    }, pollIntervalMs);

    return () => {
      clearInterval(timer);
    };
  }, [loadMachines, pollIntervalMs]);

  return {
    machines,
    loading,
    error,
    refresh: loadMachines,
  };
}
