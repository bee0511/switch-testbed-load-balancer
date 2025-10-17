# 多階段建置：建置階段
FROM node:18-slim AS builder

# 設定工作目錄
WORKDIR /app

# 設定 npm 配置以加速安裝
RUN npm config set registry https://registry.npmmirror.com/ && \
    npm config set fund false && \
    npm config set audit false && \
    npm config set progress false

# 只複製 package 相關檔案以利用 Docker 快取層
COPY frontend/package.json frontend/package-lock.json* ./

RUN npm cache clean --force && \
    rm -rf node_modules package-lock.json && \
    npm install --silent --no-fund --no-audit
    
# 複製其餘的前端原始碼
COPY frontend/ .

# 設定建置時的環境變數（從 docker-compose.yml 傳入）
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

# 建置應用程式
RUN npm run build

# 生產階段：使用 nginx 提供靜態檔案服務
FROM nginx:alpine

# 複製建置好的檔案到 nginx 目錄
COPY --from=builder /app/dist /usr/share/nginx/html

# 複製 nginx 設定檔案
COPY frontend/nginx.conf /etc/nginx/nginx.conf

# 暴露端口
EXPOSE 80

# 啟動 nginx
CMD ["nginx", "-g", "daemon off;"]