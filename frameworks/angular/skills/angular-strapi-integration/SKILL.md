---
name: angular-strapi-integration
description: "Strict development guidelines for enterprise Angular SSR frontends that are heavily dependent on Strapi CMS. Enforces zero hardcoding of data/assets, API-driven dynamic rendering, and proactive Strapi schema generation prompts."
---

# Goal
Ensure that the Angular SSR frontend is 100% dynamic and completely driven by the Strapi CMS API. There must be zero hardcoded content, text, or media assets within the Angular application components. This context guides AI agents to fetch all necessary data dynamically and proactively suggest backend modifications when data is missing.

# Core Development Principles

## 1. Zero Hardcoding Rule
- **STRICT ENFORCEMENT**: You must NEVER hardcode any content (titles, paragraphs, lists, links, image URLs, etc.) directly in HTML templates or TypeScript component classes.
- All dynamic data MUST be consumed from a Strapi REST or GraphQL API response.
- Static assets (like global SVGs or logos) can be local, but any content-driven images or galleries MUST be loaded via the Strapi Media Library URL.

## 2. API-First Architecture
- If a component requires data to render, you must inject an Angular Service that calls the appropriate Strapi API endpoint.
- If the required API endpoint is unknown or missing, explicitly ask the user for the endpoint URL or the API structure before attempting to implement mock data.

## 3. Proactive Strapi Schema Suggestions
If you identify that required data is not available in the current Strapi API response, or if a new component is being built that requires new CMS fields:
1. **DO NOT** fallback to hardcoding the data.
2. **SUGGEST** to the user that this data should be added to the Strapi CMS.
3. **PROVIDE A PROMPT** that the user can directly copy and paste into their Strapi project to have another AI agent generate the required Strapi schema.

## 4. Advanced CMS & SSR Integration Rules
- **Dynamic SEO & Meta Tags**: NEVER hardcode `<title>` or `<meta>` tags in `index.html`. Always use Angular's `Title` and `Meta` services to dynamically inject metadata based on the `Shared.Seo` Strapi component.
- **Strapi Query Population (`?populate=`)**: Strapi does not return nested relations (like media, dynamic zones, or SEO components) by default. ALWAYS ensure your API requests explicitly include query parameters like `?populate=*` or deep population logic to fetch necessary relational data.
- **Dynamic Routing & 404 Handling**: Page routing MUST rely on CMS slugs (e.g., `/:slug`). If the Strapi API returns a 404 or empty data for a slug, the Angular app MUST gracefully redirect to a dynamic 404 Not Found page to avoid broken UI states.
- **Rich Text / Markdown Security**: Content coming from Strapi Rich Text editors MUST be rendered securely. Utilize Angular's `DomSanitizer` (`bypassSecurityTrustHtml`) or a verified markdown library (like `ngx-markdown`) to prevent XSS vulnerabilities.
- **SSR State Transfer**: To prevent screen flickering and duplicate API calls upon client hydration, you MUST use Angular's `TransferState` (or `makeStateKey`). Fetch the Strapi data on the server, transfer the state to the browser, and read from the state cache before making client-side HTTP calls.

# Instructions

When developing or updating Angular components in this ecosystem:

1. **Check for Data Source**: Verify if the data is being fetched from a Strapi service.
2. **Implement Fetch Logic**: Use Angular's `HttpClient` (or relevant service wrappers) to fetch data from Strapi. For SSR, ensure data fetching is properly handled (e.g., using `TransferState` or resolving data before rendering to avoid layout shifts).
3. **Handle Missing Data**:
   - If the API doesn't provide the data, output a clear warning/suggestion to the user.
   - Example format for suggestion:
     *"I noticed that the `Hero Banner Subtitle` is missing from the Strapi API response. We should add this to the CMS rather than hardcoding it."*
   - Example format for the prompt:
     ```text
     **Copy/Paste this prompt in your Strapi project:**
     "I need to add a new string field called 'subtitle' to the 'HeroBanner' component/collection in Strapi. Please generate the necessary schema update for this."
     ```
4. **Environment Variables**: Always use Angular environment variables (`environment.strapiApiUrl`) for constructing API endpoints and Media URLs. Do not hardcode the API domain.
5. **Strict `pnpm` Usage**: Use `pnpm` for all package management tasks.

# Constraints
- NEVER hardcode text content or image paths in Angular templates or components.
- Do not make assumptions about API schemas; ask the user if the structure is not provided.
- Always append the base Strapi URL to media asset paths returned by Strapi, as Strapi often returns relative URLs for media.
