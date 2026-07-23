---
trigger: always_on
description: "General project context and architectural mandate for Seyalicraft Portfolio Showcase (Angular 21, Material 3, SSR, Cloudflare Workers)."
---
# Seyalicraft Project Context & Architectural Mandate

## Project Overview
**Seyalicraft** (`seyalicraft-frontend`) is a high-performance, edge-deployed professional portfolio and engineering showcase platform built by Murali. Hosted on Cloudflare Pages/Workers, it demonstrates modern full-stack web capabilities, interactive developer tools, case-study project showcases, and technical blogs.

## Core Application Structure & Domain Pages

| Route | Page | Purpose & Key Components |
| :--- | :--- | :--- |
| `/` | **Home** | Hero banner, technical skill stack matrix, featured projects, recent blog highlights |
| `/projects` | **Projects Showcase** | Searchable/filterable gallery of engineering projects, architecture diagrams, live demo links |
| `/blog` | **Blog & Insights** | Technical articles, tutorials, and software architecture deep-dives |
| `/tools` | **Developer Tools** | Interactive client-side developer utility tools and calculators |
| `/contact` | **Contact** | Interactive contact form with Reactive Forms validation |

## Tech Stack & Architectural Mandates

### 1. Framework & Core Paradigm
- **Angular Version**: Angular 21.x (`standalone: true` default).
- **Control Flow**: Native `@if`, `@for`, `@switch` control flow blocks only. Legacy `*ngIf` / `*ngFor` directives are strictly forbidden.
- **State Management**: Signals (`signal()`, `computed()`, `input()`, `output()`) for local and shared reactive state.

### 2. Styling & UI Tokens
- **Design System**: Angular Material 3 (`@angular/material` v21) with modern `mat.define-theme` SCSS mixins and CSS custom properties.
- **Component Styling**: Encapsulated component SCSS consuming global theme tokens. Avoid ad-hoc hex colors, inline styles (`style="..."`), or un-guarded `::ng-deep`.

### 3. Edge SSR & Hydration
- **Engine**: `@angular/ssr` rendered on Cloudflare Workers edge via Wrangler (`wrangler.jsonc`).
- **DOM Guarding**: Browser-only APIs (`window`, `localStorage`) MUST be guarded with `isPlatformBrowser(this.platformId)`.

### 4. Testing & Package Management
- **Test Runner**: Vitest (`pnpm test`).
- **Package Manager**: `pnpm` (`pnpm-lock.yaml`).

## Code Quality & Standards Enforcement
- **Zero `any` Type**: Strict TypeScript types across all components, models, and services.
- **Accessibility**: All interactive elements must satisfy WCAG AA standards (proper `aria-*` tags, focus indicators).
- **Service Layer**: Components must remain presentation-only ("dumb"); all data fetching and business logic belong in injectable services (`providedIn: 'root'`).
