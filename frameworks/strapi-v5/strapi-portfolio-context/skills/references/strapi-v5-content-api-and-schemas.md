# Strapi v5 Content Types & Schema Architecture

## Overview
Strapi v5 introduces significant architectural updates over v4, including native document-based drafting (`draftAndPublish`), simplified REST and GraphQL response payloads (flattening the legacy v4 `data.attributes` nesting), and the new **Document Service API**.

---

## 1. Schema Definition Format (`schema.json`)
Every collection type in Strapi v5 is declared inside `src/api/<collection-name>/content-types/<collection-name>/schema.json`:

```json
{
  "kind": "collectionType",
  "collectionName": "projects",
  "info": {
    "singularName": "project",
    "pluralName": "projects",
    "displayName": "Project",
    "description": "Portfolio project item and case study"
  },
  "options": {
    "draftAndPublish": true
  },
  "pluginOptions": {},
  "attributes": {
    "title": {
      "type": "string",
      "required": true,
      "maxLength": 120
    },
    "slug": {
      "type": "uid",
      "targetField": "title",
      "required": true
    },
    "shortDescription": {
      "type": "text",
      "required": true
    },
    "content": {
      "type": "blocks",
      "required": true
    },
    "coverImage": {
      "type": "media",
      "multiple": false,
      "required": true,
      "allowedTypes": ["images"]
    },
    "skills": {
      "type": "relation",
      "relation": "manyToMany",
      "target": "api::skill.skill",
      "inversedBy": "projects"
    },
    "seo": {
      "type": "component",
      "repeatable": false,
      "component": "shared.seo"
    }
  }
}
```

---

## 2. Mandatory UID Slugs & Indexing
- **Type**: Must always declare `"type": "uid"`.
- **Target Field**: Attach to the entity's primary human-readable title or name (`"targetField": "title"`).
- **Frontend SPA Resolution**: In Single Page Applications (Angular, React), routes are resolved by `/projects/:slug` rather than numeric database IDs.

---

## 3. Rich Content: Strapi Blocks vs Markdown
- Strapi v5 defaults to the structured **Blocks Editor** (`"type": "blocks"`), returning an AST JSON array representing headings, paragraphs, lists, and code blocks.
- Frontend apps parse Blocks into semantic HTML or render them via native components (`@strapi/blocks-react-renderer` or custom Angular Pipes).

---

## 4. Public Role Permissions
By default, new Strapi APIs are locked. The developer or deployment script must enable `find` and `findOne` permissions under **Settings > Users & Permissions Plugin > Roles > Public** for:
- `api::project.project`
- `api::skill.skill`
- `api::experience.experience`
- `api::article.article`
- `api::global.global`
- `api::about.about`
