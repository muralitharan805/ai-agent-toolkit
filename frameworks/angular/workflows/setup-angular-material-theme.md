---
description: "Configures Angular Material UI with Dark Theme default, OS detection, Signal ThemeService, theme toggle, and M3 SCSS palettes. Triggered by 'material-theme:', 'setup-material:', or '/setup-angular-material-theme'."
trigger: manual
---

# Setup Angular Material Dark Theme Default & Theme Toggle Workflow

## Objective
Scaffold and configure Angular Material (`@angular/material`) in an Angular project with **Dark Theme enabled as default** (supporting OS preference detection), a Signal-driven reactive `ThemeService`, a header theme toggle button, centralized SCSS M3 palettes, and Google Fonts typography (`Inter`, `Roboto`, `Outfit`).

---

## Execution Steps

### Step 1: Install Angular Material & CDK
```bash
pnpm add @angular/material @angular/cdk
```

### Step 2: Add Google Fonts, Material Icons & 0-FOUC Script to `src/index.html`
1. Add Google Fonts (`Inter`, `Outfit`, `Roboto`) and Material Icons link tags in `src/index.html`.
2. Add synchronous 0ms `<head>` script to read `localStorage.getItem('app-theme-preference')` at Frame 0 to prevent dark/light Flash of Unstyled Content (FOUC) on reload.

### Step 3: Configure SCSS Typography, M3 Theme Palettes & MDC Overrides
1. Create `src/styles/_typography.scss` with M3 font family tokens (`--app-font-heading: 'Outfit'`, `--app-font-body: 'Inter'`).
2. Create `src/styles/_theme.scss` applying `mat.define-theme` for both `.dark-theme` (default) and `.light-theme`.
3. Add high-specificity MDC overrides in `src/styles.scss` for `mat-card, .mat-mdc-card` and `mat-form-field` to enforce CSS custom property inheritance (`var(--bg-card)`, `var(--text-primary)`, `var(--border-color)`).

### Step 4: Create Signal-Driven Reactive `ThemeService`
Create `src/app/core/services/theme.service.ts` using Angular Signals (`isDarkMode = signal<boolean>(true)`). Check `localStorage` first, fallback to `window.matchMedia('(prefers-color-scheme: dark)')`, defaulting to `true` (Dark Mode).

### Step 5: Create Header Theme Toggle Component
Create `src/app/shared/components/theme-toggle/theme-toggle.component.ts` using `<button mat-icon-button>` with `dark_mode` / `light_mode` Material icons to invoke `themeService.toggleTheme()`.

### Step 6: Verify Theme Persistence & AAA Contrast
1. Run local dev server (`pnpm run start:staging`).
2. Verify root `<html>` element toggles between `.dark-theme` and `.light-theme`.
3. Verify choice persists across browser page reloads in `localStorage` without any visual FOUC flash.
4. Verify text components maintain high AAA contrast in both Light and Dark themes.
