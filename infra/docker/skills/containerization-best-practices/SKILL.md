---
name: containerization-best-practices
description: "Best practices for writing production-grade Dockerfiles, multi-stage builds, non-root user execution, caching layers, and minimal container image optimization."
---
# Goal
Guide the agent in authoring secure, lightweight, and fast-building Docker container images for Node.js, Angular, NestJS, and other application stacks.

# Instructions
1. Use official slim or alpine base images (e.g., `node:20-alpine`, `nginx:alpine`).
2. Implement multi-stage builds (`build` stage for compilation, `production` stage for running artifacts) to keep final image size minimal.
3. Leverage Docker build caching by copying dependency manifests (`package.json`, `package-lock.json`) before copying full application source code.
4. Always set a non-root user (e.g., `USER node`) in the final production image stage for security compliance.
5. Include a comprehensive `.dockerignore` file excluding `node_modules`, `.git`, `.env`, and build outputs.

# Examples
Input: Write a Dockerfile for a NestJS production service.
Output:
```dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Stage 2: Production Run
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY package*.json ./
RUN npm ci --only=production
COPY --from=builder /app/dist ./dist

USER node
EXPOSE 3000
CMD ["node", "dist/main.js"]
```

# Constraints
- Do NOT run container processes as `root` in the final production stage.
- Do NOT copy `node_modules` from host system into the container image.
