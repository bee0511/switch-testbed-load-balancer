# switch-testbed-load-balancer

![Backend Pulls](https://img.shields.io/docker/pulls/bee000092/switch-testbed-backend.svg)
![Frontend Pulls](https://img.shields.io/docker/pulls/bee000092/switch-testbed-frontend.svg)

A FastAPI-based service for reserving and tracking switch testbed machines.

## API 概覽

| Method | Path | 說明 | 回傳格式 |
| ------ | ---- | ---- | -------- |
| `GET` | `/machines` | 取得 device.yaml 中所有機器的即時狀態，可使用 `vendor`、`model`、`version`、`status=available\|unavailable\|unreachable` 等查詢參數。 | **200**: `{ "machines": Machine[] }`。<br>**4xx/5xx**: `{ "detail": "錯誤說明" }`。若無符合條件的機器，`machines` 為空陣列。|
| `POST` | `/reserve/{vendor}/{model}/{version}` | 將符合條件且目前可用的其中一台機器標記為 `unavailable` 並回傳詳細資訊。| **200**: `Machine`。<br>**404**: `{ "detail": "No available machines for given specification" }`。|
| `POST` | `/release/{serial_number}` | 將機器釋放回 `available` 狀態。 | **200**: `{ "machine": Machine }`。<br>**404**: `{ "detail": "Machine not found" }`。|


`Machine` 物件包含下列欄位，可以參考 [device.yaml](device.yaml)：

```jsonc
{
  "vendor": "cisco",
  "model": "n9k",
  "version": "9.3",
  "ip": "192.168.2.1",
  "port": 7001,
  "serial": "n9kSerial1",
  "available": true,
  "status": "available" // 或 "unavailable", "unreachable"
}
```

## 後端開發環境設置

後端使用 [uv](https://docs.astral.sh/uv/) 作為包管理工具。

### 1. 設定 SSH 憑證

為了讓系統能夠 SSH 連線到設備進行序號驗證,您需要設定登入憑證:

```bash
# 複製憑證範本
cp credentials.yaml.example credentials.yaml

# 編輯 credentials.yaml 並填入每台設備的帳號密碼
# 注意: credentials.yaml 已在 .gitignore 中,不會被推送到 GitHub
```

`credentials.yaml` 格式如下:

```yaml
credentials:
  # 每台設備的序號對應的帳號密碼
  97SQ3QZXPHF:
    username: admin
    password: your_password_here
  
  9EET8R3N8UN:
    username: admin
    password: another_password_here
  
  # ... 其他設備

# 可選: 設定預設憑證(當設備沒有單獨設定時使用)
default:
  username: admin
  password: default_password
```

### 2. 安裝系統依賴

SSH 密碼驗證需要 `sshpass` 工具:

```bash
# Ubuntu/Debian
sudo apt-get install sshpass

# macOS
brew install sshpass
```

### 3. 安裝 Python 套件並啟動

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
   docker-compose up -d
   ```
- 注意: 前端的環境變數 `VITE_API_BASE_URL` 要去 `frontend/Dockerfile` 改成後端的 IP + port, 否則前端沒辦法打 API 到後端
