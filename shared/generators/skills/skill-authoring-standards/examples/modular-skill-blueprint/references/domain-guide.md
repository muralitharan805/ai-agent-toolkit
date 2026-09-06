# Deep Domain Guide

> Granular technical reference loaded on demand during complex sub-tasks.

## Core Invariants
1. **Zero Data Loss**: Always backup state before running destructive file or schema mutations.
2. **Deterministic Output**: Always sort keys in generated JSON or YAML artifacts.
3. **Guard Clauses**: Flatten execution flow using early returns rather than deep nesting.

## Advanced Patterns
When handling large data payloads, stream records in batches of 100 items rather than buffering the entire array into memory.
