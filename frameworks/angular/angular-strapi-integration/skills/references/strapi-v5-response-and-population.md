# Strapi v5 Document API & Population Architecture

This reference documents the data contract, query population mechanics, and response structures for applications consuming Strapi v5 headless CMS APIs from Angular.

---

## 1. Strapi v5 Document Service vs Legacy Strapi v4

Strapi v5 introduced the **Document Service API**, fundamentally simplifying REST responses and draft/publish workflows.

### Legacy Strapi v4 (Deprecated):
```json
{
  "data": {
    "id": 1,
    "attributes": {
      "title": "Cloud Modernization",
      "summary": "Enterprise solutions...",
      "createdAt": "2026-01-01T00:00:00.000Z"
    }
  }
}
```

### Modern Strapi v5 (Current Standard):
In Strapi v5, the nested `attributes` envelope is eliminated:
```json
{
  "data": {
    "id": 1,
    "documentId": "c1f7a2b9e4d6f8a0",
    "title": "Cloud Modernization",
    "summary": "Enterprise solutions...",
    "createdAt": "2026-01-01T00:00:00.000Z",
    "publishedAt": "2026-01-02T12:00:00.000Z"
  },
  "meta": {
    "pagination": {
      "page": 1,
      "pageSize": 25,
      "pageCount": 1,
      "total": 1
    }
  }
}
```

### The `documentId` Identifier
Strapi v5 uses `documentId` (a unique string) to track documents across their full lifecycle (drafts, published versions, and multiple locales). Angular routing and API fetches should query by `documentId` or `slug` rather than transient auto-incrementing numeric IDs.

---

## 2. Deep Population Query Syntax

By default, Strapi REST queries return only scalar fields. Relational fields, media attachments, and components are omitted unless explicitly populated.

### Global Wildcard Population
For simple content types:
```text
GET /api/articles?populate=*
```

### Granular Relational Population
To optimize payload size and avoid over-fetching heavy relational trees:
```text
GET /api/articles?populate[coverImage][fields][0]=url&populate[coverImage][fields][1]=alternativeText&populate[category][fields][0]=name
```

### Dynamic Zone & Component Population
For pages built with dynamic zones (e.g. `page.sections`):
```text
GET /api/pages?filters[slug][$eq]=about&populate[sections][populate]=*
```

---

## 3. Filtering & Pagination Query Best Practices

### Filtering by Slug
```text
GET /api/articles?filters[slug][$eq]=angular-signals-guide
```

### Pagination by Page
```text
GET /api/articles?pagination[page]=1&pagination[pageSize]=12&sort=publishedAt:desc
```
