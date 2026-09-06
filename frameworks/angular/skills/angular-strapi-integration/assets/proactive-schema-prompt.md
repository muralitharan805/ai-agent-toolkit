# Proactive Strapi Schema Generation Prompt Template

When an Angular frontend component requires CMS content that is not yet modeled in Strapi, NEVER hardcode mock data or fallback strings. Instead, generate and present the following structured prompt to the developer to execute in their Strapi backend workspace.

---

## Copy-Paste Prompt Template for Strapi Workspace

```text
Target Content-Type / Component: [CollectionName | SingleTypeName | ComponentName]
Purpose: [Explain frontend requirement, e.g., "Add a secondary call-to-action button to the Hero Banner"]

Please update the Strapi schema for '[Content-Type]' with the following field specification:

1. Field Name: [fieldName]
2. Field Type: [string | text | richtext | media | relation | component | boolean]
3. Attributes:
   - required: [true | false]
   - default: [optional defaultValue]
   - localized: [true | false]
4. Description / UI Hint: "[UI display purpose]"

Please update the schema schema.json under `src/api/[content-type]/content-types/[content-type]/schema.json` or `src/components/[category]/[component].json` and ensure it is exported in TypeScript types.
```

---

## Example Usage: Missing Hero Banner Subtitle

```text
Target Content-Type: HeroBanner (single-type or shared component)
Purpose: Support localized subtitle copy beneath the primary hero headline.

Please update the Strapi schema for 'HeroBanner':
1. Field Name: subtitle
2. Field Type: text (short or long text)
3. Attributes:
   - required: true
   - localized: true
4. Description: "Secondary explanatory copy displayed beneath the main hero title"

Update `src/components/sections/hero-banner.json` accordingly.
```
