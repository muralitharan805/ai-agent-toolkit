---
name: angular-material-styling
description: "Architecture, automated audit tools, and setup protocols for Angular Material UI. Enforces Dark Theme as default with OS detection fallback, Signal-based theme switching, zero-FOUC Frame 0 script, M3 design tokens, and Material-first component selection."
compatibility: "Requires Angular 19+ and Node.js 20+"
---

# Angular Material Styling Skill (`angular-material-styling`)

## Persona & Architectural Mandate
Act as a Principal Frontend and UI Architect specializing in Angular Material (v19+) design systems. Your mandate is to enforce Angular Material as the primary UI component library across all views, ensure **Dark Theme initializes as the default application state** (with automatic OS preference fallback), implement zero-FOUC (Flash of Unstyled Content) loading, wire Signal-based reactive theme toggling, and apply centralized SCSS Material 3 (M3) design tokens with high-legibility Google Fonts.

---

## 5-Pillar Directory Map

```text
frameworks/angular/skills/angular-material-styling/
├── SKILL.md                                        # Tier 2 Core Guidance & Setup Protocol (< 500 lines)
├── references/
│   ├── material-3-theming-and-tokens.md            # M3 define-theme, design tokens & MDC overrides
│   └── dark-mode-zero-fouc-architecture.md         # Frame 0 script, OS detection & Signal state
├── scripts/
│   └── audit_angular_material.py                   # Standalone CLI validation tool (PEP 723)
├── assets/
│   ├── theme.service.ts                            # Standalone Signal ThemeService
│   ├── theme-toggle.component.ts                   # Standalone accessible <app-theme-toggle>
│   ├── _theme-tokens.scss                          # Canonical M3 tokens & MDC overrides
│   └── zero-fouc-script.html                       # 0ms synchronous head script snippet
└── evals/
    ├── evals.json                                  # Empirical verification test suite
    └── grading.json                                # Quality benchmark scorecard (100%)
```

---

## Authoritative Reference Grounding & Bundled Assets
Consult the specialized guides and assets bundled directly inside this skill:
- **M3 Theming & MDC Overrides Guide**: [references/material-3-theming-and-tokens.md](references/material-3-theming-and-tokens.md)
- **Dark Mode & Zero-FOUC Guide**: [references/dark-mode-zero-fouc-architecture.md](references/dark-mode-zero-fouc-architecture.md)
- **Reactive Theme Service Asset**: [assets/theme.service.ts](assets/theme.service.ts)
- **Header Theme Toggle Asset**: [assets/theme-toggle.component.ts](assets/theme-toggle.component.ts)
- **Theme Tokens & MDC Overrides Asset**: [assets/_theme-tokens.scss](assets/_theme-tokens.scss)
- **Zero-FOUC Head Script Asset**: [assets/zero-fouc-script.html](assets/zero-fouc-script.html)
- **Automated Material Audit CLI Tool**: `python3 scripts/audit_angular_material.py <path>`
- **Empirical Test Suite**: [evals/evals.json](evals/evals.json)

---

## 1. Material-First Component Selection Matrix

| Standard UI Element | Restricted Raw Element | Mandatory Angular Material Component |
| :--- | :--- | :--- |
| **Data Grid / Table** | `<table>` | `<table mat-table>`, `<mat-paginator>`, `matSort` |
| **Buttons & Actions** | `<button>` | `mat-button`, `mat-flat-button`, `mat-icon-button` |
| **Form Inputs** | `<input>`, `<textarea>` | `<mat-form-field>`, `<input matInput>` |
| **Dropdowns & Select** | `<select>` | `<mat-select>`, `<mat-option>`, `<mat-autocomplete>` |
| **Dialogs & Modals** | `<dialog>`, custom modal | `MatDialog` service, `<mat-dialog-content>` |
| **Layout Shell & Header** | `<header>`, `<div>` | `<mat-toolbar>`, `<mat-sidenav-container>`, `<mat-card>` |
| **Selection Controls** | `<input type="checkbox">` | `<mat-checkbox>`, `<mat-slide-toggle>` |
| **Feedback & Badges** | custom tooltip / banner | `MatSnackBar`, `<mat-tooltip>`, `<mat-progress-bar>` |

---

## 2. Step-by-Step Setup Protocol

### Step 1: Install Dependencies
```bash
pnpm add @angular/material @angular/cdk
```

### Step 2: Configure `src/index.html` (Google Fonts & Zero-FOUC Script)
Embed Google Fonts (`Inter`, `Outfit`), Material Icons, and the synchronous Frame 0 script from [assets/zero-fouc-script.html](assets/zero-fouc-script.html):

```html
<head>
  <!-- Google Fonts & Material Icons -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@500;600;700;800&display=swap" rel="stylesheet">
  <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">

  <!-- Zero-FOUC Frame 0 Script (Eliminates White Flash on Reload) -->
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
</head>
```

