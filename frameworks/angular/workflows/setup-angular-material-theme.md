---
description: "Step-by-step workflow to configure Angular Material, setup M3/SCSS theme palettes, define component overrides, and apply global theme tokens."
trigger: manual
---
# Setup Angular Material SCSS Theme Workflow

## Objective
Scaffold and configure Angular Material in an Angular application with a centralized SCSS theme structure supporting dark/light mode switching and material design tokens.

## Prerequisites
- Existing Angular application (v15+) with SCSS enabled (`schematics: { "@schematics/angular:component": { "style": "scss" } }`).
- Node.js and Angular CLI installed.

## Execution Steps
1. **Install Angular Material & CDK**:
   Run `ng add @angular/material` or manually install dependencies:
   ```bash
   pnpm add @angular/material @angular/cdk
   ```

2. **Create Centralized SCSS Theme Architecture**:
   Create the theme file `src/styles/_theme.scss` and define the Angular Material M3/M2 theme mixin imports:
   ```scss
   @use '@angular/material' as mat;

   @include mat.core();

   $primary-palette: mat.$azure-palette;
   $tertiary-palette: mat.$blue-palette;

   $light-theme: mat.define-theme((
     color: (
       theme-type: light,
       primary: $primary-palette,
       tertiary: $tertiary-palette,
     ),
     typography: (
       plain-family: 'Roboto, sans-serif',
     )
   ));

   $dark-theme: mat.define-theme((
     color: (
       theme-type: dark,
       primary: $primary-palette,
       tertiary: $tertiary-palette,
     )
   ));
   ```

3. **Configure Global Styles Import**:
   In `src/styles.scss`, include core mixins and apply theme tokens to the root and dark theme class:
   ```scss
   @use './styles/theme' as app-theme;
   @use '@angular/material' as mat;

   html {
     @include mat.all-component-themes(app-theme.$light-theme);
   }

   html.dark-theme {
     @include mat.all-component-colors(app-theme.$dark-theme);
   }

   body {
     margin: 0;
     font-family: Roboto, "Helvetica Neue", sans-serif;
     background-color: var(--mat-sys-background);
     color: var(--mat-sys-on-background);
   }
   ```

4. **Verify Component Style Boundary**:
   Inspect component `.scss` files across the workspace to ensure no hardcoded hex colors exist, replacing them with `--mat-sys-*` tokens.

5. **Validate Dark/Light Theme Switching**:
   Create a theme toggle service or mechanism toggling the `.dark-theme` class on the `<html>` root element and verify visual compliance.

## Expected Output
A fully functional Angular Material SCSS theme architecture where all components automatically inherit light and dark theme colors from global design tokens.
