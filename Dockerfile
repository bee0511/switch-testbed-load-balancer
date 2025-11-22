# 使用官方 Python 3.11 Slim 版本
FROM python:3.11-slim

# 安裝 uv 工具
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 設定環境變數
# PYTHONUNBUFFERED: 讓 log 直接輸出
# UV_COMPILE_BYTECODE: 編譯 bytecode 加快啟動
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT="/app/.venv" \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    sshpass \
    iputils-ping \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 1. 先複製依賴定義檔 (利用 Docker Cache Layer)
COPY pyproject.toml uv.lock ./

# 2. 安裝依賴 (不包含專案本身，只安裝 packages)
# --frozen: 嚴格依照 lock file
# --no-install-project: 目前只安裝依賴
RUN uv sync --frozen --no-install-project --no-dev

# 3. 複製其餘程式碼
COPY app/ ./app/
COPY credentials.yaml.example ./credentials.yaml.example 
# 注意：credentials.yaml 和 device.yaml 通常透過 volume 掛載，不建議 copy 進去

# 4. 安裝專案本身 (如果有定義 entry points) 或單純同步環境
RUN uv sync --frozen --no-dev

EXPOSE 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 啟動命令 (使用 list 格式)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]