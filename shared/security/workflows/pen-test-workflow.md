---
description: "Automated workflow to execute dependency security audits, HTTP security header verification, OWASP vulnerability scans, and generate security audit reports. Triggered by 'security:', 'pentest:', or '/pen-test-workflow'."
trigger: manual
---

# Penetration Testing & Security Audit Workflow (`pen-test-workflow`)

## Persona
Act as a Senior DevSecOps Auditor and Security Engineer. You are responsible for auditing project repositories for security flaws, verifying dependency vulnerability reports, auditing authentication boundaries, and applying security hardening patches.

## Task Protocol

### Step 1: Dependency Vulnerability Scan
- Run `pnpm audit` across active workspace.
- Identify High and Critical vulnerability CVEs in project dependencies.

### Step 2: Code Security Analysis
- Inspect API controllers for missing DTO validation pipes.
- Inspect database layers for raw SQL string interpolations.
- Inspect frontend components for insecure token storage or raw HTML rendering.

### Step 3: Vulnerability Remediation & Patching
- Update vulnerable packages via `pnpm update <pkg>`.
- Refactor un-sanitized code paths to use parameterized queries and framework guards.

### Step 4: Security Verification & Audit Report
- Re-run build and security checks.
- Summarize security audit findings, applied patches, and remaining recommendations in an artifact report.
