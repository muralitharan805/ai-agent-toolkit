---
trigger: always_on
description: "Strictly enforces a zero-hardcoding policy across all Angular frontend applications that consume Strapi APIs, ensuring dynamic data binding and proactive schema generation."
---
# Angular & Strapi Zero-Hardcoding Rule

## Description
This rule strictly enforces a zero-hardcoding policy across all Angular frontend applications that consume Strapi APIs. It ensures that AI agents always fetch text, metadata, and media dynamically from the CMS and never write static content into HTML templates or TS files.

## Constraints
- **NO STATIC CONTENT**: You MUST NEVER hardcode titles, descriptions, lists, or image sources in Angular `.html` or `.ts` files.
- **DYNAMIC BINDING ONLY**: All content-driven data MUST be bound dynamically (e.g., `[src]="article.coverImage.url"`, `{{ project.title }}`).
- **PROACTIVE CMS PROMPT**: If the requested data does not exist in the API response, DO NOT mock it or hardcode it. You MUST output a prompt for the user to copy/paste into their Strapi backend to generate the necessary schema field.
- **SSR AWARENESS**: Fetch data dynamically, but ensure SSR state transfer (`TransferState`) is used to prevent layout shifts or duplicate API calls.

## Examples
- **Correct implementation:**
```html
<!-- Data bound dynamically from the CMS API response -->
<section class="hero">
  <h1>{{ globalSettings.siteName }}</h1>
  <p>{{ globalSettings.metaDescription }}</p>
  <img [src]="globalSettings.favicon.url" [alt]="globalSettings.siteName" />
</section>
```

- **Incorrect implementation:**
```html
<!-- NEVER hardcode text or static paths when building a CMS-driven site -->
<section class="hero">
  <h1>Seyalicraft Portfolio</h1>
  <p>Welcome to my software engineering portfolio.</p>
  <img src="assets/logo.png" alt="Logo" />
</section>
```
