---
name: angular-material-styling
description: "Guidelines and architecture for prioritizing Angular Material UI components (Tables, Inputs, Dropdowns, Buttons), default Dark Theme initialization with Signal-based toggle, centralizing Google Fonts SCSS typography, and applying M3 design tokens across Angular applications."
---
# Goal
Enforce Angular Material (`@angular/material`) as the mandatory primary UI component library for all standard user interface controls, initialize **Dark Theme as default** with a Signal-based theme switcher, integrate Google Fonts SCSS typography (`Inter`, `Roboto`, `Outfit`), and implement strict fallback guidelines.

# Instructions

1. **Dark Theme Default & Reactive Switching**:
   - Initialize the application in **Dark Mode by default** (`isDarkMode = signal<boolean>(true)`).
   - Implement a singleton `ThemeService` using Angular Signals to toggle themes, save user preferences in `localStorage`, and update the root `<html>` element class (`.dark-theme` / `.light-theme`).
   - Include a user theme toggle component (`<app-theme-toggle>`) in the header shell or main toolbar.

2. **Material First Component Selection**:
   Always use standard Angular Material standalone modules for core UI controls:
   - **Tables**: `MatTableModule`, `MatPaginatorModule`, `MatSortModule`
   - **Buttons & Icons**: `MatButtonModule`, `MatIconButton`, `MatIconModule`
   - **Inputs & Form Fields**: `MatFormFieldModule`, `MatInputModule`
   - **Dropdowns & Selects**: `MatSelectModule`, `MatOptionModule`, `MatAutocompleteModule`
   - **Dialogs & Overlays**: `MatDialogModule`, `MatSnackBarModule`, `MatMenuModule`, `MatTooltipModule`
   - **Containers & Layout**: `MatCardModule`, `MatToolbarModule`, `MatSidenavModule`

3. **Google Fonts & Typography System**:
   - Embed modern Google Fonts (`Inter`, `Outfit`, `Roboto`) in `index.html`.
   - Define a central `src/styles/_typography.scss` configuring the `typography` field in Angular Material 3 (`mat.define-theme`).
   - Set font CSS custom properties `--app-font-heading: 'Outfit', sans-serif;` and `--app-font-body: 'Inter', sans-serif;`.

4. **SCSS Theme & M3 Design Tokens**:
   - Configure global SCSS styles (`src/styles.scss`) to load the Dark Theme by default on the root `html` or `html.dark-theme` selector.
   - Use Angular Material 3 CSS tokens (`var(--mat-sys-primary)`, `var(--mat-sys-surface-container)`, `var(--mat-sys-on-surface)`).

5. **Component Fallback Guidelines**:
   - Fallback to third-party libraries or custom controls ONLY if Angular Material lacks the required component.
   - Custom fallback components MUST consume global M3 theme variables (`var(--mat-sys-*)`) to maintain dark/light mode compatibility.

# Examples

## 1. Reactive Theme Service (Dark Default)
```typescript
// src/app/core/services/theme.service.ts
import { Injectable, signal, effect, inject, DOCUMENT } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly document = inject(DOCUMENT);
  private readonly STORAGE_KEY = 'nidhiflow-theme-mode';

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
    return true; // Default to Dark Mode if no stored preference
  }
}
```

## 2. Header Theme Toggle Component
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
            [matTooltip]="themeService.isDarkMode() ? 'Switch to Light Theme' : 'Switch to Dark Theme'"
            (click)="themeService.toggleTheme()"
            aria-label="Toggle Theme">
      <mat-icon>{{ themeService.isDarkMode() ? 'light_mode' : 'dark_mode' }}</mat-icon>
    </button>
  `
})
export class ThemeToggleComponent {
  readonly themeService = inject(ThemeService);
}
```

## 3. Global SCSS Theme Setup (Dark Default)
```scss
// src/styles.scss
@use './styles/theme' as app-theme;
@use '@angular/material' as mat;

// Default root styling initializes with Dark Theme
html, html.dark-theme {
  @include mat.all-component-themes(app-theme.$dark-theme);
  color-scheme: dark;
  font-family: var(--app-font-body, 'Inter', sans-serif);
}

html.light-theme {
  @include mat.all-component-colors(app-theme.$light-theme);
  color-scheme: light;
}

body {
  margin: 0;
  background-color: var(--mat-sys-background);
  color: var(--mat-sys-on-background);
  min-height: 100vh;
}
```

# Constraints
- Do NOT make Light Theme the default setting; applications MUST default to Dark Theme.
- Do NOT use standard HTML `<input>`, `<select>`, `<button>`, or `<table>` when corresponding Angular Material components exist.
- Do NOT hardcode arbitrary static font-family strings (`font-family: Arial`) or CSS hex colors (`#ffffff`, `#000000`).
