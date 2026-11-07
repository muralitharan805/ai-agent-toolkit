# Permission Request Template

Before executing any file modifications, the agent must present the following structured plan to the user:

```markdown
### 🛡️ Execution Plan & Permission Request

**1. Objective:**
[Brief summary of what the change accomplishes.]

**2. Target Files & Action:**
- `[MODIFY]` `path/to/target-file.ts` (Lines X–Y)
- `[NEW]` `path/to/new-file.ts`

**3. Blast Radius Assessment:**
- Scope: [Local component / Shared utility / Module boundary]
- Risk Level: [Low / Medium / High]
- Reversibility: [Type 2 (Two-way door) - Easy rollback via git]

**4. Proposed Diff Preview:**
```diff
- [Old code line]
+ [New code line]
```

**Permission Prompt:**
> *"Shall I proceed with applying these changes to `[target-file]`?"*
```
