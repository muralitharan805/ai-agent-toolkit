---
trigger: always_on
description: "Mandates that all Angular component styles MUST consume global Angular Material SCSS theme tokens and variables rather than defining ad-hoc hex colors or static font sizes."
---
# Angular Material Theme Only Rule

## Description
This rule enforces strict theme-driven styling across all Angular Material components. All colors, typography, background surfaces, and dark mode palette switches must originate from the central `_theme.scss` configuration and Material design tokens.

## Constraints
- The agent MUST use Angular Material CSS custom properties (e.g., `var(--mat-sys-primary)`, `var(--mat-sys-on-surface)`, `var(--mat-sys-error)`) or SCSS theme mixins for component colors and surfaces.
- The agent MUST NOT use hardcoded hex (`#1976d2`), `rgb()`, `hsl()`, or named color strings (`red`, `blue`) inside component `.scss` files.
- The agent MUST place all custom theme palettes, typography configs, and density settings in the central `src/styles/_theme.scss` file.
- The agent MUST NOT use `::ng-deep` to apply static inline color overrides to Material components.

## Examples
- **Correct implementation:**
```scss
// src/app/feature/dashboard.component.scss
.dashboard-header {
  background-color: var(--mat-sys-surface-container-high);
  color: var(--mat-sys-on-surface);
  border-bottom: 1px solid var(--mat-sys-outline-variant);
  padding: var(--mat-sys-spacing-medium, 16px);
}
```

- **Incorrect implementation:**
```scss
// src/app/feature/dashboard.component.scss
.dashboard-header {
  background-color: #f5f5f5; // Hardcoded color!
  color: #333333;           // Hardcoded color!
  border-bottom: 1px solid #e0e0e0;
}
```
