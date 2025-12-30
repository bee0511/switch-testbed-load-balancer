/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  // 可以添加更多環境變數
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}

interface RuntimeConfig {
  VITE_API_BASE_URL?: string
}

declare global {
  interface Window {
    __RUNTIME_CONFIG__?: RuntimeConfig
  }
}

export {}
