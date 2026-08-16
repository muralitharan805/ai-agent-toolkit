---
description: "Penetration test workflow to verify global workflow execution. Triggered by '/pen-test-workflow' or 'run-pen-test-workflow'."
trigger: manual
---

# Penetration Test Workflow

Follow these steps when invoked via `/pen-test-workflow`:

1. **Acknowledge Workflow**: State that the global workflow was invoked via `/pen-test-workflow`.
2. **Output Token**: Return exact verification token `PEN_TEST_WORKFLOW_SUCCESS_7789`.
3. **Confirm Location**: State clearly that it was loaded from `~/.gemini/config/global_workflows/pen-test-workflow.md`.
