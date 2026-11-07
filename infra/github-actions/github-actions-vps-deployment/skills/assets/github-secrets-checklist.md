# GitHub Repository Deployment Secrets Checklist

Configure these secrets in your GitHub repository under **Settings > Secrets and variables > Actions > New repository secret**:

| Secret Name | Required | Description | Example |
| :--- | :--- | :--- | :--- |
| `SERVER_HOST` | Yes | Target VPS public IP or registered domain | `203.0.113.195` |
| `SERVER_USERNAME` | Yes | Non-root deployment user with docker group access | `deployer` |
| `SERVER_SSH_KEY` | Yes | Private SSH key string (contents of `id_ed25519`) | `-----BEGIN OPENSSH PRIVATE KEY-----...` |
| `SERVER_PORT` | Yes | Target SSH port (default: 22) | `22` |
| `PROJECT_PATH` | Yes | Target application directory path on the VPS | `/home/deployer/my-app` |
