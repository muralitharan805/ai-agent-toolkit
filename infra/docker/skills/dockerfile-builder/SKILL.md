# Dockerfile Builder Skill

## Metadata
* **Name:** dockerfile_generation
* **Description:** Expert skill for generating, refactoring, and optimizing standalone Dockerfile configurations following enterprise standards.
* **Target OS Runtimes:** Alpine Linux, Ubuntu (LTS), Debian Slim
* **Scope:** Building highly optimized, secure, OCI-compliant, and cached multi-stage Docker images.

## Core Mandates & Rules

### 1. Mandatory Multi-Stage Builds
Every production Dockerfile must utilize a multi-stage architecture. This separates the build environment (compiling dependencies, installing devPackages) from the minimal execution layer, keeping production images tiny and minimizing vulnerabilities.
* **Stage 1 (Builder):** Install build-essential, clang, git, etc. Compile assets.
* **Stage 2 (Runtime):** Copy *only* runtime files and compiled binaries from the builder. Do not carry over compilers, source code control files, or temporary build dependencies.

### 2. Optimize Build Caching & Layer Minimization
* **Layer Minimization:** Combine logical commands using `&& \` within `RUN` instructions.
* **Dependency Sequencing:** Place instructions that change least frequently (like base image definition, package installation, runtime user setup) at the top of the file. Place instructions that change frequently (like source code `COPY` or compile stages) at the bottom.
* **Deterministic Versioning:** Never use the `latest` tag. Always pin exact semantic versions or specific image digests to ensure deterministic builds (e.g., `postgis/postgis:16-3.5-alpine`).

### 3. Non-Root USER Execution
By default, the container must run as a non-privileged user. Never leave the final stage running as `root`.
* For standard runtimes, use the runtime's unprivileged user (e.g., `USER node` for Node, `USER postgres` for PostgreSQL (UID 70/GID 70), or create a custom service user).
* Always pre-create directories and assign correct permissions (using `chown` and `chmod`) before switching the user.

### 4. Build-Time Metadata (OCI Conformity)
Always include OCI (Open Container Initiative) compliant labels in the final runtime stage:
```dockerfile
LABEL org.opencontainers.image.title="Image Title" \
      org.opencontainers.image.description="Short description" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="Vendor Name" \
      org.opencontainers.image.licenses="MIT"
```

## Reference Template (Alpine-based C Extension compilation)
```dockerfile
# STAGE 1: BUILD ENVIRONMENT (builder)
FROM postgis/postgis:16-3.5-alpine AS builder

# Install build dependencies utilizing cache mount for speed
RUN --mount=type=cache,target=/var/cache/apk \
    apk add --no-cache git build-base clang llvm-dev

WORKDIR /tmp/my-extension
ARG EXTENSION_VERSION=v0.1.0

# Clone and compile without JIT if clang/llvm JIT mismatch exists
RUN git clone --depth 1 --branch ${EXTENSION_VERSION} https://github.com/example/ext.git . \
    && make with_llvm=no \
    && make install with_llvm=no

# STAGE 2: RUNTIME ENVIRONMENT
FROM postgis/postgis:16-3.5-alpine
LABEL org.opencontainers.image.title="PostgreSQL Extension Image" \
      org.opencontainers.image.version="16-alpine"

# Copy compiled binaries from builder
COPY --from=builder /usr/local/lib/postgresql/ext.so /usr/local/lib/postgresql/
COPY --from=builder /usr/local/share/postgresql/extension/ext* /usr/local/share/postgresql/extension/

# Harden runtime directories and switch to default postgres non-root UID 70
RUN mkdir -p /var/lib/postgresql/data /var/run/postgresql \
    && chown -R postgres:postgres /var/lib/postgresql/data /var/run/postgresql \
    && chmod 700 /var/lib/postgresql/data \
    && chmod 775 /var/run/postgresql

USER postgres
EXPOSE 5432
```
