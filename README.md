# switch-testbed-load-balancer

A FastAPI-based load balancer for switch testbed management.

## 開發環境設置

本專案使用 [uv](https://docs.astral.sh/uv/) 作為包管理工具。

後端可以透過以下指令開啟:

```bash
make run
```

### 前端 (React) 開發

專案根目錄下的 `frontend/` 目錄提供 ticket 查詢介面的 React 應用程式，採用 Vite 建置。

1. 安裝依賴：

   ```bash
   cd frontend
   npm install
   ```

2. 啟動開發伺服器：

   ```bash
   npm run dev
   ```

   預設於 http://localhost:5173 執行，可透過 `VITE_API_BASE_URL` 環境變數指定後端 API 位址。