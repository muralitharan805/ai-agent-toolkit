---
name: github-actions-vps-deployment
description: "Universal procedural skill for automated GitHub Actions SSH deployment to remote VPS servers using Docker Compose, Zero-VPS builds, and secret hygiene."
---

# Automated GitHub Actions VPS Deployment Skill

## Purpose
Establishes production-grade CI/CD continuous deployment pipelines using GitHub Actions, SSH key authentication, the Zero-VPS Compilation pattern, pre-built Docker container registry pulling, and automated server disk hygiene.

## Architecture & Tooling Matrix
- **SSH Security & Key Hygiene**: [references/vps-ssh-security-and-key-hygiene.md](references/vps-ssh-security-and-key-hygiene.md)
- **Zero-VPS Compilation Pattern**: [references/zero-vps-compilation-pattern.md](references/zero-vps-compilation-pattern.md)
- **Automated CLI Validator**: [scripts/audit_github_actions_workflow.py](scripts/audit_github_actions_workflow.py)
- **Starter Templates**:
  - Deploy Workflow: [assets/deploy-workflow-template.yml](assets/deploy-workflow-template.yml)
  - Secrets Checklist: [assets/github-secrets-checklist.md](assets/github-secrets-checklist.md)
- **Verification Suite**: [evals/evals.json](evals/evals.json)

---

## Execution Workflow

### Phase 1: Project & Branch Detection
1. Inspect project root to verify git repository configuration and default production branch (`main` or `master`).
2. Verify that Docker Compose files are present (`docker-compose.yml`, `docker-compose.existing-infra.yml`, `docker-compose.repo.yml`).
3. Ensure `.github/workflows/` directory exists.

### Phase 2: Workflow Scaffolding
1. Scaffold `.github/workflows/deploy.yml` using the official `appleboy/ssh-action@v1.0.3` action.
2. Configure workflow triggers to listen for pushes to the primary branch.
3. Parameterize server connection details with GitHub repository secrets:
   - `secrets.SERVER_HOST`
   - `secrets.SERVER_USERNAME`
   - `secrets.SERVER_SSH_KEY`
   - `secrets.SERVER_PORT`
   - `secrets.PROJECT_PATH`

### Phase 3: Zero-VPS Compilation Execution Command
1. In the remote script payload, pull latest repository changes:
   ```bash
   cd ${{ secrets.PROJECT_PATH }}
   git pull origin main
   ```
2. Deploy using pre-built images with the `--pull always` flag:
   ```bash
   docker compose -f docker-compose.existing-infra.yml -f docker-compose.repo.yml up -d --pull always
   ```
3. Never run `docker compose up -d --build` on the target VPS server.

### Phase 4: Server Disk Hygiene & Image Pruning
1. Append an explicit layer cleanup command to the script block:
   ```bash
   docker image prune -f
   ```
2. This removes dangling images from prior deployments and prevents gradual VPS disk exhaustion.

### Phase 5: Automated CLI Audit & Secrets Guidance
1. Execute the automated CLI validator to verify workflow compliance:
   ```bash
   python3 infra/github-actions/skills/github-actions-vps-deployment/scripts/audit_github_actions_workflow.py --path .github/workflows --strict
   ```
2. Present the user with the formatted [assets/github-secrets-checklist.md](assets/github-secrets-checklist.md) so they can configure required secrets in GitHub Repository Settings.

---

## Gotchas & Common Pitfalls

| Faulty / Anti-Pattern | Production Replacement | Why it Matters |
| :--- | :--- | :--- |
| **Server-Side Build in CI** (`docker compose up -d --build`) | Pre-built image pull (`--pull always`) | Multi-stage image compilation exhausts VPS RAM and crashes production processes. |
| **Missing Image Pruning** | `docker image prune -f` after deployment | Dangling image layers consume 100% of server disk over repeated deployments, freezing Docker. |
| **Hardcoded SSH Credentials in Workflow** | GitHub Repository Secrets (`${{ secrets.* }}`) | Commits private keys and IP addresses into version control history. |
| **Deploying as Root User** | Dedicated `deployer` user in `docker` group | Unrestricted root SSH access creates catastrophic security vulnerabilities if keys leak. |
| **Reusing Personal SSH Keys** | Dedicated Ed25519 deployment key pair | Compromise of personal keys breaches all servers; dedicated keys can be revoked individually. |
| **Missing `set -e` in Remote Script** | Explicit error propagation | Without `set -e`, failed git pulls or docker crashes silently proceed without failing the CI run. |
