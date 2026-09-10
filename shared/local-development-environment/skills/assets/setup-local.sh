#!/usr/bin/env bash
# =============================================================================
# scripts/setup-local.sh — One-Command Local Development Environment Setup
# =============================================================================
# Usage: ./scripts/setup-local.sh
#
# What this script does:
#   1. Copies .env.example → .env (if .env doesn't exist)
#   2. Starts docker compose stack and waits for all services to be healthy
#   3. Installs project dependencies via pnpm
#   4. Runs database migrations
#   5. Seeds development data
#   6. Prints the local service URL table
#
# Prerequisites: Docker Desktop or Docker Engine + Compose v2, pnpm
# =============================================================================

set -euo pipefail

# ─── ANSI colors for output ──────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info()    { echo -e "${BLUE}[INFO]${NC}    $*"; }
log_success() { echo -e "${GREEN}[OK]${NC}      $*"; }
log_warn()    { echo -e "${YELLOW}[WARN]${NC}    $*"; }
log_error()   { echo -e "${RED}[ERROR]${NC}   $*" >&2; }

# ─── Step 1: Copy .env.example → .env if not present ─────────────────────────
log_info "Checking .env file..."
if [ ! -f ".env" ]; then
  if [ ! -f ".env.example" ]; then
    log_error ".env.example not found. Cannot initialize .env. Aborting."
    exit 1
  fi
  cp .env.example .env
  log_success ".env created from .env.example"
  log_warn "Review .env and update any placeholder values before continuing."
else
  log_info ".env already exists — skipping copy"
fi

# ─── Step 2: Start Docker Compose stack with health check wait ────────────────
log_info "Starting Docker Compose stack (waiting for all services to be healthy)..."
docker compose up -d --wait
log_success "All services healthy and running"

# ─── Step 3: Install dependencies ────────────────────────────────────────────
log_info "Installing dependencies via pnpm..."
pnpm install --frozen-lockfile
log_success "Dependencies installed"

# ─── Step 4: Run database migrations ─────────────────────────────────────────
log_info "Running database migrations..."
pnpm db:migrate
log_success "Migrations complete"

# ─── Step 5: Seed development data ───────────────────────────────────────────
log_info "Seeding development data..."
pnpm db:seed:dev
log_success "Development data seeded"

# ─── Step 6: Print local service URL table ────────────────────────────────────
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅  Local development environment is ready!               ${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "  Service          URL"
echo -e "  ───────────────  ─────────────────────────────────────────"
echo -e "  App (dev)        http://localhost:3000"
echo -e "  API Docs         http://localhost:3000/docs"
echo -e "  PostgreSQL       postgresql://myapp:localpassword@localhost:5432/myapp_dev"
echo -e "  Redis            redis://localhost:6379"
echo -e "  RabbitMQ         amqp://myapp:localpassword@localhost:5672"
echo -e "  RabbitMQ UI      http://localhost:15672  (myapp / localpassword)"
echo -e "  Mailhog SMTP     smtp://localhost:1025  (no auth)"
echo -e "  Mailhog Web UI   http://localhost:8025"
echo -e "  Adminer DB UI    http://localhost:8080"
echo ""
echo -e "  Run the app:     pnpm dev"
echo ""
