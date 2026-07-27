---
description: "Step-by-step workflow to configure Angular Material UI with Dark Theme as default, OS preference detection, Signal ThemeService, theme toggle component, M3 SCSS palettes, and Google Fonts typography. Triggered by 'material-theme:', 'setup-material:', or '/setup-angular-material-theme'."
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

### Step 2: Add Google Fonts & Material Icons to `src/index.html`
Add Google Fonts (`Inter`, `Outfit`, `Roboto`) and Material Icons link tags in `src/index.html`.

### Step 3: Configure SCSS Typography & M3 Theme Palettes
1. Create `src/styles/_typography.scss` with M3 font family tokens (`--app-font-heading: 'Outfit'`, `--app-font-body: 'Inter'`).
2. Create `src/styles/_theme.scss` applying `mat.define-theme` for both `.dark-theme` (default) and `.light-theme`.
3. Import `_theme.scss` in `src/styles.scss`.

### Step 4: Create Signal-Driven Reactive `ThemeService`
Create `src/app/core/services/theme.service.ts` using Angular Signals (`isDarkMode = signal<boolean>(true)`). Check `localStorage` first, fallback to `window.matchMedia('(prefers-color-scheme: dark)')`, defaulting to `true` (Dark Mode).

### Step 5: Create Header Theme Toggle Component
Create `src/app/shared/components/theme-toggle/theme-toggle.component.ts` using `<button mat-icon-button>` with `dark_mode` / `light_mode` Material icons to invoke `themeService.toggleTheme()`.

### Step 6: Verify Theme Persistence
1. Run local dev server (`pnpm run dev`).
2. Verify root `<html>` element toggles between `.dark-theme` and `.light-theme`.
3. Verify choice persists across browser page reloads in `localStorage`.
