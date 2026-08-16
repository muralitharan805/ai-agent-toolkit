---
description: "Workflow to set up automated free GitHub Actions SSH deployment for Docker Compose projects. Triggered by 'setup-github-ssh-deploy:', 'deploy-vps:', or '/setup-github-ssh-deploy'."
trigger: manual
---

# Automated GitHub Actions SSH Deployment

## Goal
Automate Docker Compose deployments to a remote VPS server for free using GitHub Actions. The agent will scaffold the CI/CD pipeline and instruct the user on configuring necessary secrets.

## Execution Steps

### Step 1: Detect Project Configuration
1. Inspect the project root to identify the primary Docker Compose file (e.g., `docker-compose.yml`, `docker-compose.prod.yml`, `docker-compose.existing-infra.yml`).
2. Identify the default production branch (e.g., `main` or `master`).

### Step 2: Scaffold GitHub Actions Workflow
The agent MUST create `.github/workflows/deploy.yml` with the following strict structure (adjusting branch names and compose files based on Step 1 detection):

```yaml
name: Deploy to VPS via SSH

on:
  push:
    branches:
      - main
      - master

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Execute SSH Deployment
        uses: appleboy/ssh-action@v1.0.3
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USERNAME }}
          key: ${{ secrets.SERVER_SSH_KEY }}
          port: ${{ secrets.SERVER_PORT }}
          script: |
            cd ${{ secrets.PROJECT_PATH }}
            git pull origin main
            
            # Agent MUST adapt this command based on the detected compose file
            docker compose -f <DETECTED_COMPOSE_FILE> up -d --build
            
            # Clean up dangling images to save server disk space
            docker image prune -f
```

### Step 3: Provide GitHub Secrets Configuration Checklist
After scaffolding the workflow file, the agent **MUST** present the user with a formatted, actionable checklist of secrets they need to add in their GitHub Repository Settings (`Settings > Secrets and variables > Actions > New repository secret`):

- `SERVER_HOST`: The public IP address or domain of the VPS.
- `SERVER_USERNAME`: The SSH user (e.g., `root`, `ubuntu`).
- `SERVER_SSH_KEY`: The raw private SSH key string (e.g., contents of `id_rsa` or `id_ed25519`) for authentication. Ensure the corresponding public key is in `~/.ssh/authorized_keys` on the server.
- `SERVER_PORT`: The SSH port to connect to (e.g., `22`, `2001`).
- `PROJECT_PATH`: The absolute directory path on the VPS where the project is already cloned (e.g., `/home/ubuntu/example-app-backend`).

### Step 4: Update README.md
The agent **MUST** update the target project's `README.md` to include a section documenting the GitHub Actions deployment setup. It should explain how to add the repository secrets and include a table of all the required variables (SERVER_HOST, SERVER_USERNAME, SERVER_PORT, SERVER_SSH_KEY, PROJECT_PATH) with descriptions and examples, so that future maintainers can easily configure the environment.
