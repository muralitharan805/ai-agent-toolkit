# File Upload & Storage — Deep Architecture Guide

## 1. Magic Byte Reference Catalog

File type validation MUST check the actual bytes of the file content, not the extension or `Content-Type` header:

```
Format          Extension   Magic Bytes (Hex)          ASCII Hint
─────────────────────────────────────────────────────────────────────
JPEG            .jpg/.jpeg  FF D8 FF                   ÿØÿ
PNG             .png        89 50 4E 47 0D 0A 1A 0A    .PNG....
PDF             .pdf        25 50 44 46 2D              %PDF-
GIF             .gif        47 49 46 38                 GIF8
WebP            .webp       52 49 46 46 ... 57 45 42 50 RIFF...WEBP
DOCX/XLSX/PPTX  .docx       50 4B 03 04                PK.. (ZIP-based)
ZIP             .zip        50 4B 03 04                PK..

DANGEROUS — ALWAYS REJECT:
EXE/DLL         .exe/.dll   4D 5A                      MZ
ELF (Linux bin) —           7F 45 4C 46                .ELF
Script (shebang) .sh        23 21                      #!
Mach-O (macOS)  —           FE ED FA CE                ....
```

**Node.js implementation:**
```typescript
import { fileTypeFromBuffer } from 'file-type';

async function validateMagicBytes(
  buffer: Buffer,
  declaredMimeType: string
): Promise<void> {
  const detectedType = await fileTypeFromBuffer(buffer.slice(0, 4100));

  // Always reject EXE/ELF regardless of declared type
  const dangerousMimeTypes = ['application/x-msdownload', 'application/x-executable'];
  if (detectedType && dangerousMimeTypes.includes(detectedType.mime)) {
    throw new SecurityException('Executable file types are not permitted');
  }

  if (!detectedType || detectedType.mime !== declaredMimeType) {
    throw new ValidationException(
      `File content type (${detectedType?.mime}) does not match declared type (${declaredMimeType})`
    );
  }
}
```

---

## 2. Virus Scan Pipeline Architecture

### Option A: AWS Macie (AWS-native, serverless)
```
S3 Upload ──► S3 Event Notification ──► Lambda
                                          │
                                    Start Macie scan job
                                          │
                               Macie Findings ──► EventBridge
                                          │
                           Lambda: UPDATE file_uploads SET virus_scan_status
```

### Option B: ClamAV (self-hosted, open source)
```
S3 Upload ──► S3 Event ──► SQS Queue ──► Scanner Worker (ECS/EKS)
                                              │
                              clamdscan --stdin {file}
                                              │
                         Clean → UPDATE status='clean'
                         Infected → DELETE from S3 + alert security team
```

**ClamAV Docker integration:**
```dockerfile
FROM clamav/clamav:1.3
COPY scanner-worker.sh /app/
CMD ["/app/scanner-worker.sh"]
```

---

## 3. Per-User Storage Quota Architecture

```sql
-- User storage quota table
CREATE TABLE user_storage_quotas (
  user_id            UUID PRIMARY KEY REFERENCES users(id),
  quota_bytes        BIGINT NOT NULL DEFAULT 5368709120,  -- 5 GB default
  used_bytes         BIGINT NOT NULL DEFAULT 0,
  updated_at         TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Quota enforcement function (called at upload-url generation)
CREATE OR REPLACE FUNCTION check_and_reserve_storage_quota(
  p_user_id UUID,
  p_file_size_bytes BIGINT
) RETURNS VOID AS $$
DECLARE
  v_quota RECORD;
BEGIN
  SELECT quota_bytes, used_bytes INTO v_quota
  FROM user_storage_quotas
  WHERE user_id = p_user_id
  FOR UPDATE;  -- Row-level lock prevents race condition

  IF (v_quota.used_bytes + p_file_size_bytes) > v_quota.quota_bytes THEN
    RAISE EXCEPTION 'Storage quota exceeded. Used: % bytes, Quota: % bytes',
      v_quota.used_bytes, v_quota.quota_bytes;
  END IF;

  UPDATE user_storage_quotas
  SET used_bytes = used_bytes + p_file_size_bytes
  WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;
```

---

## 4. S3 Multipart Upload (Files > 5MB)

For large files, the client MUST use multipart upload to enable resumable uploads:

```typescript
// Step 1: Initiate multipart upload
const { UploadId } = await s3.createMultipartUpload({
  Bucket: config.S3_BUCKET,
  Key: fileKey,
  ContentType: mimeType,
}).promise();

// Step 2: Generate pre-signed URLs for each part (5MB minimum per part)
const partUrls = await Promise.all(
  Array.from({ length: partCount }, async (_, index) =>
    s3.getSignedUrlPromise('uploadPart', {
      Bucket: config.S3_BUCKET,
      Key: fileKey,
      UploadId,
      PartNumber: index + 1,
      Expires: 3600, // 1 hour per part
    })
  )
);

// Step 3: Client uploads each part directly to S3
// Step 4: Client calls CompleteMultipartUpload with ETags from each part response
```

---

## 5. CDN Signed URL Strategies by Provider

| Provider | View URL (1h) | Download URL (24h) | Revocation |
|---|---|---|---|
| **AWS CloudFront** | Signed URL via RSA key pair | Signed URL, 24h TTL | Signed URL invalidation |
| **GCS** | `storage.generateSignedUrl(V4)` | V4 signed URL | IAM permission removal |
| **Cloudflare R2** | Pre-signed URL (S3-compatible) | Long-TTL pre-signed URL | Cannot revoke — use short TTL |
| **Azure Blob** | SAS token, 1h | SAS token, 24h | Revoke via stored access policy |
