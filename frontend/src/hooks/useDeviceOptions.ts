import { useEffect, useState } from "react";
import type { DeviceConfig } from "../types";

const API_PATH = "/devices/options";
const DEFAULT_BASE_URL = "http://localhost:8000";

async function requestDeviceOptions(): Promise<DeviceConfig | null> {
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? DEFAULT_BASE_URL;

  const response = await fetch(`${baseUrl}${API_PATH}`);
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  const data = (await response.json()) as DeviceConfig | null;
  return data;
}

export function useDeviceOptions() {
  const [options, setOptions] = useState<DeviceConfig | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    requestDeviceOptions()
      .then((data) => {
        if (!isMounted) {
          return;
        }
        setOptions(data);
      })
      .catch((err: unknown) => {
        console.error(err);
        if (!isMounted) {
          return;
        }
        setError("無法載入設備選項，請稍後再試。");
        setOptions(null);
      })
      .finally(() => {
        if (isMounted) {
          setLoading(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, []);

  return { options, loading, error };
}
