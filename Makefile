# Makefile for switch-testbed-load-balancer

# 安裝依賴
install:
	uv sync

# 清理
clean:
	rm -rf .venv/
	rm -rf __pycache__/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + || true

# 生產環境運行
run:
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# 開發環境運行（帶自動重載）
dev:
	uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 建置專案
build:
	uv build