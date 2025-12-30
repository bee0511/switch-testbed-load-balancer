# Switch Testbed Load Balancer

![Backend](https://img.shields.io/badge/Backend-FastAPI%20%2B%20uv-009688.svg)
![Frontend](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61DAFB.svg)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED.svg)

一個基於 **FastAPI** (後端) 與 **React** (前端) 的網路設備實驗室管理系統。提供設備狀態監控、自動化預約、以及 SSH 自動重置功能。

## ✨ 主要功能

- **即時狀態監控**：自動 Ping 檢查設備連線狀態 (Available / Unavailable / Unreachable)。
- **自動化預約**：透過 API 鎖定特定規格 (Vendor/Model/Version) 的設備。
- **自動重置機制**：釋放設備時，後端會透過 SSH 自動還原設定並重啟設備。
- **現代化架構**：
  - 後端採用 **Async I/O** 與 **uv** 套件管理，效能優異。
  - 前端採用 **Runtime Configuration**，更改 API 位址無需重新 Build Image。

---

## 🚀 快速開始 (使用 Docker Compose)

本倉庫僅供開發使用，所有設定集中在 `config/`，缺少設定會直接啟動失敗。正式部署請使用獨立的 config repo：https://github.com/bee0511/switch-testbed-load-balancer-config

### 1. 準備設定檔

```bash
# 1) 設備清單 (非敏感)
nano config/base/device.yaml

# 2) 建立 SSH 憑證檔 (已在 .gitignore)
cp config/secrets/credentials.yaml.example config/secrets/credentials.yaml
nano config/secrets/credentials.yaml

# 3) 設定環境變數檔 (本 repo 只提供 development)
cp config/backend.env.example config/backend.env
cp config/frontend.env.example config/frontend.env
nano config/backend.env    # API_BEARER_TOKEN (後端 API 的驗證 Token)
nano config/frontend.env   # VITE_API_BASE_URL (瀏覽器要連線到後端 API 的 URL)
```

### 2. 啟動服務

```bash
# 開發環境 (使用 config/*.env)
sudo docker compose up -d

# 正式環境：請在 config repo (https://github.com/bee0511/switch-testbed-load-balancer-config) 執行該 repo 內的 docker-compose.yml

# 如果要用本機程式碼建置映像，改用 --build
sudo docker compose up --build -d
```

服務啟動後：

 - **前端頁面**：http://localhost:8080 (或伺服器 IP:8080)
  - **後端 API 文件**：http://localhost:8000/docs
  - `/health` 為開放端點；其他 API 需要 `Authorization: Bearer $API_BEARER_TOKEN`。
  - 前端頁面右上角可點「輸入 Token」手動填入 Bearer Token（僅儲存在瀏覽器，不會上傳）。

-----

## 🛠️ 本地開發指南

如果您想貢獻程式碼或進行二次開發。

### 後端 (Backend)

使用 [uv](https://github.com/astral-sh/uv) 進行極速的依賴管理。請先進入 `backend` 目錄：

```bash
cd backend

# 安裝依賴
uv sync

# 設定本地測試用的 API Token (不要提交到版本控制)
cp .env.example .env
# 建議沿用集中設定
export CONFIG_DIR=$(realpath ../config/base)
export CREDENTIALS_PATH=$(realpath ../config/secrets/credentials.yaml)

# 啟動開發伺服器 (自動重載)
make dev
# 或手動執行: uv run uvicorn app.main:app --reload
```

### 前端 (Frontend)

```bash
cd frontend

# 安裝依賴
npm install

# 設定本地開發環境變數
# 建立 .env 檔案並填入: VITE_API_BASE_URL (可直接沿用 config/frontend.env)
cp .env.example .env

# 啟動開發伺服器
npm run dev
```

-----

## 📡 API 概覽

詳細文件請參考 Swagger UI (`/docs`)。

| Method | Endpoint | 描述 |
| :--- | :--- | :--- |
| `GET` | `/machines` | 取得所有機器列表與狀態。支援篩選參數 (`vendor`, `model`, `status`)。 |
| `POST` | `/reserve/{vendor}/{model}/{version}` | 鎖定一台符合規格的可用機器，回傳機器資訊。 |
| `POST` | `/release/{serial_number}` | 釋放機器。系統會背景執行 SSH Reset，機器將短暫變為 `unreachable` 直到重啟完成。 |
| `POST` | `/admin/reload` | 觸發後端重新讀取 `device.yaml` 設定檔。會保留目前被借用機器的狀態，並更新新增/移除的機器。 |
