# --- 建置階段 ---
FROM node:18-slim AS builder

WORKDIR /app

# 設定 npm 參數
RUN npm config set registry https://registry.npmmirror.com/ && \
    npm config set fund false && \
    npm config set audit false

# 1. 先複製依賴定義
COPY package.json package-lock.json* ./

# 2. 安裝依賴
RUN npm ci --silent

# 3. 複製原始碼
COPY . .

# 4. 接收 Build Argument (這是關鍵修改)
# 預設值可以是 localhost，但在 docker-compose 中我們會覆寫它
ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# 5. 建置 (這時候 Vite 會把 ENV 的值寫死進 JS 檔案)
RUN npm run build

# --- 生產階段 ---
FROM nginx:alpine

# 安裝 shell (alpine 預設有 sh，但為了保險)
RUN apk add --no-cache bash

# 複製建置成果
COPY --from=builder /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/nginx.conf

# 複製並設定 entrypoint 腳本
COPY frontend/entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80

# 設定 Entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]