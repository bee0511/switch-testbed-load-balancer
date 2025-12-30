import type { Machine, MachineListResponse } from "../types";
import { requireRuntimeApiBaseUrl } from "../runtimeConfig";

const API_BASE_URL = requireRuntimeApiBaseUrl();

export async function fetchMachines(token?: string | null): Promise<Machine[]> {
  const headers: HeadersInit = token ? { Authorization: `Bearer ${token}` } : {};
  const response = await fetch(`${API_BASE_URL}/machines`, { headers });

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("需要有效的 API Token 才能存取機器清單。");
    }
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  const data = (await response.json()) as MachineListResponse | { machines: Machine[] };
  return data.machines || [];
}
