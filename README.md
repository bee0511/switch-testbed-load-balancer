# switch-testbed-load-balancer

![Backend Pulls](https://img.shields.io/docker/pulls/bee000092/switch-testbed-backend.svg)
![Frontend Pulls](https://img.shields.io/docker/pulls/bee000092/switch-testbed-frontend.svg)

A FastAPI-based load balancer for switch testbed management.

## 後端開發環境設置

後端使用 [uv](https://docs.astral.sh/uv/) 作為包管理工具。

可透過以下指令安裝必要的 packages 以及將後端啟動:

```bash
make install
make run
```

## 前端開發環境設置

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

   預設於 http://localhost:5173 執行。