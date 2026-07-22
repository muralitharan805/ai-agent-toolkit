---
name: git-conventional-commits
description: "Best practices and standard formatting for Git conventional commit messages, including scope definitions, breaking change formatting, and automated commit validation."
---
# Goal
Ensure all Git commit messages across projects adhere strictly to Conventional Commits specification for automatic changelog generation and clear version history.

# Instructions
1. Analyze git diff and identify the primary intent of the changes (e.g., `feat`, `fix`, `docs`, `refactor`, `test`, `chore`).
2. Format the commit header as `<type>(<scope>): <short description in imperative mood>`.
3. Keep the commit title under 72 characters and do not capitalize the first letter of the description.
4. If there is a breaking change, append `!` after the type/scope or add `BREAKING CHANGE: <explanation>` in the footer.
5. Provide a detailed bulleted list in the body for non-trivial commits explaining *what* changed and *why*.

# Examples
Input: Added user profile avatar upload API endpoint in NestJS user module.
Output:
`feat(user): add profile avatar upload endpoint`

Input: Fixed database reconnection memory leak in Redis client.
Output:
`fix(redis): resolve memory leak during client reconnection`

# Constraints
- Do NOT use generic commit messages like "updated code", "fixes", or "changes".
- Do NOT include sensitive secrets or token values in commit messages.
