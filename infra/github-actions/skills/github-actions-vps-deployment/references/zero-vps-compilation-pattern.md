# Zero-VPS Compilation Deployment Pattern

## Overview
Compiling large TypeScript, Rust, or Go applications directly on cost-effective, low-RAM VPS servers (e.g. 1GB or 2GB VPS droplets) frequently exhausts system memory, leading to swap thrashing, unkillable out-of-memory (OOM) kernel panics, and production downtime.

The **Zero-VPS Compilation Pattern** offloads all image compilation to local machines or GitHub Actions runners, using the remote server strictly to pull pre-built images.

---

## 1. Remote Build & Push Phase
Images are built in CI/CD or locally and pushed to Docker Hub:
```bash
# Build production runner stage
docker build --target runner -t username/my-app:latest .

# Push image to registry
docker push username/my-app:latest
```

---

## 2. Remote VPS Execution Phase
The SSH deployment script navigates to the project directory, pulls the new image layer, restarts the service, and cleans up dangling layers:

```bash
cd /home/deployer/my-app
git pull origin main

# Deploy pulling pre-built image with zero VPS compilation
docker compose -f docker-compose.yml -f docker-compose.existing-infra.yml -f docker-compose.repo.yml up -d --pull always

# Prune dangling layers to prevent disk exhaustion
docker image prune -f
```

---

## 3. Server Disk Hygiene
Each new Docker deployment leaves older image layers on disk. Without automated pruning, VPS disk space will gradually fill up, eventually halting Docker daemon execution. Appending `docker image prune -f` guarantees zero disk leaks.
