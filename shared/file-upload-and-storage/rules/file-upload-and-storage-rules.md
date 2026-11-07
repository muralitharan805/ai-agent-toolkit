---
trigger: model_decision
description: "Enforces pre-signed URL upload architecture (file bytes never traverse app server), magic byte file type validation, virus scanning pipeline before file access, time-limited signed CDN URLs for private files, per-user storage quota, and orphaned file cleanup cron jobs."
framework_version: "Language-Agnostic"
last_verified_date: "2026-09-10"
---

# File Upload & Storage Architecture Standards

## Description
Enforces secure, scalable, and memory-safe file upload and storage architecture across all backend services. Mandates the Pre-Signed URL pattern so file bytes never traverse application server memory (preventing memory exhaustion and throughput ceiling under concurrent load), magic byte validation on every upload (preventing extension spoofing attacks), automated virus scanning pipeline via ClamAV or AWS Macie before granting any file access, time-limited signed CDN URLs for all private file access (preventing auth bypass via guessable S3 URLs), per-user storage quota enforcement at URL generation time, and orphaned file cleanup cron jobs for pending uploads exceeding 24 hours.

## Constraints

### 1. Pre-Signed URL Mandatory — No File Bytes Through Application Server
- Application servers MUST NOT receive, buffer, or proxy raw file content bytes.
- All file uploads MUST follow the 5-step Pre-Signed URL pattern:
  1. Client sends file metadata (`filename`, `mimeType`, `fileSize`) to backend.
  2. Backend validates metadata and generates a pre-signed `PUT` URL from S3/GCS/Azure Blob.
  3. Client uploads file content directly to the object storage provider (bypassing backend entirely).
  4. Client confirms the upload via a separate `POST /files/confirm { fileKey }` request.
  5. Backend records metadata in `file_uploads` table with `status: 'pending'`.
- Files > 5MB MUST use the S3 multipart upload API to enable resumable uploads.

### 2. Magic Byte File Type Validation
- File type validation MUST read and compare the first N bytes (magic bytes) of the file content — never rely solely on the file extension or `Content-Type` header.
- If the magic bytes do not match the declared MIME type, the upload MUST be rejected with HTTP 422 Unprocessable Entity.
- EXE files (magic bytes `4D 5A`, MZ header) MUST always be rejected regardless of extension or MIME type.
- Tools: `file-type` (Node.js), `python-magic` (Python), Apache Tika (Java).

### 3. Virus Scanning Before File Access
- Every uploaded file MUST be automatically scanned for malware after S3 upload confirmation.
- File access (serving CDN URLs, download links) MUST be blocked until `virus_scan_status = 'clean'`.
- Infected files MUST be quarantined: `UPDATE file_uploads SET status = 'quarantined'`, deleted from S3, and the security team must be alerted.
- Pending scan state: clients receive "file is processing" response — never an expired S3 URL.

### 4. Signed CDN URLs for Private Files
- Private files (user documents, invoices, medical records, contracts) MUST NEVER be served via raw S3 URLs.
- Every private file access request MUST generate a fresh time-limited signed CDN URL:
  - View access: expires in 1 hour.
  - Download access: expires in 24 hours.
- Signed URLs MUST be invalidated immediately when user permissions are revoked.
- Public files (product images, logos) MAY use permanent public CDN URLs with `Cache-Control: public, max-age=31536000, immutable`.

### 5. Storage Quota & Cleanup
- Per-user storage quota MUST be enforced at the upload-URL generation step (before issuing pre-signed URL).
- An orphaned file cleanup cron job MUST run daily: delete from S3 all `file_uploads` records with `status = 'pending'` for more than 24 hours.

## Examples

### 1. Pre-Signed URL Generation Endpoint
```typescript
// ✅ CORRECT: Validate metadata, check quota, generate pre-signed URL
@Post('upload-url')
async generateUploadUrl(
  @Body() dto: GenerateUploadUrlDto,
  @CurrentUser() user: AuthenticatedUser
): Promise<UploadUrlResponse> {
  await this.storageService.validateQuota(user.id, dto.fileSize);
  await this.storageService.validateMimeType(dto.mimeType);

  const fileKey = `uploads/${user.id}/${crypto.randomUUID()}/${dto.filename}`;
  const uploadUrl = await this.s3Client.getSignedUrl('putObject', {
    Bucket: config.S3_BUCKET,
    Key: fileKey,
    ContentType: dto.mimeType,
    Expires: 900, // 15 minutes
  });

  await this.fileRepository.create({
    fileKey, bucket: config.S3_BUCKET, originalName: dto.filename,
    mimeType: dto.mimeType, fileSize: dto.fileSize,
    status: FileStatus.PENDING, uploadedBy: user.id,
  });

  return { uploadUrl, fileKey };
}
```

### 2. Forbidden — File Bytes Through Backend
```typescript
// ❌ FORBIDDEN: File bytes buffered in server memory
@Post('upload')
async upload(@UploadedFile() file: Express.Multer.File): Promise<void> {
  await this.s3Client.upload({ Key: file.originalname, Body: file.buffer }).promise();
  // Memory spike under concurrent uploads → OOM crash
}
```
