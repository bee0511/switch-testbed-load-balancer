# switch-testbed-load-balancer

![Backend Pulls](https://img.shields.io/docker/pulls/bee000092/switch-testbed-backend.svg)
![Frontend Pulls](https://img.shields.io/docker/pulls/bee000092/switch-testbed-frontend.svg)

A FastAPI-based service for reserving and tracking switch testbed machines.

## API 概覽

| Method | Path | 說明 | 回傳格式 |
| ------ | ---- | ---- | -------- |
| `GET` | `/machines` | 取得 device.yaml 中所有機器的即時狀態，可使用 `vendor`、`model`、`version`、`status=available\|unavailable` 等查詢參數。 | **200**: `{ "machines": Machine[] }`。<br>**4xx/5xx**: `{ "detail": "錯誤說明" }`。若無符合條件的機器，`machines` 為空陣列。|
| `GET` | `/get/{vendor}/{model}/{version}` | 將符合條件且目前可用的機器全部標記為 `unavailable` 並回傳詳細資訊。| **200**: `Machine`。<br>**404**: `{ "detail": "No available machines for given specification" }`。|
| `POST` | `/release/{serial_number}` | 將機器釋放回 `available` 狀態。 | **200**: `{ "machine": Machine }`。<br>**404**: `{ "detail": "Machine not found" }`。|

> ⚠️ `/get/...` 會改變內部狀態。若只是查詢現況請呼叫 `/machines`。

`Machine` 物件包含下列欄位，可以參考 [device.yaml](device.yaml)：

```jsonc
{
  "vendor": "cisco",
  "model": "n9k",
  "version": "9.3",
  "ip": "192.168.2.1",
  "port": 7001,
  "serial_number": "n9kSerial1",
  "available": true,
  "status": "available" // 或 "unavailable"
}
```

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
