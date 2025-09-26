# switch-testbed-load-balancer

A FastAPI-based load balancer for switch testbed management.

## 開發環境設置

本專案使用 [uv](https://docs.astral.sh/uv/) 作為包管理工具。

### 前置需求

確保您已安裝 `uv`：

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 快速開始

1. 複製專案：
```bash
git clone <repository-url>
cd switch-testbed-load-balancer
```

2. 安裝依賴：
```bash
uv sync --extra dev
```

3. 啟動開發伺服器：
```bash
uv run uvicorn app.main:app --reload
```

或者使用 Makefile：
```bash
make dev
```

### 常用命令

使用 `uv`：
```bash
# 安裝依賴
uv sync

# 安裝開發依賴
uv sync --extra dev

# 運行應用
uv run uvicorn app.main:app --reload

# 運行測試
uv run pytest

# 格式化程式碼
uv run black app/

# 程式碼檢查
uv run flake8 app/
uv run mypy app/
```

使用 Makefile：
```bash
make help          # 顯示所有可用命令
make install-dev    # 安裝所有依賴
make dev           # 啟動開發伺服器
make test          # 運行測試
make format        # 格式化程式碼
make lint          # 程式碼檢查
```

### API 文件

啟動伺服器後，您可以在以下位置查看 API 文件：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 專案結構

```
app/
├── __init__.py
├── main.py          # FastAPI 應用主檔案
├── utils.py         # 通用工具函數
├── api/             # API 路由
│   ├── routes_request.py
│   ├── routes_reset.py
│   └── routes_result.py
├── models/          # 資料模型
│   ├── machine.py
│   └── ticket.py
└── services/        # 業務邏輯服務
    ├── machine_manager.py
    ├── task_processor.py
    └── ticket_manager.py
```