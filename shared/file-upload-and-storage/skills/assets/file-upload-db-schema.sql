-- File Uploads Table: Complete lifecycle tracking schema
-- Tracks every file upload from pending → confirmed → clean/quarantined

CREATE TYPE file_upload_status AS ENUM (
  'pending',       -- Pre-signed URL issued, client upload not yet confirmed
  'confirmed',     -- Client confirmed upload, virus scan queued
  'scanning',      -- Virus scan in progress
  'clean',         -- Scan passed — file is accessible
  'quarantined',   -- Malware detected — file deleted from S3
  'orphaned'       -- pending > 24h — marked for cleanup
);

CREATE TABLE file_uploads (
  -- Identity
  id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Storage location
  file_key              VARCHAR(1024) NOT NULL UNIQUE,  -- S3/GCS object key
  bucket_name           VARCHAR(255) NOT NULL,

  -- File metadata (from client at upload-url generation time)
  original_filename     VARCHAR(512) NOT NULL,
  mime_type             VARCHAR(127) NOT NULL,
  file_size_bytes       BIGINT NOT NULL CHECK (file_size_bytes > 0),
  file_extension        VARCHAR(32),

  -- Lifecycle status
  status                file_upload_status NOT NULL DEFAULT 'pending',

  -- Virus scan tracking
  virus_scan_status     VARCHAR(32) DEFAULT 'pending',  -- 'pending' | 'clean' | 'infected'
  virus_scan_at         TIMESTAMP,
  virus_scan_provider   VARCHAR(64),  -- 'clamav' | 'aws-macie' | 'cloudmersive'

  -- Ownership & access control
  uploaded_by_user_id   UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  entity_type           VARCHAR(64),   -- 'invoice', 'profile-photo', 'contract'
  entity_id             UUID,          -- FK to the owning entity

  -- Timestamps
  upload_url_issued_at  TIMESTAMP NOT NULL DEFAULT NOW(),
  confirmed_at          TIMESTAMP,
  accessible_at         TIMESTAMP,     -- Set when status = 'clean'
  quarantined_at        TIMESTAMP,
  created_at            TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at            TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Indexes for common access patterns
CREATE INDEX idx_file_uploads_user       ON file_uploads(uploaded_by_user_id);
CREATE INDEX idx_file_uploads_entity     ON file_uploads(entity_type, entity_id);
CREATE INDEX idx_file_uploads_status     ON file_uploads(status);
CREATE INDEX idx_file_uploads_pending    ON file_uploads(upload_url_issued_at) WHERE status = 'pending';

-- Trigger: auto-update updated_at on every row change
CREATE OR REPLACE FUNCTION update_file_uploads_timestamp()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER file_uploads_updated_at
BEFORE UPDATE ON file_uploads
FOR EACH ROW EXECUTE FUNCTION update_file_uploads_timestamp();

COMMENT ON TABLE file_uploads IS
  'Tracks every file upload lifecycle: pending URL → client upload → virus scan → clean/quarantined.
   Files are NOT accessible until virus_scan_status = ''clean'' and status = ''clean''.
   Orphan cleanup cron: DELETE FROM file_uploads WHERE status = ''pending''
   AND upload_url_issued_at < NOW() - INTERVAL ''24 hours''.';
