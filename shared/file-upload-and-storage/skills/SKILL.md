---
name: file-upload-and-storage
description: "Enforces pre-signed URL upload architecture (client uploads directly to S3/GCS), magic byte file type validation, virus scanning pipeline (ClamAV/Macie), time-limited signed CDN URLs for private files, and per-user storage quota enforcement. Triggered by 'file-upload:', 'storage:', 'presigned-url:', or '/file-upload-and-storage'."
metadata:
  framework_version: "Language-Agnostic"
  last_verified_date: "2026-09-10"
---

# File Upload & Storage Architecture Skill

## Overview

This skill establishes production engineering standards for the **Pre-Signed URL Upload Pattern** (file bytes never traverse the application server), **Magic Byte File Type Validation** (extension spoofing prevention), **Automated Virus Scanning Pipeline** (ClamAV / AWS Macie on every upload), **Time-Limited Signed CDN URLs for Private Files** (auth bypass prevention), and **Per-User Storage Quota Enforcement**. It eliminates memory exhaustion from buffering large files, prevents malware storage, and ensures private files are never exposed via guessable S3 URLs.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                   Pre-Signed URL Upload Architecture                     │
│                                                                          │
│  Step 1: Client → POST /api/v1/files/upload-url                          │
│               Backend validates metadata + generates pre-signed PUT URL  │
│  Step 2: Client → PUT {presignedUrl} directly to S3 (bypasses backend)  │
│  Step 3: Client → POST /api/v1/files/confirm { fileKey }                │
│               Backend records metadata, status: 'pending'               │
│  Step 4: S3 Event → Lambda/Webhook → Virus scan triggered               │
│  Step 5: Scan result → UPDATE status: 'clean' | 'quarantined'           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 4-Phase Execution Guide

### Phase 1: Pre-Signed URL Generation (Request Validation)
1. **Validate metadata** (server-side, before issuing URL):
   - `mimeType` must be in allowed MIME type allowlist.
   - `fileSize` must be within limit for the entity type.
   - User has not exceeded their storage quota.
2. **Magic byte pre-check** (for uploads going through the backend transiently):
   - Validate file magic bytes — not extension. Common bytes documented in references.
3. **Generate pre-signed PUT URL** with S3/GCS SDK:
   - TTL: 15 minutes (URL expires — prevents abuse).
   - Set `ContentType` constraint in URL (S3 rejects mismatched MIME type uploads).
4. **Create DB record** with `status: 'pending'` and return `{ uploadUrl, fileKey }`.

### Phase 2: Client Direct Upload
- Client performs `PUT {uploadUrl}` directly with binary content.
- Backend is completely bypassed — zero memory pressure on pods.
- Files > 5MB: client must use S3 multipart upload API (resumable).

### Phase 3: Upload Confirmation & Virus Scan Trigger
1. Client calls `POST /api/v1/files/confirm { fileKey }`.
2. Backend updates `file_uploads.status = 'confirmed'` and `confirmed_at`.
3. S3 event notification triggers virus scan Lambda/worker automatically.

### Phase 4: Virus Scan Result Processing
1. **Clean**: Update `status = 'clean'`, generate CDN URL, make file accessible.
2. **Infected**: Update `status = 'quarantined'`, delete from S3, alert security team.
3. **Pending**: Users receive "file is processing" state until scan completes.
4. **Users MUST NOT access files until `virus_scan_status = 'clean'`**.

---

## Private vs Public File Serving
```
Private (user docs, invoices, medical):
  ❌ NEVER: raw S3 URL (auth bypass — anyone with URL accesses file)
  ✅ Always: Time-limited signed CDN URL per request
     View: expires in 1 hour | Download: expires in 24 hours
     Revoke: invalidate signed URL immediately on permission change

Public (product images, logos, avatars):
  ✅ S3 + CloudFront/Cloudflare CDN (permanent public URL)
  ✅ Cache-Control: public, max-age=31536000, immutable
     (content-hash suffix in filename ensures cache busting)
```

---

## Authoritative References & Assets

- **Deep Architecture Guide**: Read [references/file-upload-storage-and-cdn-patterns.md](references/file-upload-storage-and-cdn-patterns.md) for S3 multipart upload, magic byte catalog, ClamAV Lambda integration, and quota architecture.
- **Production Asset**: Inspect [assets/file-upload-db-schema.sql](assets/file-upload-db-schema.sql) for the complete `file_uploads` table schema with status lifecycle columns.
- **CLI Auditor Tool**: Execute [scripts/audit_file_upload_security.py](scripts/audit_file_upload_security.py) to detect raw S3 URLs, missing virus scan checks, and extension-only validation.
- **Evaluation Suite**: Review [evals/evals.json](evals/evals.json) for quality verification test cases.

---

## Gotchas & Pitfalls

| Category | ❌ Anti-Pattern (Legacy / Brittle) | ✅ Production-Grade (Modern Standard) | Risk |
| :--- | :--- | :--- | :--- |
| **Upload Path** | File bytes through backend server | Pre-signed URL — client uploads to S3 directly | Memory exhaustion under concurrent load |
| **Type Validation** | Extension check only | Magic byte validation (first N bytes) | Attacker renames `malware.exe` → `photo.jpg` |
| **Private Files** | Raw S3 URL in DB | Time-limited signed CDN URL generated per request | Auth bypass — anyone with URL accesses file |
| **Virus Scanning** | No scan | ClamAV / AWS Macie on every S3 upload event | Malware stored and served to all users |
| **Access Control** | Serve file before scan | Block access until `virus_scan_status = 'clean'` | Malware served to users before detection |
| **Orphaned Files** | No cleanup | Cron job: `status = 'pending'` > 24h → delete from S3 | Unbounded S3 storage growth |
| **Quota** | No per-user limit | Enforce quota at upload-url generation step | Single user fills entire S3 bucket |
