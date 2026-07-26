---
trigger: always_on
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
  - **Tables & Data Grids**: `<table mat-table>`, `<mat-paginator>`, `matSort`.
  - **Buttons & Actions**: `mat-button`, `mat-flat-button`, `mat-stroked-button`, `mat-icon-button`, `mat-fab`.
  - **Form Fields & Inputs**: `<mat-form-field>`, `<input matInput>`, `<textarea matInput>`.
  - **Dropdowns & Selection**: `<mat-select>`, `<mat-option>`, `<mat-autocomplete>`.
  - **Dialogs & Modals**: `MatDialog` service and `<mat-dialog-content>`.
  - **Navigation & Layout**: `<mat-toolbar>`, `<mat-sidenav>`, `<mat-nav-list>`, `<mat-card>`.
  - **Selection Controls**: `<mat-checkbox>`, `<mat-radio-button>`, `<mat-slide-toggle>`.
  - **Feedback & Overlays**: `<mat-tooltip>`, `<mat-menu>`, `MatSnackBar`, `<mat-progress-bar>`, `<mat-spinner>`.

### 3. Restrictive Component Fallback Policy
- Alternative third-party component libraries or custom component builds are permitted ONLY IF Angular Material lacks a native equivalent or specific required feature.
- When a fallback custom component is created, it MUST consume global CSS custom properties (`var(--mat-sys-*)`) to ensure 100% theme harmony across both light and dark modes.

### 4. Centralized SCSS Theme & Google Fonts Typography Architecture
- **Google Fonts Loading**: High-legibility Google Fonts (`Inter`, `Roboto`, `Outfit`, `Plus Jakarta Sans`) MUST be loaded globally in `index.html`.
- **Global Theme Tokens**: All colors, surface elevations, rounded corners, and font scales MUST originate from `src/styles/_theme.scss` and `src/styles/_typography.scss`.
- **Material 3 Token Consumption**: Components MUST use M3 tokens (e.g., `var(--mat-sys-primary)`, `var(--mat-sys-surface-container)`) instead of hardcoded hex values (`#1976d2`).

## Examples

- **Correct Reactive Theme Service Implementation (OS Aware & Dark Default):**
```typescript
// src/app/core/services/theme.service.ts
import { Injectable, signal, effect, inject, DOCUMENT } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly document = inject(DOCUMENT);
  private readonly STORAGE_KEY = 'app-theme-preference';

  // Default initial state is OS preference aware, defaulting to Dark Theme (true)
  readonly isDarkMode = signal<boolean>(this.getInitialThemePreference());

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
