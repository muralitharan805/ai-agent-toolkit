# Container Hardener Skill

## Metadata
* **Name:** security_hardening
* **Description:** Expert skill for conducting security threat audits, non-root system paradigm enforcement, runtime privilege reduction, and secret protection.
* **Scope:** Hardening container definitions to eliminate attack vectors, prevent host system compromises, and manage credentials securely.

## Security Mandates & Implementation Details

### 1. No Root Execution
Running containers as `root` provides attackers with direct paths to escape to the host kernel in case of a runtime escape vulnerability.
* **Switch to Non-Privileged User:** Switch to an explicit non-root user at the end of the runtime stage (e.g. `USER postgres` (UID 70/GID 70), `USER node` (UID 1000/GID 1000), or build a dedicated service account).
* **Pre-create & Permission Folders:** Because unprivileged users cannot write to root-owned directories, always pre-create and configure ownership inside the Dockerfile *before* calling the `USER` directive:
```dockerfile
RUN mkdir -p /var/lib/postgresql/data /var/run/postgresql \
    && chown -R postgres:postgres /var/lib/postgresql/data /var/run/postgresql \
    && chmod 700 /var/lib/postgresql/data \
    && chmod 775 /var/run/postgresql
```

### 2. Build Secrets Protection (BuildKit Secrets)
* **Never use COPY or ARG for secrets:** Doing so embeds tokens, passwords, and SSH keys permanently in the static layers of the final image.
* **Leverage BuildKit Secrets Mounts:** For build-time credentials (such as NPM registry keys or SSH credentials), leverage BuildKit secret mounting:
```dockerfile
# Inside Dockerfile
RUN --mount=type=secret,id=my_secret \
    export SECRET_KEY=$(cat /run/secrets/my_secret) && \
    npm run build
```
Execute with:
```bash
docker build --secret id=my_secret,src=.env .
```

### 3. Resource Allocation & Denial of Service (DoS) Hardening
Heavy operations (such as high-dimensional `pgvector` indexing or heavy compiling) can freeze host systems. Always bound CPU and memory limits inside `docker-compose.yml`:
```yaml
deploy:
  resources:
    limits:
      cpus: '1.5'
      memory: 1500M
```

### 4. Filesystem Hardening & Ports
* **Read-Only Filesystems:** Where possible, make the container root filesystem read-only using `read_only: true` in Compose, and mount specific writable directories (`/tmp`, `/var/run`) as temporary mount points (`tmpfs`).
* **Strict Port Binding:** Bind ports explicitly to `127.0.0.1` in development instead of exposing them globally (e.g., `127.0.0.1:5432:5432`). Expose only the required ports.
