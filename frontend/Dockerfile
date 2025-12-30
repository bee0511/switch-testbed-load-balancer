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

# 4. 建置
RUN npm run build

# --- 生產階段 ---
FROM nginx:alpine

# 複製建置成果
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

# 複製並設定 entrypoint 腳本
COPY entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80

# 設定 Entrypoint
ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
