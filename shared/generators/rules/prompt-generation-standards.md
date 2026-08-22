---
description: "Enforces production-grade prompt generation standards, pattern selection rules, XML structural tagging, and zero-conversational-noise output rules."
trigger: always_on
---

# Enterprise Prompt Generation Standards

## Description
Enforces mandatory quality standards for prompt engineering, pattern selection, XML tag structuring, missing information handling, and zero-noise output formatting across all AI prompt generation workflows.

## Constraints

### 1. Mandatory Goal Preservation & Pattern Selection
- Prompt generators MUST preserve the user's core intent while eliminating ambiguity.
- Pattern selection MUST be selective based on task type (e.g. Simple, Vague, Analytical, Research, Complex, Multi-stage, Creative, Technical). Forcing all patterns into every prompt is strictly forbidden.

### 2. Pragmatic XML Structural Tagging
- Generated prompts MUST utilize XML structural tags (`<role>`, `<context>`, `<task>`, `<requirements>`, `<constraints>`, `<references>`, `<process>`, `<validation>`, `<output_format>`) when structural separation improves LLM execution clarity.
- Do NOT create unnecessary custom tags or blindly apply unused tags.

### 3. Missing Information Protocol
- When critical information is genuinely missing, use Flipped Interaction or Ask-for-Input patterns to ask only the minimum necessary questions.
- If safe, reasonable assumptions can be made, state them explicitly in the generated prompt instead of harassing the user for trivial details.

### 4. Zero-Noise Output Requirement
- Output MUST contain ONLY the final optimized, standalone prompt.
- Pre-thinking, pattern explanations, conversational introductions ("Here is your prompt:"), and post-generation commentary are STRICTLY FORBIDDEN.
