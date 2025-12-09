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

這是最推薦的部署方式。

### 1. 準備設定檔

在啟動前，您需要建立設備清單與登入憑證（檔案位於 `backend/config/` 目錄下）：

```bash
# 0. 設定 API Token
cp backend/.env.example backend/.env
# 編輯 backend/.env，填入 API_BEARER_TOKEN

# 1. 複製憑證範本
cp backend/config/credentials.yaml.example backend/config/credentials.yaml

# 2. 編輯 credentials.yaml 填入設備的 SSH 帳號密碼
# (此檔案已被 gitignore，請放心填寫)
nano backend/config/credentials.yaml

# 3. 確認 device.yaml 中定義了您的設備清單
nano backend/config/device.yaml
```

### 2. 啟動服務

```bash
export API_BEARER_TOKEN="your_secure_token"   # 請自行指定，勿提交到 Git
# 拉取最新映像檔並啟動 (預設會 pull)
sudo docker compose up -d

# 如果要用本機程式碼建置映像，改用 --build
sudo docker compose up --build -d
```

服務啟動後：

 - **前端頁面**：http://localhost:8080 (或伺服器 IP:8080)
  - **後端 API 文件**：http://localhost:8000/docs
  - `/health` 為開放端點；其他 API 需要 `Authorization: Bearer $API_BEARER_TOKEN`。
  - 前端頁面右上角可點「輸入 Token」手動填入 Bearer Token（僅儲存在瀏覽器，不會上傳）。

-----

## ⚙️ 設定指南

### 修改後端 API 連線地址 (前端設定)

本專案前端支援 **Runtime Configuration**，這意味著您可以在啟動容器時動態指定後端的 URL，而**不需要重新建置 (Rebuild)** 映像檔。

**方法：修改 `docker-compose.yml`**

找到 `frontend` 服務下的 `environment` 區塊，修改 `VITE_API_BASE_URL`：

```yaml
  frontend:
    image: bee000092/switch-testbed-frontend:latest
    # ...
    environment:
      # 修改此處為實際的後端 IP 或 Domain
      # 注意：這是瀏覽器要連線的地址，請勿填寫 Docker 內部 IP
      - VITE_API_BASE_URL={YOUR_IP_HERE}
```

修改後，只需執行 `sudo docker compose up -d` 即可生效。

設定檔位於 **`backend/config/`** 目錄下：

  - **`backend/config/device.yaml`**：定義設備的靜態資訊 (IP, Port, Serial, Model)。
  - **`backend/config/credentials.yaml`**：定義設備的 SSH 登入資訊。
      - 系統會優先匹配 `serial_number`。
      - 若找不到特定序號的憑證，會使用 `default` 區塊的帳密。

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
# 編輯 .env 填入 API_BEARER_TOKEN

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
# 建立 .env 檔案並填入: VITE_API_BASE_URL=http://localhost:8000
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
