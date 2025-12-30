# Switch Testbed Load Balancer (Dev Only)

本倉庫僅用於開發與本地測試。正式部署請使用獨立的 config repo：<https://github.com/bee0511/switch-testbed-load-balancer-config>

## 主要功能
- FastAPI 後端 + React/Vite 前端
- 設備狀態監控、預約、釋放與 SSH 重置
- 前端 runtime config（API URL 不需重建映像即可切換）

## 快速開始（Docker Compose，開發環境）
```bash
# 1) 準備設定檔
cp config/secrets/credentials.yaml.example config/secrets/credentials.yaml
cp config/backend.env.example config/backend.env
cp config/frontend.env.example config/frontend.env
nano config/base/device.yaml            # 填寫設備清單
nano config/secrets/credentials.yaml    # 填寫 SSH 憑證
nano config/backend.env                 # 填 API_BEARER_TOKEN
nano config/frontend.env                # 填 VITE_API_BASE_URL (瀏覽器連到後端的 URL)

# 2) 啟動
docker compose up --build -d
```

啟動後：
- 前端：<http://localhost:8080>
- 後端 API：<http://localhost:8000/docs>
- 除 `/health` 外的 API 會需要 `Authorization: Bearer $API_BEARER_TOKEN` 才可以訪問

## 本地開發（不透過 Compose）
### Backend
```bash
cd backend
uv sync
cp .env.example .env
export CONFIG_DIR=$(realpath ../config/base)
export CREDENTIALS_PATH=$(realpath ../config/secrets/credentials.yaml)
make dev   # 或 uv run uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
cp .env.example .env   # 填 VITE_API_BASE_URL，可沿用 config/frontend.env
npm run dev
```

## 設定檔說明
- `config/base/device.yaml`：設備清單（非敏感）
- `config/secrets/credentials.yaml`：設備 SSH 登入資訊
- `config/backend.env`：後端環境變數（`API_BEARER_TOKEN`）
- `config/frontend.env`：前端 runtime API URL（`VITE_API_BASE_URL`）

## 正式部署
請改用 production config repo：<https://github.com/bee0511/switch-testbed-load-balancer-config>，內含 production compose 與設定範本，會直接拉取 Docker Hub 映像。
