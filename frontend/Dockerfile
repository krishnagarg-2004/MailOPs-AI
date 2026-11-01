# syntax=docker/dockerfile:1
# Stage 1: build the frontend
FROM node:18-alpine AS builder

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: serve with nginx, proxying /api to the backend
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY frontend/nginx/default.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

# nginx listens on port 80 inside the container; Compose maps host 3000 -> container 80
CMD ["nginx", "-g", "daemon off;"]
