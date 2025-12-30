type RuntimeConfig = {
  VITE_API_BASE_URL?: string;
};

const runtimeConfigHolder = window as typeof window & {
  __RUNTIME_CONFIG__?: RuntimeConfig;
};

export function setRuntimeApiBaseUrl(url: string | undefined) {
  runtimeConfigHolder.__RUNTIME_CONFIG__ = { VITE_API_BASE_URL: url };
}

export function requireRuntimeApiBaseUrl(): string {
  const url = runtimeConfigHolder.__RUNTIME_CONFIG__?.VITE_API_BASE_URL;
  if (!url) {
    throw new Error("VITE_API_BASE_URL is required but not provided.");
  }
  return url;
}
