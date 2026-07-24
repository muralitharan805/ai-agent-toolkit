---
description: "Step-by-step workflow to configure Angular Material UI with Dark Theme as default, Signal ThemeService, theme toggle component, M3 SCSS palettes, and Google Fonts typography. Triggered by 'material-theme:', 'setup-material:', or '/setup-angular-material-theme'."
trigger: manual
---
# Setup Angular Material Dark Theme Default & Theme Toggle Workflow

## Objective
Scaffold and configure Angular Material (`@angular/material`) in an Angular project with **Dark Theme enabled as default**, a Signal-driven reactive `ThemeService`, a header theme toggle button, centralized SCSS M3 palettes, and Google Fonts typography (`Inter`, `Roboto`, `Outfit`).

## Prerequisites
- Existing Angular application (v15+) with SCSS enabled (`schematics: { "@schematics/angular:component": { "style": "scss" } }`).
- Node.js and Angular CLI / pnpm installed.

## Execution Steps

### Step 1: Install Angular Material & CDK
Install mandatory Angular Material packages:
```bash
pnpm add @angular/material @angular/cdk
```

### Step 2: Inject Google Fonts into `src/index.html`
Add Google Fonts and Material Icons in `src/index.html`:
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

### Step 4: Create SCSS Theme Palettes & Configurations
Create `src/styles/_theme.scss`:
```scss
@use '@angular/material' as mat;
@use './typography' as app-type;

@include mat.core();

$primary-palette: mat.$azure-palette;
$tertiary-palette: mat.$blue-palette;

// Default Dark Theme Palette
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

// Alternate Light Theme Palette
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
```

### Step 5: Configure Default Dark Theme in Global `src/styles/styles.scss`
Enforce Dark Theme as the default root theme:
```scss
@use './styles/theme' as app-theme;
@use '@angular/material' as mat;

// Dark Theme is applied by DEFAULT on root html
html, html.dark-theme {
  @include mat.all-component-themes(app-theme.$dark-theme);
  color-scheme: dark;
  font-family: var(--app-font-body);
}

// Light Theme applies when explicitly toggled by user
html.light-theme {
  @include mat.all-component-colors(app-theme.$light-theme);
  color-scheme: light;
}

body {
  margin: 0;
  background-color: var(--mat-sys-background);
  color: var(--mat-sys-on-background);
  min-height: 100vh;
  -webkit-font-smoothing: antialiased;
}

h1, h2, h3, h4, h5, h6 {
  font-family: var(--app-font-heading);
}
```

### Step 6: Create Reactive `ThemeService` (Dark Mode Default)
Create `src/app/core/services/theme.service.ts`:
```typescript
import { Injectable, signal, effect, inject, DOCUMENT } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly document = inject(DOCUMENT);
  private readonly STORAGE_KEY = 'app-theme-preference';

  // Default state is TRUE (Dark Mode active by default)
  readonly isDarkMode = signal<boolean>(this.getSavedPreference());

  constructor() {
    effect(() => {
      const dark = this.isDarkMode();
      const root = this.document.documentElement;
      
      if (dark) {
        root.classList.add('dark-theme');
        root.classList.remove('light-theme');
      } else {
        root.classList.add('light-theme');
        root.classList.remove('dark-theme');
      }
      
      localStorage.setItem(this.STORAGE_KEY, dark ? 'dark' : 'light');
    });
  }

  toggleTheme(): void {
    this.isDarkMode.update(prev => !prev);
  }

  private getSavedPreference(): boolean {
    const saved = localStorage.getItem(this.STORAGE_KEY);
    if (saved) return saved === 'dark';
    return true; // Default to dark theme if no stored preference
  }
}
```

### Step 7: Create Header Theme Toggle Component
Create `src/app/shared/components/theme-toggle/theme-toggle.component.ts`:
```typescript
import { Component, ChangeDetectionStrategy, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTooltipModule } from '@angular/material/tooltip';
import { ThemeService } from '../../../core/services/theme.service';

@Component({
  selector: 'app-theme-toggle',
  standalone: true,
  imports: [MatButtonModule, MatIconModule, MatTooltipModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <button mat-icon-button
            [matTooltip]="themeService.isDarkMode() ? 'Switch to Light Theme' : 'Switch to Dark Theme'"
            (click)="themeService.toggleTheme()"
            aria-label="Toggle Dark/Light Theme">
      <mat-icon>{{ themeService.isDarkMode() ? 'light_mode' : 'dark_mode' }}</mat-icon>
    </button>
  `
})
export class ThemeToggleComponent {
  readonly themeService = inject(ThemeService);
}
```

### Step 8: Material Component & Theme Verification Checklist
- [ ] Verify `<html>` loads with `.dark-theme` class by default.
- [ ] Verify `<app-theme-toggle>` toggles `.dark-theme` / `.light-theme` class on root `<html>`.
- [ ] Verify theme choice persists across browser reloads via `localStorage`.
- [ ] Verify all Material components (`mat-table`, `mat-form-field`, `mat-select`, `mat-card`, `mat-dialog`) seamlessly transition colors on theme switch.

## Expected Output
An enterprise Angular application configured with Dark Theme as default, an interactive Signal-driven theme switcher, persisted preferences, and full Material 3 token alignment.
