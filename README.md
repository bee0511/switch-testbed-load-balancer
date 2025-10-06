# switch-testbed-load-balancer

![Backend Pulls](https://img.shields.io/docker/pulls/bee000092/switch-testbed-backend.svg)
![Frontend Pulls](https://img.shields.io/docker/pulls/bee000092/switch-testbed-frontend.svg)

A FastAPI-based service for reserving and tracking switch testbed machines.

## API 概覽

| Method | Path | 說明 |
| ------ | ---- | ---- |
| `GET` | `/machines` | 取得 device.yaml 中所有機器的即時狀態，可使用 `vendor`、`model`、`version`、`status=available\|unavailable` 等查詢參數，回傳內容同時包含篩選下拉所需的階層選項。 |
| `GET` | `/get/{vendor}/{model}/{version}` | 將符合條件且目前可用的機器全部標記為 `unavailable` 並回傳詳細資訊。可選擇在查詢參數加入 `count=n` 只保留前 `n` 台。 |
| `POST` | `/release/{serial_number}` | 將機器釋放回 `available` 狀態。 |

> ⚠️ `/get/...` 會改變內部狀態。若只是查詢現況請呼叫 `/machines`。

## 後端開發環境設置

後端使用 [uv](https://docs.astral.sh/uv/) 作為包管理工具。

可透過以下指令安裝必要的 packages 以及將後端啟動:

```bash
make install
make run
```

## 前端開發環境設置

專案根目錄下的 `frontend/` 目錄提供機器狀態看板的 React 應用程式，採用 Vite 建置。

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

## Docker Images

- Docker Hub: [backend](https://hub.docker.com/r/bee000092/switch-testbed-backend), [frontend](https://hub.docker.com/r/bee000092/switch-testbed-frontend)

- Pull:
  ```bash
  docker pull bee000092/switch-testbed-backend:latest
  docker pull bee000092/switch-testbed-frontend:latest
  ```
- Start application:
   ```bash
   docker-compose up -d --no-build --pull always
   ```
