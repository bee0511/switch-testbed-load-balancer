import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";
import { requireRuntimeApiBaseUrl, setRuntimeApiBaseUrl } from "./runtimeConfig";

// Populate runtime config from Vite env in dev so the app has a single source of API base URL.
if (import.meta.env.DEV) {
  setRuntimeApiBaseUrl(import.meta.env.VITE_API_BASE_URL);
}

requireRuntimeApiBaseUrl();

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
