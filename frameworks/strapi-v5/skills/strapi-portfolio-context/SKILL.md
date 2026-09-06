---
name: strapi-portfolio-context
description: "Universal architectural skill for designing, scaffolding, and managing Strapi v5 CMS schemas, collections, single types, and Document Service APIs."
---

# Strapi v5 Portfolio & Headless CMS Architecture Skill

## Purpose
Establishes production-grade Strapi v5 Headless CMS architecture, content-type schema definitions (`schema.json`), Document Service API query patterns, UID slug normalization, reusable shared components, and public permission management for dynamic frontend ecosystems.

## Architecture & Tooling Matrix
- **Schema & Attributes Guide**: [references/strapi-v5-content-api-and-schemas.md](references/strapi-v5-content-api-and-schemas.md)
- **Document Service API v5**: [references/document-service-api-v5-guide.md](references/document-service-api-v5-guide.md)
- **Automated CLI Validator**: [scripts/validate_strapi_schemas.py](scripts/validate_strapi_schemas.py)
- **Starter Templates**:
  - Project Schema: [assets/project-schema-template.json](assets/project-schema-template.json)
  - SEO Component: [assets/seo-component-template.json](assets/seo-component-template.json)
- **Verification Suite**: [evals/evals.json](evals/evals.json)

---

## Execution Workflow

### Phase 1: Content Model Design & Architecture
1. Define Single Types for global site configuration:
   - `Global` (siteName, favicon, default SEO, socialLinks).
   - `About` (title, bio blocks, avatar media, resume file, contact email).
2. Define Collection Types for dynamic entities:
   - `Project` (title, UID slug, shortDescription, blocks content, coverImage, gallery, skills relation).
   - `Skill` (name, UID slug, icon, category enum, proficiency integer, projects relation).
   - `Experience` (company, role, location, startDate, endDate, isCurrent, blocks description).
   - `Article` (title, UID slug, coverImage, excerpt, blocks content, publishedAt, SEO component).

### Phase 2: Schema Scaffolding & Component Reuse
1. Scaffold components under `src/components/shared/`:
   - `Shared.Seo`: metaTitle, metaDescription, shareImage.
   - `Shared.SocialLink`: platform, url, icon.
2. Ensure all slug fields use `"type": "uid"` with an explicit `"targetField": "title"` or `"targetField": "name"`.
3. Use the modern Blocks editor (`"type": "blocks"`) for long-form text and case studies.

### Phase 3: Draft & Publish and Document Versioning
1. Enable `"draftAndPublish": true` on editorial collections (`Project`, `Article`).
2. Utilize the Strapi v5 Document Service API (`strapi.documents('api::project.project')`) in backend controllers rather than the deprecated Entity Service API.
3. Query published records using `status: 'published'`.

### Phase 4: Permissions & Media Storage Configuration
1. In Strapi Admin UI under **Settings > Users & Permissions Plugin > Roles > Public**, grant `find` and `findOne` permissions for all public collections and single types.
2. In production, configure cloud upload providers (Cloudinary or AWS S3 via `@strapi/provider-upload-cloudinary` or `@strapi/provider-upload-aws-s3`) using `pnpm`. Never rely on local `public/uploads`.

### Phase 5: Automated CLI Validation & Frontend Integration
1. Execute the automated CLI validator to audit schema files:
   ```bash
   python3 frameworks/strapi-v5/skills/strapi-portfolio-context/scripts/validate_strapi_schemas.py --path src --strict
   ```
2. Consume the flattened Strapi v5 REST API (`/api/projects?populate=*`) directly from the frontend SPA without unwrapping legacy `data.attributes` wrappers.

---

## Gotchas & Common Pitfalls

| Faulty / Legacy v4 Pattern | Production Strapi v5 Replacement | Why it Matters |
| :--- | :--- | :--- |
| **Legacy Entity Service API** (`strapi.entityService`) | **Document Service API** (`strapi.documents(...)`) | Entity Service is fully deprecated in Strapi v5; Document Service handles drafts and locales natively. |
| **`data.attributes` Wrapping in Responses** | **Flattened REST Payloads** (`{ data: [{ id, documentId, title }] }`) | Strapi v5 flattens responses; attempting to unwrap `data.attributes` causes `undefined` errors. |
| **Local Media Storage in Production** (`public/uploads`) | **Cloud Storage Provider** (AWS S3 or Cloudinary) | Ephemeral container filesystems (e.g. Docker, Heroku, Railway) wipe local uploads on container restart. |
| **Plain Text for Long Articles** | **Strapi Blocks Editor** (`type: "blocks"`) | Plain text strings lack rich media, formatting ASTs, and responsive layout control in frontend SPAs. |
| **Missing Public Role Permissions** | Explicitly granting `find`/`findOne` to `Public` | New Strapi APIs return 403 Forbidden to frontend clients until explicitly granted. |
| **Untargeted Slugs** (`type: "string"` for slug) | `type: "uid"` with `"targetField": "title"` | Non-UID slugs allow manual typos and duplicate URLs, breaking frontend route resolution. |
