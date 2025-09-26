# Makefile for switch-testbed-load-balancer

.PHONY: help install install-dev sync clean test lint format run dev build

# 預設目標
help:
	@echo "可用的命令："
	@echo "  install     - 安裝專案依賴"
	@echo "  install-dev - 安裝專案依賴和開發依賴"
	@echo "  sync        - 同步依賴（重新安裝所有套件）"
	@echo "  clean       - 清理快取和虛擬環境"
	@echo "  test        - 運行測試"
	@echo "  format      - 格式化程式碼"
	@echo "  run         - 啟動生產伺服器"
	@echo "  dev         - 啟動開發伺服器（帶自動重載）"
	@echo "  build       - 建置專案"

# 安裝依賴
install:
	uv sync

# 安裝開發依賴
install-dev:
	uv sync --extra dev

# 重新同步所有依賴
sync:
	uv sync --extra dev --refresh

# 清理
clean:
	rm -rf .venv/
	rm -rf __pycache__/
	find . -name "*.pyc" -delete
	find . -name "*.pyo" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + || true

# 測試
test:
	uv run pytest

# 格式化程式碼
format:
	uv run black app/

# 生產環境運行
run:
	uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# 開發環境運行（帶自動重載）
dev:
	uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# 建置專案
build:
	uv build