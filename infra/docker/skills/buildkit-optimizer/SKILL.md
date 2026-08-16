# BuildKit Optimizer Skill

## Metadata
* **Name:** performance_tuning
* **Description:** Expert skill for diagnosing slow container build times, reducing bloating image sizes, troubleshooting build caches, and optimizing host resource usage.
* **Scope:** Harnessing BuildKit cache systems, multi-stage layer isolation, and smart cache mounts to create lightning-fast, high-performance container pipelines.

## Build Optimization Guidelines

### 1. BuildKit Cache Mounting
By default, each Docker build step starts from scratch when dependencies change. BuildKit cache mounts persist standard directories between independent build runs.
* **Apt/Apk package caching:** Store downloaded package indexes and packages in host-persisted build caches:
```dockerfile
# Alpine Package Cache
RUN --mount=type=cache,target=/var/cache/apk \
    apk add --no-cache git build-base clang llvm-dev
```
* **Language Package caching:** Map package manager cache directories:
  * *NPM (Node):* `--mount=type=cache,target=/root/.npm`
  * *Composer (PHP):* `--mount=type=cache,target=/root/.composer`
  * *Pip (Python):* `--mount=type=cache,target=/root/.cache/pip`

### 2. Multi-Stage Runtime Slimming
Never ship builds with compiler tools (`gcc`, `g++`, `clang`, `git`, `make`, `llvm`).
* **The "Discard compilers" rule:** Compile all libraries and third-party tools in a builder stage (e.g., `FROM alpine AS builder`).
* **Minimal Runtime Stage:** Start the runtime stage from the smallest possible stable base (e.g., standard Alpine, Debian-slim, Distroless).
* **Targeted COPY:** Copy *only* the compiled `.so` files, node modules, binaries, or config folders into the runtime:
```dockerfile
COPY --from=builder /usr/local/lib/postgresql/vector.so /usr/local/lib/postgresql/
```

### 3. Comprehensive `.dockerignore` Usage
Avoid sending massive context files (such as local database directories, `.git`, `node_modules`, `.env`, or build logs) to the Docker daemon. Keep a `.dockerignore` file in the root context containing:
```text
.git
.gitignore
.env
.env.example
docker-compose.yml
**/.DS_Store
node_modules
dist
build
*.log
```

### 4. Build-Time Resource Constraints
Ensure the build does not choke the host system by utilizing build-time args to scale compilation JIT, parallel jobs (`make -j$(nproc)`), or disable heavy operations if dependencies are missing (e.g., `make with_llvm=no` to compile `pgvector` without massive JIT clang dependencies).
