# Angular SSR TransferState & Strapi Media Resolution

This reference details the mechanics of SSR hydration caching via `TransferState` and media URL resolution when consuming Strapi CMS assets in Angular applications.

---

## 1. Why `TransferState` is Mandatory in Angular SSR with Strapi

In Angular Server-Side Rendering:
1. The server receives the incoming HTTP request.
2. Angular executes the component lifecycle and fetches data from Strapi via `HttpClient`.
3. The server renders the initial HTML string and sends it to the browser.
4. The browser loads the JavaScript bundles and begins client **Hydration**.
5. **The Bug without `TransferState`**: If the client component executes the same `HttpClient` request during hydration, the UI flickers or rerenders, generating redundant load on the Strapi database.

### The Solution: State Serialization
`TransferState` serializes the server-fetched CMS data into a `<script id="ng-state" type="application/json">` block within the pre-rendered HTML. When the client hydrates, it reads from this embedded JSON state synchronously without executing any network calls.

```typescript
// Core TransferState pattern
const key = makeStateKey<Article>('article_slug_xyz');

if (this.transferState.hasKey(key)) {
  const data = this.transferState.get(key, null);
  this.transferState.remove(key); // Free memory
  return of(data);
}

return this.http.get<Article>('/api/articles/...').pipe(
  tap(data => {
    if (!isPlatformBrowser(this.platformId)) {
      this.transferState.set(key, data);
    }
  })
);
```

---

## 2. Dynamic Media URL Resolution Mechanics

Strapi Media Library behaves differently depending on the storage provider:
- **Local Upload Provider**: Returns relative paths starting with `/uploads/...` (e.g. `/uploads/hero_banner.webp`).
- **Cloud Storage Provider (S3 / Cloudflare R2 / Cloudinary)**: Returns absolute HTTPS URLs (e.g. `https://pub-xyz.r2.dev/hero_banner.webp`).

### The `StrapiMediaPipe` Invariant
Components must never manually concatenate strings like `'http://localhost:1337' + item.url`. Instead, pass the URL through `StrapiMediaPipe`:
```html
<img [src]="item.coverImage.url | strapiMedia" [alt]="item.title" />
```

The pipe automatically inspects the prefix:
- If the URL already begins with `http://` or `https://`, it returns it untouched.
- If the URL is relative, it prepends `environment.strapiApiUrl`.

---

## 3. Responsive Image Formats (`srcset`)

Strapi automatically generates responsive variations during media upload:
- `formats.thumbnail`: $156 \times 156$
- `formats.small`: $500\text{px}$ width
- `formats.medium`: $750\text{px}$ width
- `formats.large`: $1000\text{px}$ width

### Responsive Picture Syntax:
```html
@if (article.coverImage.formats; as formats) {
  <picture>
    @if (formats.large) {
      <source media="(min-width: 1024px)" [srcset]="formats.large.url | strapiMedia">
    }
    @if (formats.medium) {
      <source media="(min-width: 768px)" [srcset]="formats.medium.url | strapiMedia">
    }
    <img [src]="article.coverImage.url | strapiMedia" [alt]="article.title" loading="lazy" />
  </picture>
}
```
