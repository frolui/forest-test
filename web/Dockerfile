# ---- build ----
FROM node:20-alpine AS builder
WORKDIR /app

COPY package*.json ./
# если нет package-lock.json — npm ci упадёт; fallback на npm install
RUN npm ci || npm install

COPY . .
RUN npm run build
RUN ls -la /app/dist  # разово: убедимся, что сборка есть

# ---- runtime ----
FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
