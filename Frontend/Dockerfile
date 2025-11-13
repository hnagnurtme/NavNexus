# ============================
# 🧱 STAGE 1: BUILD
# ============================
FROM node:20-alpine AS build
WORKDIR /app

# Install basic dependencies
RUN apk add --no-cache python3 make g++

# Copy package files
COPY package.json package-lock.json* ./

# Install dependencies with specific npm version and settings
RUN npm install --no-optional --no-audit --no-fund --loglevel error

# Copy source code
COPY . .

# Build the application
RUN npm run build

# ============================
# 🚀 STAGE 2: RUNTIME (nginx)
# ============================
FROM nginx:alpine AS runtime

# Copy build output from build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Create nginx configuration for SPA routing
RUN echo 'server { \
    listen 80; \
    server_name _; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    location /api { \
        proxy_pass http://backend:8080; \
        proxy_http_version 1.1; \
        proxy_set_header Upgrade $http_upgrade; \
        proxy_set_header Connection "upgrade"; \
        proxy_set_header Host $host; \
        proxy_cache_bypass $http_upgrade; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
