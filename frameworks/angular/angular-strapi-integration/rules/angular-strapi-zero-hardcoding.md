---
description: "Strictly enforces zero-hardcoding of text, media, and metadata for Angular applications consuming Strapi CMS APIs, mandating dynamic binding, TransferState, and proactive schema prompts."
trigger: model_decision
---

# Angular & Strapi Zero-Hardcoding Architecture Rules

## Description
This rule strictly enforces a zero-hardcoding invariant across all Angular applications that consume headless Strapi CMS APIs. The Angular frontend acts purely as a dynamic presentation layer: all copy, titles, structural lists, navigation links, and media assets MUST be retrieved dynamically from Strapi. Static placeholders, hardcoded content strings, and fake mock arrays in component files are strictly forbidden. When CMS schema gaps occur, AI agents must proactively output copy-pasteable schema prompts for the Strapi backend.

---

## Constraints

### 1. Strict Zero-Hardcoding Invariant
- Angular HTML templates (`*.component.html`) and TypeScript component classes (`*.component.ts`) MUST NEVER contain hardcoded content-driven text:
  - Prohibited: hardcoded page titles, hero headers, body paragraphs, marketing feature lists, benefit bullets, footer copyright strings, or static placeholder arrays (`const FEATURES = [...]`).
- Content-driven images and media MUST NOT use local relative paths (e.g. `<img src="assets/images/hero.png">`). All content imagery MUST be bound dynamically to Strapi Media Library assets (`[src]="hero.image.url | strapiMedia"`).
- Static assets are strictly limited to fixed architectural iconography (e.g. theme toggle moon/sun SVG, system spinner).

### 2. Strapi v5 Document API Model Alignment
- Strapi v5 replaces the legacy Strapi v4 nested `data.attributes` envelope with the simplified **Document Service API** model.
- Components and services MUST bind directly to document properties (`article.title`, `article.documentId`, `article.publishedAt`) rather than traversing deprecated Strapi v4 wrappers (`article.data.attributes.title`).
- All Strapi collection and single-type response payloads MUST be strictly typed using interfaces that reflect this flat document structure.

### 3. Deep Relation & Component Population
- Headless Strapi endpoints do NOT return relational fields, media attachments, or dynamic zone components by default.
- Every API request originating from Angular services MUST explicitly declare population parameters:
  - Global wildcard population: `?populate=*`
  - Granular field population: `?populate[coverImage][fields][0]=url&populate[coverImage][fields][1]=alternativeText`
- Applications MUST NOT rely on default unpopulated endpoints and then attempt to patch missing fields with client-side fallback text.

### 4. Dynamic Media URL Resolution (`environment.strapiApiUrl`)
- Strapi Media Library endpoints return relative paths (e.g. `/uploads/hero_banner_abc123.webp`) or absolute third-party CDN URLs (e.g. AWS S3 / Cloudflare R2).
- Templates MUST NEVER prepend hardcoded host strings (e.g. `'http://localhost:1337' + image.url`).
- Applications MUST utilize a dedicated standalone pipe (`StrapiMediaPipe`) or centralized media utility that checks whether the URL is already absolute, prepending `environment.strapiApiUrl` only when the path is relative.

### 5. SSR Hydration & `TransferState` Requirement
- In Angular Server-Side Rendered (SSR) applications, data fetching MUST utilize Angular's `TransferState` (`makeStateKey`):
  1. The server pre-renders HTML using data fetched from Strapi and serializes the response into the page payload.
  2. The browser client reads the transferred state upon hydration, avoiding duplicate HTTP network round-trips and preventing UI screen flicker.
- Direct, un-cached `HttpClient` requests inside `ngOnInit()` in SSR mode that bypass `TransferState` are STRICTLY FORBIDDEN.

### 6. Proactive Strapi Schema Generation Protocol
- When building a component that requires fields not yet exposed by the Strapi API response:
  1. The agent MUST NOT invent local mock data or hardcode temporary strings.
  2. The agent MUST alert the developer to the schema deficit.
  3. The agent MUST output a structured prompt block formatted for immediate copy-pasting into the Strapi backend workspace to generate the missing schema.

### 7. Rich Text & Markdown Security (XSS Prevention)
- Content originating from Strapi Rich Text editors (Blocks or Markdown) rendered via `[innerHTML]` MUST be sanitized to prevent Cross-Site Scripting (XSS).
- Use a dedicated sanitizer or trusted markdown parsing pipeline (such as `DomSanitizer.sanitize(SecurityContext.HTML, ...)`). Raw un-sanitized HTML injection is strictly prohibited.

### 8. Strict Type Safety (Zero `any`)
- Writing `any` for Strapi API responses, media payloads, dynamic zone blocks, or pagination metadata is STRICTLY FORBIDDEN.
- Every endpoint MUST have corresponding typed interfaces defining document fields, pagination objects, and media formats.

---

## Examples

### 1. Correct Implementation: Dynamic Binding with StrapiMediaPipe & TransferState

```typescript
import { Component, ChangeDetectionStrategy, inject, input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StrapiMediaPipe } from '../../shared/pipes/strapi-media.pipe';
import { ArticleDocument } from '../../core/models/strapi-models';

/**
 * Editorial showcase card dynamically binding content and media from Strapi v5.
 */
@Component({
  selector: 'app-article-card',
  standalone: true,
  imports: [CommonModule, StrapiMediaPipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (article(); as item) {
      <article class="article-card">
        @if (item.coverImage) {
          <img [src]="item.coverImage.url | strapiMedia"
               [alt]="item.coverImage.alternativeText || item.title"
               class="article-thumbnail"
               loading="lazy" />
        }
        <div class="content-body">
          <span class="category-badge">{{ item.category?.name }}</span>
          <h2>{{ item.title }}</h2>
          <p>{{ item.summary }}</p>
        </div>
      </article>
    }
  `,
  styles: [`
    .article-card { border-radius: 8px; overflow: hidden; }
    .article-thumbnail { width: 100%; height: 220px; object-fit: cover; }
  `]
})
export class ArticleCardComponent {
  /** Strongly typed article input received from CMS service */
  readonly article = input.required<ArticleDocument>();
}
```

### 2. Incorrect Implementation (STRICTLY FORBIDDEN)

```typescript
// ❌ CRITICAL ERRORS:
// 1. Hardcoded static headline, copy, and button label.
// 2. Hardcoded local asset path instead of Strapi Media Library URL.
// 3. Traversal of deprecated Strapi v4 nested attributes envelope.
// 4. Explicit 'any' type annotation.

@Component({
  selector: 'app-bad-card',
  standalone: true,
  template: `
    <article class="card">
      <!-- ❌ Hardcoded local asset -->
      <img src="assets/images/portfolio-sample.png" alt="Sample" />
      
      <!-- ❌ Hardcoded text copy -->
      <h2>Enterprise Cloud Modernization</h2>
      <p>We deliver scalable microservices architectures using Angular and NestJS.</p>
      <button>Learn More</button>
    </article>
  `
})
export class BadCardComponent {
  // ❌ Explicit 'any' and deprecated v4 attribute access
  processData(response: any): void {
    const title = response.data.attributes.title; // ❌ Deprecated v4 structure
  }
}
```
