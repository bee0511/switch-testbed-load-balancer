import type { Machine, MachineListResponse } from "../types";

// 定義一個 interface 來擴充 window 物件
declare global {
  interface Window {
    __RUNTIME_CONFIG__?: {
      VITE_API_BASE_URL: string;
    };
  }
}

// 判斷是否為開發模式 (Vite 內建變數)
const isDev = import.meta.env.DEV;

// 設定 API URL 的優先權邏輯
const API_BASE_URL =
  // 1. 如果是開發模式 (npm run dev)，且 .env 有設定，絕對優先使用 .env
  //    (這樣可以無視 index.html 裡面的 localhost 預設值)
  (isDev && import.meta.env.VITE_API_BASE_URL) ||
  
  // 2. 如果是生產環境 (Docker)，優先使用 Runtime Config (由 entrypoint.sh 注入)
  window.__RUNTIME_CONFIG__?.VITE_API_BASE_URL ||
  
  // 3. 如果上述都沒有，嘗試使用 Build time 的環境變數
  import.meta.env.VITE_API_BASE_URL ||
  
  // 4. 最後的備案
  "http://localhost:8000";

export async function fetchMachines(): Promise<Machine[]> {
  const response = await fetch(`${API_BASE_URL}/machines`);

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`);
  }

  const data = (await response.json()) as MachineListResponse | { machines: Machine[] };
  return data.machines || [];
}