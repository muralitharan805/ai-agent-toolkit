---
trigger: model_decision
description: "Mandates Angular Material UI as primary component library, enforces Dark Theme as default with OS system preference detection, Signal-based light/dark theme toggle, global SCSS theme tokens, and Google Fonts typography."
---
# Angular Material Primary Component, Dark Theme Default & SCSS Theme Rule

## Description
This rule mandates Angular Material (`@angular/material`) as the primary UI component library for all standard UI elements across Angular applications. It also enforces **Dark Theme as the default initial application state** (with OS preference detection fallback), a Signal-based theme toggle mechanism, a centralized SCSS theme design system, and modern Google Fonts typography (`Inter`, `Roboto`, `Outfit`, `Plus Jakarta Sans`).

## Constraints

### 1. Default Dark Theme, OS Preference & Toggle Mechanism
- **Dark Mode Default & System Detection**: Applications MUST initialize in **Dark Theme by default**, checking `localStorage` first, then evaluating `window.matchMedia('(prefers-color-scheme: dark)')`, defaulting to `true` (Dark Mode).
- **Reactive Theme Service**: Application MUST provide a reactive `ThemeService` using Angular Signals to control dark/light mode state, persisting user selection in `localStorage` and syncing the root `<html>` element CSS class (`.dark-theme` / `.light-theme`).
- **Interactive UI Toggle**: Header or shell layout MUST include a user-accessible theme toggle control (`<mat-slide-toggle>` or `<button mat-icon-button>` with `dark_mode`/`light_mode` Material icons).

### 2. Angular Material First Component Policy
- The agent MUST prioritize Angular Material components for all standard user interface elements:
  - **Tables & Grids**: `<table mat-table>`, `<mat-paginator>`, `matSort`.
  - **Buttons & Inputs**: `mat-button`, `mat-flat-button`, `mat-icon-button`, `<mat-form-field>`, `<input matInput>`.
  - **Selection & Overlays**: `<mat-select>`, `<mat-option>`, `MatDialog`, `<mat-tooltip>`, `<mat-menu>`, `MatSnackBar`.
  - **Navigation & Layout**: `<mat-toolbar>`, `<mat-sidenav>`, `<mat-nav-list>`, `<mat-card>`, `<mat-slide-toggle>`.

### 3. Restrictive Component Fallback Policy
- Alternative third-party component libraries or custom component builds are permitted ONLY IF Angular Material lacks a native equivalent or specific required feature.
- When a fallback custom component is created, it MUST consume global CSS custom properties (`var(--mat-sys-*)`) to ensure 100% theme harmony across both light and dark modes.

### 4. Centralized SCSS Theme & Google Fonts Typography Architecture
- **Google Fonts Loading**: High-legibility Google Fonts (`Inter`, `Roboto`, `Outfit`, `Plus Jakarta Sans`) MUST be loaded globally in `index.html`.
- **Global Theme Tokens**: All colors, surface elevations, rounded corners, and font scales MUST originate from global CSS variables (`var(--bg-primary)`, `var(--bg-secondary)`, `var(--bg-card)`, `var(--text-primary)`, `var(--text-secondary)`, `var(--text-muted)`, `var(--border-color)`, `var(--color-primary)`).
- **Zero Hardcoding Rule**: Hardcoded hex colors (`#ffffff`, `#0f172a`) or static gradient stops inside component SCSS files are strictly prohibited. Header text gradients MUST fallback to `color: var(--text-primary)` to ensure high contrast in Light Mode.

### 5. High-Specificity MDC Shadow DOM Overrides
- Component cards, form fields, and dropdowns MUST include explicit MDC class overrides in global `src/styles.scss` to prevent Angular Material 3 default inline styles from breaking theme variables:
  ```scss
  mat-card,
  .mat-mdc-card {
    background-color: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border-color) !important;

    .mat-mdc-card-header,
    .mat-mdc-card-title,
    .mat-mdc-card-subtitle,
    .mat-mdc-card-content {
      color: var(--text-primary) !important;
    }
  }
  ```

### 6. Zero-FOUC (Flash of Unstyled Content) Synchronous Head Script
- `index.html` MUST include a 0ms synchronous inline script inside `<head>` to read `localStorage.getItem('theme')` at Frame 0 before initial paint, preventing dark/light flash on page reload:
  ```html
  <script>
    (function() {
      try {
        var theme = localStorage.getItem('app-theme-preference');
        var dark = theme === 'dark' || (!theme && window.matchMedia('(prefers-color-scheme: dark)').matches);
        document.documentElement.classList.toggle('dark-theme', dark);
        document.documentElement.classList.toggle('light-theme', !dark);
      } catch (e) {}
    })();
  </script>
  ```

## Examples

- **Correct Reactive Theme Service Implementation (OS Aware & Dark Default):**
```typescript
// src/app/core/services/theme.service.ts
import { Injectable, signal, effect, inject, DOCUMENT } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly document = inject(DOCUMENT);
  private readonly STORAGE_KEY = 'app-theme-preference';

  readonly isDarkMode = signal<boolean>(this.getInitialThemePreference());

  constructor() {
    effect(() => {
      const dark = this.isDarkMode();
      const root = this.document.documentElement;
      root.classList.toggle('dark-theme', dark);
      root.classList.toggle('light-theme', !dark);
      localStorage.setItem(this.STORAGE_KEY, dark ? 'dark' : 'light');
    });
  }

  toggleTheme(): void {
    this.isDarkMode.update(prev => !prev);
  }

  private getInitialThemePreference(): boolean {
    const saved = localStorage.getItem(this.STORAGE_KEY);
    if (saved) return saved === 'dark';

    if (typeof window !== 'undefined' && window.matchMedia) {
      if (window.matchMedia('(prefers-color-scheme: light)').matches) return false;
      if (window.matchMedia('(prefers-color-scheme: dark)').matches) return true;
    }

    return true; // Default to dark theme if no preference saved
  }
}
```

- **Correct Header Theme Toggle Component:**
```typescript
// src/app/shared/components/theme-toggle/theme-toggle.component.ts
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
            [matTooltip]="themeService.isDarkMode() ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
            (click)="themeService.toggleTheme()">
      <mat-icon>{{ themeService.isDarkMode() ? 'light_mode' : 'dark_mode' }}</mat-icon>
    </button>
  `
})
export class ThemeToggleComponent {
  readonly themeService = inject(ThemeService);
}
```

- **Incorrect Implementation (STRICTLY FORBIDDEN):**
```typescript
// ❌ ANTI-PATTERN: Light mode default, raw HTML controls, hardcoded hex, and no zero-FOUC script
import { Component, signal } from '@angular/core';

@Component({
  selector: 'app-bad-header',
  template: `
    <!-- FORBIDDEN: Raw HTML button and input instead of Angular Material controls -->
    <header>
      <input type="text" placeholder="Search..." />
      <button (click)="toggle()">Toggle Theme</button>
    </header>
  `,
  styles: [`
    /* FORBIDDEN: Hardcoded hex colors and static background styles */
    header {
      background-color: #0f172a;
      color: #ffffff;
      border: 1px solid #334155;
    }
  `]
})
export class BadHeaderComponent {
  // FORBIDDEN: Defaulting to Light Mode without OS preference detection
  isDark = signal<boolean>(false);

  toggle(): void {
    // FORBIDDEN: Mutates local flag without syncing root <html> class or localStorage
    this.isDark.update(v => !v);
  }
}
```

