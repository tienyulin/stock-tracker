# Frontend Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY frontend/src ./src
COPY frontend/index.html ./
COPY frontend/tsconfig.json ./
COPY frontend/tsconfig.node.json ./
COPY frontend/vite.config.ts ./

# Build the application (clear Vite cache first)
RUN rm -rf node_modules/.vite && npm run build

# Production stage
FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
