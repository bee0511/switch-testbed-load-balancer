import type { Machine, MachineListResponse } from "../types";

// 定義一個 interface 來擴充 window 物件
declare global {
  interface Window {
    __RUNTIME_CONFIG__?: {
      VITE_API_BASE_URL: string;
    };
  }
}

// 優先讀取 window.__RUNTIME_CONFIG__，如果沒有才讀取 Vite 環境變數，最後是 localhost
const API_BASE_URL = 
  window.__RUNTIME_CONFIG__?.VITE_API_BASE_URL || 
  import.meta.env.VITE_API_BASE_URL || 
  "http://localhost:8000";

export async function fetchMachines(): Promise<Machine[]> {
  const response = await fetch(`${API_BASE_URL}/machines`);

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  const data = (await response.json()) as MachineListResponse | { machines: Machine[] };
  return data.machines || [];
}