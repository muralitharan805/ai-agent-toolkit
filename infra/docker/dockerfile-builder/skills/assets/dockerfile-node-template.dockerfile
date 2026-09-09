# ==============================================================================
# Production Multi-Stage Dockerfile Template (Node.js / TypeScript / NestJS)
# ==============================================================================

# STAGE 1: Dependency Installation with Layer Caching
FROM node:22-alpine AS deps
RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app
COPY package.json pnpm-lock.yaml ./
RUN --mount=type=cache,target=/root/.cache/pnpm pnpm install --frozen-lockfile

# STAGE 2: Application Compilation
FROM node:22-alpine AS builder
RUN corepack enable && corepack prepare pnpm@latest --activate
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN pnpm build
RUN pnpm prune --prod

# STAGE 3: Minimal Production Execution Layer
FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV PORT=3000

# Copy production artifacts with unprivileged ownership
COPY package.json ./
COPY --from=builder --chown=node:node /app/node_modules ./node_modules
COPY --from=builder --chown=node:node /app/dist ./dist

# Non-root user execution
USER node
EXPOSE ${PORT}

# Native container healthcheck
HEALTHCHECK --interval=15s --timeout=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:${PORT}/api/v1/health || exit 1

CMD ["node", "dist/main.js"]
