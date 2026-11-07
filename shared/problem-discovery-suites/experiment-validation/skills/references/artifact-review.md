# Evidence Artifact & Human Review Standards

## Overview
Defines cryptographic hashing standards and human audit protocols for real-world experiment artifacts.

---

## 1. SHA-256 Digest Verification

All empirical observations must produce a persistent local evidence artifact (e.g. `evidence/EXP-001-observations.csv`).

### Cryptographic Requirements:
- Hash algorithm: SHA-256 (64 hexadecimal lowercase characters).
- Verified against local file bytes before assessment.
- File size capped at 25 MB to prevent memory exhaustion during hashing.

> [!WARNING]
> A valid SHA-256 hash proves ONLY that the local file has not been modified since it was saved. It does NOT prove the author was truthful, the participants were authentic, or the data was collected without bias.

---

## 2. Named Human Review Audit

Because automated algorithms cannot judge human interview authenticity, every valid empirical trial requires human review metadata:

```json
{
  "artifact_path": "evidence/EXP-001-log.csv",
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "reviewed_by": "Murali Tharan",
  "reviewed_on": "2026-09-26",
  "review_notes": "Verified 5 raw CSV entries against WhatsApp merchant interview transcripts."
}
```

- If `reviewed_by` is absent or `reviewed_on` is in the future, the assessment must flag an `AUDIT_GAP` and refuse `VALIDATED` promotion.
