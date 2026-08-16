---
name: strapi-portfolio-context
description: "Context and architectural guidelines for designing, scaffolding, and managing Strapi CMS content types (Collections, Single Types, and Components) for enterprise portfolio, blog, or agency websites and related dynamic frontend ecosystems."
---

# Goal
Provide a standardized, highly dynamic, and scalable Strapi CMS schema design for a portfolio website. This context ensures that any AI agent or developer building or consuming the Strapi API adheres to a unified data architecture, enabling a fully dynamic frontend experience that can be synced across related projects.

# Core Architectural Principles
- **API-First Design**: All content schemas must be designed for easy consumption via REST or GraphQL APIs by modern frontend frameworks (e.g., Angular, Next.js).
- **Component Reusability**: Use Strapi Components for repeatable data structures (e.g., SEO metadata, social links) to keep schemas DRY.
- **Dynamic Zones**: Utilize Strapi Dynamic Zones for flexible page building where appropriate (e.g., article content blocks).
- **Relational Integrity**: Maintain clear relations (e.g., Projects <-> Skills).

# Instructions

When scaffolding or modifying Strapi content types for a portfolio project, adhere to the following schema definitions:

## 1. Single Types (Global Configurations)

### 1.1 `Global` (Site Settings)
- **siteName** (String): The name of the portfolio/site.
- **metaDescription** (Text): Default SEO description.
- **favicon** (Media - Image): Site favicon.
- **socialLinks** (Component - Repeatable): Links to GitHub, LinkedIn, Twitter, etc.
- **seo** (Component): Default SEO component.

### 1.2 `About`
- **title** (String): E.g., "About Me".
- **bio** (Rich Text / Blocks): Detailed professional biography.
- **avatar** (Media - Image): Profile picture.
- **resume** (Media - File): Downloadable PDF resume.
- **email** (String - Email): Primary contact email.

## 2. Collection Types (Dynamic Content)

### 2.1 `Project` (Portfolio Items)
- **title** (String): Project name.
- **slug** (UID attached to title): URL-friendly slug.
- **shortDescription** (Text): Brief summary for cards.
- **coverImage** (Media - Image): Main thumbnail.
- **gallery** (Media - Multiple): Screenshots or architecture diagrams.
- **content** (Rich Text / Blocks): Detailed project case study.
- **demoUrl** (String - URL): Link to live demo.
- **githubUrl** (String - URL): Link to source code.
- **startDate** (Date): Project start.
- **endDate** (Date): Project completion (null if ongoing).
- **skills** (Relation - Many-to-Many): Related `Skill` entries.

### 2.2 `Skill` (Tech Stack)
- **name** (String): E.g., "Angular", "NestJS", "Strapi".
- **slug** (UID attached to name).
- **icon** (Media - Image or String for SVG code): Visual representation.
- **category** (Enumeration): [Frontend, Backend, DevOps, Database, Tools, Design].
- **proficiency** (Integer/Enumeration): Skill level (e.g., 1 to 5).
- **projects** (Relation - Many-to-Many): Projects utilizing this skill.

### 2.3 `Experience` (Work History)
- **company** (String): Employer or client name.
- **role** (String): Job title.
- **location** (String): City/Remote.
- **startDate** (Date).
- **endDate** (Date).
- **isCurrent** (Boolean): True if currently employed here.
- **description** (Rich Text / Blocks): Responsibilities and achievements.

### 2.4 `Article` (Blog Posts)
- **title** (String): Article headline.
- **slug** (UID attached to title).
- **coverImage** (Media - Image).
- **excerpt** (Text): Short summary.
- **content** (Blocks / Dynamic Zone): Body of the article.
- **publishedAt** (Date).
- **seo** (Component): Post-specific SEO metadata.

## 3. Components

### 3.1 `Shared.Seo`
- **metaTitle** (String).
- **metaDescription** (Text).
- **shareImage** (Media - Image).

### 3.2 `Shared.SocialLink`
- **platform** (String): E.g., "GitHub".
- **url** (String - URL).
- **icon** (Media/String).

## 4. Advanced Backend & Deployment Rules

- **API Roles & Permissions**: By default, Strapi REST/GraphQL endpoints are secured. You MUST explicitly grant `find` and `findOne` permissions to the `Public` role for collections and single types intended for the frontend (e.g., `Project`, `Article`, `Experience`, `Skill`, `Global`, `About`).
- **Draft & Publish System**: Always enable the "Draft & publish" feature for collections like `Article` and `Project`. This prevents unfinished content from being accidentally exposed to the live frontend API.
- **Slug Indexing & Uniqueness**: The `slug` field across all collections MUST be marked as a `UID` (Unique Identifier) and indexed in the underlying database for fast frontend resolution.
- **Lifecycle Hooks for Slugs**: Proactively use Strapi Lifecycle Hooks (e.g., `beforeCreate`, `beforeUpdate`) in the backend code to automatically generate or sanitize the `slug` from the `title` or `name` field, preventing manual entry errors.
- **Production Media Storage**: In a production environment, NEVER rely on the local `public/uploads` directory for media storage. Always configure a third-party upload provider plugin (e.g., Cloudinary, AWS S3) so that media assets persist across server restarts and deployments.

# Constraints
- NEVER use standard Text fields for complex markdown; always prefer Rich Text (or the new Strapi Blocks editor).
- Slugs MUST be generated from titles/names to ensure consistent routing in the frontend SPA.
- All media fields MUST have appropriate size limits and allowed types (e.g., images only for avatars).
- Do not duplicate SEO fields across collections; always use the `Shared.Seo` component.
- MANDATORY: Strictly use `pnpm` as the package manager for all Strapi and frontend installations/dependencies (do not use `npm` or `yarn`).
