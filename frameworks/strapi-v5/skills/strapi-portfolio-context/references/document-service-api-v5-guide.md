# Strapi v5 Document Service API Guide

## Overview
In Strapi v5, the legacy **Entity Service API** (`strapi.entityService`) is completely deprecated and replaced by the **Document Service API** (`strapi.documents`). The Document Service API natively models documents, multiple drafts, locales, and published statuses.

---

## 1. Key Differences: v4 Entity Service vs v5 Document Service

| Feature | Strapi v4 Entity Service | Strapi v5 Document Service |
| :--- | :--- | :--- |
| **API Entrypoint** | `strapi.entityService.findMany(...)` | `strapi.documents('api::project.project').findMany(...)` |
| **Primary Identifier** | Sequential integer `id` | Stable alphanumeric `documentId` across draft/published versions |
| **Status Filter** | `publicationState: 'live' / 'preview'` | `status: 'published'` or `status: 'draft'` |
| **Document Versions**| Draft & published are separate database rows | Unified document entity with versioned statuses |

---

## 2. Querying Documents in Lifecycle Hooks & Controllers

### Fetching Published Records
```typescript
const publishedProjects = await strapi.documents('api::project.project').findMany({
  status: 'published',
  fields: ['title', 'slug', 'shortDescription'],
  populate: {
    coverImage: true,
    skills: {
      fields: ['name', 'slug', 'category']
    }
  },
  sort: { startDate: 'desc' }
});
```

### Finding by Unique Slug
```typescript
const project = await strapi.documents('api::project.project').findFirst({
  filters: {
    slug: {
      $eq: projectSlug
    }
  },
  status: 'published',
  populate: '*'
});
```

---

## 3. Flatted REST API Response Format
In Strapi v5, the REST API eliminates the tedious `data.attributes` wrappers of Strapi v4:

```json
// Strapi v5 Response
{
  "data": [
    {
      "id": 1,
      "documentId": "abc123xyz",
      "title": "FinTech Mobile Banking App",
      "slug": "fintech-mobile-banking",
      "shortDescription": "High-performance banking client",
      "createdAt": "2026-09-01T12:00:00.000Z"
    }
  ],
  "meta": {
    "pagination": { "page": 1, "pageSize": 25, "total": 1 }
  }
}
```
This enables frontend consumers (Angular, Next.js) to deserialize models directly without complex unwrap interceptors.
