---
trigger: always_on
description: "Mandates Angular Material UI as the primary component framework (Tables, Buttons, Form Inputs, Dropdowns, Dialogs) and enforces global SCSS theme tokens and Google Fonts typography across all Angular app surfaces."
---
# Angular Material Primary Component & SCSS Theme Rule

## Description
This rule mandates Angular Material (`@angular/material`) as the primary UI component library for all standard UI elements across Angular applications. It also enforces a centralized SCSS theme design system integrated with modern Google Fonts typography (`Inter`, `Roboto`, `Outfit`, `Plus Jakarta Sans`), prohibiting hardcoded hex colors, arbitrary inline font declarations, or non-theme custom styling.

## Constraints

### 1. Angular Material First Component Policy
- The agent MUST prioritize Angular Material components for all standard user interface elements:
  - **Tables & Data Grids**: `<table mat-table>`, `<mat-paginator>`, `matSort`.
  - **Buttons & Actions**: `mat-button`, `mat-flat-button`, `mat-stroked-button`, `mat-icon-button`, `mat-fab`.
  - **Form Fields & Inputs**: `<mat-form-field>`, `<input matInput>`, `<textarea matInput>`.
  - **Dropdowns & Selection**: `<mat-select>`, `<mat-option>`, `<mat-autocomplete>`.
  - **Dialogs & Modals**: `MatDialog` service and `<mat-dialog-content>`.
  - **Navigation & Layout**: `<mat-toolbar>`, `<mat-sidenav>`, `<mat-nav-list>`, `<mat-card>`.
  - **Selection Controls**: `<mat-checkbox>`, `<mat-radio-button>`, `<mat-slide-toggle>`.
  - **Feedback & Overlays**: `<mat-tooltip>`, `<mat-menu>`, `MatSnackBar`, `<mat-progress-bar>`, `<mat-spinner>`.

### 2. Restrictive Component Fallback Policy
- Alternative third-party component libraries or custom component builds are permitted ONLY IF Angular Material lacks a native equivalent or specific required feature (e.g., complex multi-layered data grid, rich text editor).
- When a fallback custom component is created, it MUST consume global CSS custom properties (`var(--mat-sys-*)`) and typography variables to ensure 100% visual and structural theme harmony.

### 3. Centralized SCSS Theme & Google Fonts Typography Architecture
- **Google Fonts Loading**: High-legibility Google Fonts (e.g., `Inter`, `Roboto`, `Outfit`, or `Plus Jakarta Sans`) MUST be loaded globally in `index.html` or `src/styles.scss`.
- **Global Theme Tokens**: All colors, surface elevations, rounded corners, and font scales MUST originate from the centralized theme setup in `src/styles/_theme.scss` and `src/styles/_typography.scss`.
- **Material 3 Token Consumption**: Components MUST use M3 tokens (e.g., `var(--mat-sys-primary)`, `var(--mat-sys-on-surface)`, `var(--mat-sys-surface-container)`) instead of hardcoded hex values (`#1976d2`) or static RGB colors.
- **No Unscoped Internal Overrides**: The agent MUST NOT use `::ng-deep` to override component internal CSS unless scoped strictly inside a parent selector using M3 custom property declarations.

## Examples

- **Correct Component Implementation (Material UI First):**
```html
<!-- src/app/features/users/user-list.component.html -->
<div class="user-container">
  <mat-form-field appearance="outline" class="search-field">
    <mat-label>Filter Department</mat-label>
    <mat-select [formControl]="departmentControl">
      <mat-option value="all">All Departments</mat-option>
      <mat-option value="engineering">Engineering</mat-option>
      <mat-option value="design">Design</mat-option>
    </mat-select>
  </mat-form-field>

  <table mat-table [dataSource]="dataSource" class="mat-elevation-z1">
    <ng-container matColumnDef="name">
      <th mat-header-cell *matHeaderCellDef> Name </th>
      <td mat-cell *matCellDef="let element"> {{element.name}} </td>
    </ng-container>

    <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
    <tr mat-row *matRowDef="let row; columns: displayedColumns;"></tr>
  </table>

  <mat-paginator [pageSizeOptions]="[5, 10, 20]" showFirstLastButtons></mat-paginator>

  <button mat-flat-button color="primary" (click)="addUser()">
    Add New User
  </button>
</div>
```

- **Correct SCSS Styling (Consuming Global Theme Tokens & Google Fonts):**
```scss
// src/styles/_typography.scss
@use '@angular/material' as mat;

$typography-config: (
  plain-family: "'Inter', 'Roboto', sans-serif",
  brand-family: "'Outfit', 'Plus Jakarta Sans', sans-serif",
  bold-weight: 700,
  medium-weight: 500,
  regular-weight: 400
);

// Component SCSS using Material CSS variables
.user-container {
  background-color: var(--mat-sys-surface-container-low);
  color: var(--mat-sys-on-surface);
  font-family: var(--app-font-body, 'Inter', sans-serif);
  padding: 1.5rem;
  border-radius: var(--mat-sys-corner-large, 16px);
}
```

- **Incorrect Implementation (Hardcoded Hex & Legacy HTML Controls):**
```html
<!-- Violates Material First Policy and Theme Tokens -->
<div style="background-color: #f5f5f5; font-family: Arial;">
  <select style="color: #333;"> <!-- Legacy HTML Select instead of mat-select -->
    <option>Engineering</option>
  </select>
  <button style="background: #1976d2; color: white;">Save</button> <!-- Inline hardcoded colors -->
</div>
```
