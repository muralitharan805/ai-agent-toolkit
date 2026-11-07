# Security Policy (`SECURITY.md`)

## 1. Supported Versions

Security fixes and dependency updates are applied to the active `main` branch.

| Branch | Supported |
| :--- | :--- |
| `main` | ✅ Yes |
| Historical release tags | ⚠️ Patch as needed |

---

## 2. Reporting a Vulnerability

If you discover a potential security vulnerability, credential exposure, or unsafe file-write boundary in **`ai-agent-toolkit`**, please **DO NOT open a public GitHub issue**.

Instead, report it privately through one of the following channels:

1. **GitHub Private Security Advisory**: Go to the **Security** tab of `muralitharan805/ai-agent-toolkit` and click **"Report a vulnerability"**.
2. **Direct Email**: Send a detailed report to **`muralitharan805@gmail.com`** with the subject line `[SECURITY] AI Agent Toolkit Vulnerability Report`.

Please include:
- A clear description of the vulnerability.
- Steps to reproduce the issue.
- Potential impact on user workspaces or file systems.
- Any proposed remediation or patch.

We aim to acknowledge reports as soon as practical and prioritize confirmed vulnerabilities according to severity. Response and remediation timelines depend on maintainer availability and the nature of the issue.

---

## 3. Security Controls and Limitations

The toolkit follows defensive security practices, with the following controls and limitations:

1. **Secret handling**: Hardcoded live credentials and tokens are prohibited. GitHub Actions runs Gitleaks on pull requests and pushes to `main` to detect potential committed secrets. Secret scanning reduces risk but cannot guarantee that a repository contains no secrets.
2. **Git history**: A passing CI scan is not proof that every historical commit is safe. Before making the repository public, separately review and scan the complete Git history. Revoke or rotate exposed credentials; removing a file from the latest branch does not erase it from history.
3. **Filesystem safety**: The `bin/context.sh` and `bin/toolkit_manifest.py` sync engine tracks installed content using SHA-256 hashes. By default, it protects unmanaged and locally modified content. The explicit `--force` option allows overwrites; review its effects before use.
4. **Private domain content**: `domains/` is ignored by default to reduce accidental additions of private modules. `.gitignore` does not protect files already tracked in Git or committed in history. Review files before publishing.
5. **Execution permissions**: Run scripts with least-privilege user permissions where possible and review any scripts before execution.

### CI verification

The `.github/workflows/ci.yml` workflow runs Bash syntax checks, Python compilation, unit/integration tests, representative Agent Skill validation, and Gitleaks secret scanning. The full ecosystem health audit is a separate maintainer-run check, not an enforced CI gate.

If Gitleaks detects a potential secret, investigate without copying its value into public issues or logs. Revoke or rotate confirmed exposed credentials before proceeding.
