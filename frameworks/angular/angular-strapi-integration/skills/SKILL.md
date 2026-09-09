---
name: angular-strapi-integration
description: "Enforces zero-hardcoding of content, Strapi v5 Document API consumption, TransferState SSR caching, dynamic media resolution, and proactive schema prompts."
---

# Angular & Strapi CMS Integration Skill

## 1. Overview & 5-Pillar Architecture

This skill provides an enterprise standard for Angular frontends consuming headless Strapi v5 CMS backends. It strictly enforces a zero-hardcoding policy where all copy, metadata, and media assets are retrieved dynamically via Strapi APIs, cached for SSR hydration using `TransferState`, rendered securely, and resolved against environment base URLs. When required CMS fields are missing, agents proactively output copy-pasteable schema prompts for the backend.

```text
frameworks/angular/skills/angular-strapi-integration/
├── SKILL.md                          # Core procedural instruction (< 500 lines) + Gotchas
├── references/                       # In-depth architectural runbooks
│   ├── strapi-v5-response-and-population.md # Strapi v5 Document API & query population
│   └── ssr-transfer-state-and-media.md # TransferState hydration & responsive media formats
├── scripts/                          # Automated compliance audit CLI
│   └── audit_strapi_integration.py   # Standalone PEP 723 audit tool
├── assets/                           # Production-ready drop-in templates
│   ├── strapi-models.ts              # Typed interfaces for Strapi v5 documents and media
│   ├── strapi.service.ts             # Generic HTTP client with TransferState caching
│   ├── strapi-media.pipe.ts          # Standalone pipe resolving relative media URLs
│   └── proactive-schema-prompt.md    # Copy-pasteable schema prompt template
└── evals/                            # Quality verification test suite
    ├── evals.json                    # Automated assertions and evaluation cases
    └── grading.json                  # Net skill lift and benchmark metrics
```

---

## 2. 4-Phase Integration Protocol

### Phase 1: Environment & API Client Configuration
1. Configure the Strapi API URL in `src/environments/environment.ts`:
   ```typescript
   export const environment = {
     production: false,
     strapiApiUrl: 'http://localhost:1337'
   };
   ```
2. Provide `STRAPI_BASE_URL` in `src/app/app.config.ts`:
   ```typescript
   import { ApplicationConfig } from '@angular/core';
   import { provideHttpClient, withFetch } from '@angular/common/http';
   import { STRAPI_BASE_URL } from './core/services/strapi.service';
   import { environment } from '../environments/environment';

   export const appConfig: ApplicationConfig = {
     providers: [
       provideHttpClient(withFetch()),
       { provide: STRAPI_BASE_URL, useValue: environment.strapiApiUrl }
     ]
   };
   ```

### Phase 2: Define Strongly Typed Models & Population Queries
1. Create models inheriting from `StrapiBaseDocument` using flat Strapi v5 schemas:
   ```typescript
   import { StrapiBaseDocument, StrapiMedia } from './strapi-models';

   export interface ArticleDocument extends StrapiBaseDocument {
     readonly title: string;
     readonly slug: string;
     readonly summary: string;
     readonly content: string;
     readonly coverImage?: StrapiMedia | null;
   }
   ```
2. In query calls, explicitly request relational population:
   ```typescript
   this.strapi.get<ArticleDocument[]>('/api/articles', {
     populate: ['coverImage', 'category'],
     sort: 'publishedAt:desc'
   });
   ```

### Phase 3: SSR Hydration Caching & Dynamic Media Resolution
1. In SSR services, consume endpoints with `getWithTransferState()` to eliminate duplicate client hydration queries:
   ```typescript
   getArticleBySlug(slug: string): Observable<StrapiResponse<ArticleDocument>> {
     return this.strapi.getWithTransferState<ArticleDocument>(
       `article_${slug}`,
       `/api/articles`,
       { filters: { slug: { $eq: slug } }, populate: '*' }
     );
   }
   ```
2. Use `StrapiMediaPipe` in templates for all image and video bindings:
   ```html
   <img [src]="article.coverImage?.url | strapiMedia" [alt]="article.title" />
   ```

### Phase 4: Proactive Strapi Schema Prompting Protocol
If a frontend design requires fields absent from the Strapi response:
1. **Never mock or hardcode** static strings in the template.
2. Present the standardized prompt from `assets/proactive-schema-prompt.md` to the user:
   ```text
   ⚠️ Strapi Schema Deficit: The field 'heroSubtitle' is missing from 'HeroBanner'.
   Copy/Paste this prompt into your Strapi project:
   "Add a localized string field 'heroSubtitle' to the 'HeroBanner' single-type in Strapi."
   ```

