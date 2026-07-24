---
description: "Step-by-step workflow to configure Angular Material UI, integrate Google Fonts typography, setup M3 SCSS theme palettes, and enforce primary Material UI components across Angular applications. Triggered by 'material-theme:', 'setup-material:', or '/setup-angular-material-theme'."
trigger: manual
---
# Setup Angular Material SCSS Theme & Google Fonts Typography Workflow

## Objective
Scaffold and configure Angular Material (`@angular/material`) as the primary UI component framework in an Angular project. Establish a centralized SCSS theme structure with Google Fonts typography (`Inter`, `Roboto`, `Outfit`, `Plus Jakarta Sans`) and CSS custom property design tokens supporting dark and light theme switching.

## Prerequisites
- Existing Angular application (v15+) with SCSS enabled (`schematics: { "@schematics/angular:component": { "style": "scss" } }`).
- Node.js and Angular CLI installed.

## Execution Steps

### Step 1: Install Angular Material & CDK
Install the mandatory Angular Material packages:
```bash
pnpm add @angular/material @angular/cdk
```

### Step 2: Inject Google Fonts into `src/index.html`
Add high-legibility Google Fonts links to the `<head>` of `src/index.html`:
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@500;600;700&family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
```

### Step 3: Create Central Typography Configuration
Create `src/styles/_typography.scss`:
```scss
@use '@angular/material' as mat;

:root {
  --app-font-body: 'Inter', 'Roboto', sans-serif;
  --app-font-heading: 'Outfit', 'Roboto', sans-serif;
}

$app-typography: mat.define-theme((
  typography: (
    plain-family: var(--app-font-body),
    brand-family: var(--app-font-heading),
    bold-weight: 700,
    medium-weight: 500,
    regular-weight: 400
  )
));
```

### Step 4: Create Centralized SCSS Theme Architecture
Create `src/styles/_theme.scss` defining palettes, M3 theme configuration, and dark mode switches:
```scss
@use '@angular/material' as mat;
@use './typography' as app-type;

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
    plain-family: var(--app-font-body),
    brand-family: var(--app-font-heading),
  )
));

$dark-theme: mat.define-theme((
  color: (
    theme-type: dark,
    primary: $primary-palette,
    tertiary: $tertiary-palette,
  ),
  typography: (
    plain-family: var(--app-font-body),
    brand-family: var(--app-font-heading),
  )
));
```

### Step 5: Configure Global Styles in `src/styles/styles.scss`
Include global tokens and root theme application:
```scss
@use './styles/theme' as app-theme;
@use '@angular/material' as mat;

html {
  @include mat.all-component-themes(app-theme.$light-theme);
  font-family: var(--app-font-body);
}

html.dark-theme {
  @include mat.all-component-colors(app-theme.$dark-theme);
}

body {
  margin: 0;
  font-family: var(--app-font-body);
  background-color: var(--mat-sys-background);
  color: var(--mat-sys-on-background);
  -webkit-font-smoothing: antialiased;
}

h1, h2, h3, h4, h5, h6 {
  font-family: var(--app-font-heading);
}
```

### Step 6: Material First UI Component Mapping Checklist
Ensure components throughout the application use Angular Material primitives:
- [ ] **Table**: Replace native HTML `<table>` with `<table mat-table>` and `<mat-paginator>`.
- [ ] **Button**: Replace `<button>` with `<button mat-flat-button color="primary">`.
- [ ] **Input**: Replace `<input>` with `<mat-form-field appearance="outline"><input matInput></mat-form-field>`.
- [ ] **Dropdown**: Replace `<select>` with `<mat-select><mat-option></mat-option></mat-select>`.
- [ ] **Dialog**: Use `MatDialog` service with `<mat-dialog-content>`.
- [ ] **Card & Panel**: Replace generic container `<div>` elements with `<mat-card>`.

### Step 7: Fallback Component Audit
Audit all non-Material components (e.g. specialized charts or third-party widgets) to verify they consume `var(--mat-sys-*)` tokens for background, border, text color, and typography.

## Expected Output
A unified Angular Material UI infrastructure with central SCSS theme palettes and Google Fonts typography globally applied across all components, tables, inputs, dropdowns, buttons, and custom fallbacks.
