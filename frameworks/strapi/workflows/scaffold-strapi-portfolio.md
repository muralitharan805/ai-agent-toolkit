---
description: "Workflow to automatically scaffold a complete Strapi Portfolio/CMS schema including Collections (Project, Article, Experience, Skill) and Single Types (Global, About). Triggered by 'scaffold-portfolio', '/scaffold-strapi-portfolio'."
trigger: manual
---

# Scaffold Strapi Portfolio Backend

## Persona
Act as an expert Strapi CMS Architect. Your objective is to scaffold a production-grade portfolio backend inside an existing Strapi project by following the universal `strapi-portfolio-context` skill.

## Task Protocol
1. **Context Verification**: Read the `frameworks/strapi/skills/strapi-portfolio-context/SKILL.md` file to understand the exact schema structure required (Collections, Single Types, Components).
2. **Scaffold Collections**: Use Strapi CLI or modify Strapi API files directly to create the following Collections:
   - `Project`
   - `Skill`
   - `Experience`
   - `Article`
3. **Scaffold Single Types**:
   - `Global`
   - `About`
4. **Scaffold Components**:
   - `Shared.Seo`
   - `Shared.SocialLink`
5. **Apply Advanced Constraints**: 
   - Ensure all `slug` fields are set as UID.
   - Enable Draft/Publish for `Project` and `Article`.
   - Setup `beforeCreate` and `beforeUpdate` lifecycle hooks for slug generation where applicable.
6. **Documentation**: Provide the user with a summary of the created APIs and remind them to grant `find` / `findOne` permissions to the Public role via the Strapi Admin UI.
