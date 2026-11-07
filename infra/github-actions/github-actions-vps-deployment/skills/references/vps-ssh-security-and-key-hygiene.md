# VPS SSH Security & Deployment Key Hygiene

## Overview
Automated continuous deployment from GitHub Actions to a remote VPS requires establishing an authenticated SSH connection without human intervention. Using hardcoded credentials or insecure root keys creates severe security risks.

---

## 1. Dedicated Deployment Key Generation
Always generate a dedicated, high-entropy SSH key pair specifically for automated deployments. Never reuse personal developer keys:

```bash
# Generate dedicated Ed25519 key pair with descriptive comment
ssh-keygen -t ed25519 -C "github-actions-deploy-key" -f ~/.ssh/github_actions_deploy -N ""
```

---

## 2. Server-Side Installation & Permission Hardening
1. Append the public key to the target user's `authorized_keys`:
   ```bash
   cat ~/.ssh/github_actions_deploy.pub >> ~/.ssh/authorized_keys
   ```
2. Lock down SSH directory permissions:
   ```bash
   chmod 700 ~/.ssh
   chmod 600 ~/.ssh/authorized_keys
   ```
3. Dedicated Deploy User:
   - Create an unprivileged user (e.g., `deployer`) added to the `docker` group:
     ```bash
     sudo useradd -m -s /bin/bash deployer
     sudo usermod -aG docker deployer
     ```
   - Avoid executing automated SSH deployment commands as `root`.

---

## 3. GitHub Repository Secrets Mapping
Store the deployment credentials exclusively under **GitHub > Settings > Secrets and variables > Actions**:

| Secret Name | Description | Example Value |
| :--- | :--- | :--- |
| `SERVER_HOST` | Public IP address or domain of target VPS | `198.51.100.42` |
| `SERVER_USERNAME` | Target SSH account name | `deployer` |
| `SERVER_SSH_KEY` | Private Ed25519 key content | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `SERVER_PORT` | Target SSH port (default or hardened) | `22` or `2222` |
| `PROJECT_PATH` | Absolute path where repo is cloned | `/home/deployer/my-app` |