### Step 3: Deploy Theme Tokens & MDC Overrides
Import [assets/_theme-tokens.scss](assets/_theme-tokens.scss) into `src/styles.scss`:

```scss
@import './styles/theme-tokens';
```

### Step 4: Deploy Reactive `ThemeService`
Deploy [assets/theme.service.ts](assets/theme.service.ts) into `src/app/core/services/theme.service.ts`:
```typescript
import { Injectable, signal, effect, inject, DOCUMENT } from '@angular/core';

@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly document = inject(DOCUMENT);
  private static readonly STORAGE_KEY = 'app-theme-preference';

  readonly isDarkMode = signal<boolean>(this.getInitialThemePreference());

  constructor() {
    effect(() => {
      const dark = this.isDarkMode();
      const root = this.document.documentElement;
      root.classList.toggle('dark-theme', dark);
      root.classList.toggle('light-theme', !dark);
      try {
        localStorage.setItem(ThemeService.STORAGE_KEY, dark ? 'dark' : 'light');
      } catch {}
    });
  }

  toggleTheme(): void {
    this.isDarkMode.update(prev => !prev);
  }

  private getInitialThemePreference(): boolean {
    try {
      const saved = localStorage.getItem(ThemeService.STORAGE_KEY);
      if (saved) return saved === 'dark';
    } catch {}

    if (typeof window !== 'undefined' && window.matchMedia) {
      if (window.matchMedia('(prefers-color-scheme: light)').matches) return false;
      if (window.matchMedia('(prefers-color-scheme: dark)').matches) return true;
    }

    return true; // Default to Dark Theme
  }
}
```

### Step 5: Deploy Header Theme Toggle Component
Deploy [assets/theme-toggle.component.ts](assets/theme-toggle.component.ts) into header shells:

```typescript
@Component({
  selector: 'app-theme-toggle',
  standalone: true,
  imports: [MatButtonModule, MatIconModule, MatTooltipModule],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <button mat-icon-button
            [matTooltip]="themeService.isDarkMode() ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
            [attr.aria-label]="themeService.isDarkMode() ? 'Switch to Light Mode' : 'Switch to Dark Mode'"
            (click)="themeService.toggleTheme()">
      <mat-icon>{{ themeService.isDarkMode() ? 'light_mode' : 'dark_mode' }}</mat-icon>
    </button>
  `
})
export class ThemeToggleComponent {
  readonly themeService = inject(ThemeService);
}
```

### Step 6: Verify Theme Persistence & AAA Contrast
Run `pnpm start` and verify:
1. Root `<html>` element initializes with `.dark-theme`.
2. Clicking toggle swaps `.dark-theme` and `.light-theme`.
3. Page reload maintains dark mode without white screen flicker.

---

## 3. Automated Material & Theme Audit Tool
Scan an entire Angular workspace or feature directory for raw HTML controls, hardcoded hex colors, and missing zero-FOUC scripts:

```bash
# Standard console audit:
python3 frameworks/angular/skills/angular-material-styling/scripts/audit_angular_material.py src/app

# Machine-readable JSON output:
python3 frameworks/angular/skills/angular-material-styling/scripts/audit_angular_material.py src/app --json

# Strict enforcement for CI pipelines:
python3 frameworks/angular/skills/angular-material-styling/scripts/audit_angular_material.py src/app --strict
```

---

## Gotchas & Anti-Patterns

| Anti-Pattern | Root Cause & Failure Mode | Modern Recommended Replacement |
| :--- | :--- | :--- |
| **Light Theme Default Trap** | `signal(false)` forces bright UI by default, causing user eye strain in low-light environments. | **Default `isDarkMode = signal(true)`** with OS preference evaluation. |
| **FOUC White Flash on Reload** | Theme initialization deferred to Angular lifecycle renders white body before JS execution. | **0ms synchronous `<head>` script** setting `dark-theme` at Frame 0. |
| **Hardcoded Hex Colors in SCSS** | `#1e293b` breaks color contrast when users toggle from Dark to Light theme. | **CSS Custom Properties** (`var(--bg-card)`, `var(--text-primary)`). |
| **MDC Override Specificity Loss** | Angular Material 3 default inline styles override custom variables if specificity is too low. | **Explicit `.mat-mdc-*` class targeting** in global `styles.scss` with `!important`. |
| **Raw `<button>` and `<input>`** | Inconsistent hover states, missing ripple effects, and broken theme token integration. | **`mat-button`, `mat-icon-button`, `<input matInput>`**. |
| **Missing Toggle `aria-label`** | Screen readers cannot identify icon-only button purpose, failing WCAG accessibility audits. | **`[attr.aria-label]="..."`** providing accessible name. |