---

## 3. Core Architecture Implementations

### Dynamic Media Pipe (`src/app/shared/pipes/strapi-media.pipe.ts`)
```typescript
import { Pipe, PipeTransform, inject } from '@angular/core';
import { STRAPI_BASE_URL } from '../../core/services/strapi.service';

@Pipe({
  name: 'strapiMedia',
  standalone: true
})
export class StrapiMediaPipe implements PipeTransform {
  private readonly baseUrl = inject(STRAPI_BASE_URL);

  transform(url?: string | null): string {
    if (!url) return '';
    if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('//')) {
      return url;
    }
    const normalizedBase = this.baseUrl.replace(/\/$/, '');
    const normalizedPath = url.startsWith('/') ? url : `/${url}`;
    return `${normalizedBase}${normalizedPath}`;
  }
}
```

### Type-Safe Client Service with SSR Caching (`src/app/core/services/strapi.service.ts`)
```typescript
import { Injectable, inject, PLATFORM_ID, makeStateKey, TransferState, InjectionToken } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { isPlatformBrowser } from '@angular/common';
import { Observable, of } from 'rxjs';
import { tap } from 'rxjs/operators';
import { StrapiResponse, StrapiQueryParams } from '../models/strapi-models';

export const STRAPI_BASE_URL = new InjectionToken<string>('STRAPI_BASE_URL', {
  providedIn: 'root',
  factory: () => 'http://localhost:1337'
});

@Injectable({ providedIn: 'root' })
export class StrapiService {
  private readonly http = inject(HttpClient);
  private readonly transferState = inject(TransferState);
  private readonly platformId = inject(PLATFORM_ID);
  private readonly baseUrl = inject(STRAPI_BASE_URL);

  get<T>(endpoint: string, query?: StrapiQueryParams): Observable<StrapiResponse<T>> {
    const url = `${this.baseUrl.replace(/\/$/, '')}/${endpoint.replace(/^\//, '')}`;
    return this.http.get<StrapiResponse<T>>(url);
  }

  getWithTransferState<T>(cacheKey: string, endpoint: string, query?: StrapiQueryParams): Observable<StrapiResponse<T>> {
    const key = makeStateKey<StrapiResponse<T>>(cacheKey);

    if (this.transferState.hasKey(key)) {
      const cached = this.transferState.get(key, null as unknown as StrapiResponse<T>);
      this.transferState.remove(key);
      if (cached) return of(cached);
    }

    return this.get<T>(endpoint, query).pipe(
      tap((response) => {
        if (!isPlatformBrowser(this.platformId)) {
          this.transferState.set(key, response);
        }
      })
    );
  }
}
```

---

## 4. Automated Compliance Verification

Verify codebase compliance using the bundled audit CLI:
```bash
# Run audit against src directory
python3 frameworks/angular/skills/angular-strapi-integration/scripts/audit_strapi_integration.py src

# Run in strict mode for CI/CD pipelines
python3 frameworks/angular/skills/angular-strapi-integration/scripts/audit_strapi_integration.py --strict

# Output machine-readable JSON
python3 frameworks/angular/skills/angular-strapi-integration/scripts/audit_strapi_integration.py --json
```

---

## 5. Gotchas & Anti-Patterns

| Category | Deprecated / Broken Pattern (❌) | Modern Production Replacement (✅) |
|---|---|---|
| **Hardcoding Copy** | Writing static headlines or paragraphs in `.html` templates | Bind all text dynamically from Strapi models (`{{ article.title }}`) |
| **Media Resolution** | Hardcoding `'http://localhost:1337' + url` or local image paths | Use standalone `StrapiMediaPipe` (`[src]="img.url \| strapiMedia"`) |
| **Strapi v4 Attributes** | Traversing nested v4 attributes (`res.data.attributes.title`) | Bind directly to flat v5 document properties (`res.data.title`) |
| **Missing Relations** | Expecting media/categories in default query (omitted by Strapi) | Pass explicit `populate=*` or granular field arrays in request query |
| **SSR Hydration** | Refetching data on client hydration, causing UI screen flicker | Serialize server data via Angular `TransferState` (`makeStateKey`) |
| **Missing Schema Fields** | Creating fake mock data arrays in component files when fields missing | Output copy-pasteable schema prompt using `proactive-schema-prompt.md` |
| **Type Safety** | Using explicit `any` for Strapi API responses and components | Define strict TypeScript models extending `StrapiBaseDocument` |
| **Rich Text XSS** | Rendering raw Strapi markdown/HTML via unchecked `[innerHTML]` | Sanitize HTML or use verified markdown parser (e.g. `ngx-markdown`) |
