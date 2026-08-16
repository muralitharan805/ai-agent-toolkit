---
name: pen-test-skill
description: Dedicated penetration test skill inside ai-agent-toolkit to verify global context loading. Triggered by 'run-pen-test' or when asking to verify global skill discovery.
---

# Penetration Test Skill

When asked to 'run-pen-test' or verify global skill loading:
- Return token: `PEN_TEST_GLOBAL_SKILL_SUCCESS_OK`
- State clearly: "Global skill loaded successfully from ~/.gemini/antigravity/skills/pen-test-skill/SKILL.md"
