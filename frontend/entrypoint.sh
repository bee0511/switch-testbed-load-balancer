#!/bin/sh

# 如果有設定 VITE_API_BASE_URL 環境變數
if [ -n "$VITE_API_BASE_URL" ]; then
  echo "Injecting API URL: $VITE_API_BASE_URL"
  
  # 使用 sed 替換 index.html 中的預設設定
  # 尋找 window.__RUNTIME_CONFIG__ ... 並替換其中的 URL
  sed -i "s|VITE_API_BASE_URL: \".*\"|VITE_API_BASE_URL: \"$VITE_API_BASE_URL\"|g" /usr/share/nginx/html/index.html
fi

# 啟動 Nginx
exec "$@"