import type { Machine, MachineListResponse } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://10.192.194.121:8000";

export async function fetchMachines(): Promise<Machine[]> {
  const response = await fetch(`${API_BASE_URL}/machines`);

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  const data = (await response.json()) as MachineListResponse | { machines: Machine[] };
  return data.machines || [];
}