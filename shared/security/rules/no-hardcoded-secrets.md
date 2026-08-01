---
trigger: always_on
description: "Prevents hardcoding passwords, API tokens, private keys, database credentials, or secret strings in source code or configuration files."
---
# No Hardcoded Secrets Rule

## Description
This rule mandates that all sensitive credentials, secret tokens, private keys, and database passwords MUST be loaded exclusively through environment variables or secret management services. Hardcoding secrets in any code file is strictly prohibited.

## Constraints
- The agent MUST NOT write hardcoded secret strings (API keys, JWT secrets, passwords, SSH keys) in source files, tests, or config files.
- The agent MUST reference environment variables (`process.env.API_KEY`, `process.env.DATABASE_URL`) or use `.env.example` templates for configuration.
- The agent MUST ensure `.env` files are included in `.gitignore`.
- **`.env.example` Strict Parity**: Every variable required in `.env` MUST be present in `.env.example`.
- **No Sensitive Data in `.env.example`**: The `.env.example` file MUST NEVER contain real sensitive data (use placeholder values like `your_api_key_here`).
- **Junior-Friendly Documentation**: The agent MUST add a clear, descriptive comment above every variable in `.env.example`. The comment must explain what the variable does, its expected format, and where to obtain it, so that any junior developer or newcomer can easily set up the project without confusion.

## Examples
- **Correct implementation:**
```typescript
const dbUri = process.env.DATABASE_URL;
if (!dbUri) {
  throw new Error("DATABASE_URL environment variable is required");
}
```

- **Incorrect implementation:**
```typescript
const dbUri = "postgres://admin:secretpassword123@localhost:5432/mydb"; // Security Risk!
```
