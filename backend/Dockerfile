# 使用官方 Python 3.11 Slim 版本
FROM python:3.11-slim

# 安裝 uv 工具
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 設定環境變數
# 新增 CONFIG_DIR 指向容器內的設定檔路徑
ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_PROJECT_ENVIRONMENT="/app/.venv" \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app \
    CONFIG_DIR="/app/config"

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
RUN uv sync --frozen --no-install-project --no-dev

# 3. 複製程式碼與設定檔
COPY app/ ./app/
RUN mkdir -p /app/config /app/secrets

# 4. 安裝專案本身
RUN uv sync --frozen --no-dev

EXPOSE 8000

# 啟動命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
