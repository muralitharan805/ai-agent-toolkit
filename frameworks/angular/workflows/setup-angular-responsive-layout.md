---
description: "Sequential workflow to configure Angular CDK BreakpointObserver, scaffold Signal-driven ScreenService, set up responsive Angular Material mat-sidenav shell, and implement responsive data views. Triggered by 'responsive:', 'setup-responsive:', or '/setup-angular-responsive-layout'."
trigger: manual
---

# Setup Angular Material Responsive Layout Workflow

This workflow guides the developer and AI agent through setting up an ultra-responsive Angular application utilizing **Angular Material (`@angular/material`)** components, Angular CDK `BreakpointObserver`, and a Signal-driven `ScreenService`.

---

## Step 1: Install Angular CDK & Material Packages

Ensure `@angular/material` and `@angular/cdk` are installed in the workspace:
```bash
pnpm add @angular/material @angular/cdk
```

---

## Step 2: Scaffold Signal-Driven `ScreenService`

1. Create `src/app/core/services/screen.service.ts`.
2. Inject `BreakpointObserver` from `@angular/cdk/layout`.
3. Create reactive signals (`isMobile`, `isTablet`, `isDesktop`, `gridCols`).
4. Subscribe to `Breakpoints.Handset`, `Breakpoints.Tablet`, and `Breakpoints.Web` within browser platform check (`isPlatformBrowser`).

---

## Step 3: Implement Angular Material Responsive Shell

1. Update main layout component (`src/app/app.component.html`):
   - Wrap layout in `<mat-sidenav-container>`.
   - Bind `<mat-sidenav [mode]="screen.isMobile() ? 'over' : 'side'" [opened]="screen.isDesktop()">`.
   - Add `<mat-toolbar color="primary">` with conditional mobile menu button (`@if (screen.isMobile())`).
   - Add optional mobile bottom navigation bar for small screens.

---

## Step 4: Configure Safe Area & Touch SCSS Mixins

1. Add mobile safe area insets to `src/styles.scss`:
   ```scss
   .main-content {
     padding-top: env(safe-area-inset-top, 0px);
     padding-bottom: env(safe-area-inset-bottom, 0px);
   }

   button, a.mat-mdc-button-base {
     min-height: 44px;
     min-width: 44px;
   }
   ```

---

## Step 5: Verify Responsive Behavior

1. Run local dev server (`pnpm run dev`).
2. Open Chrome DevTools Device Mode (toggle between iPhone 14, iPad, and 1080p Desktop).
3. Confirm Sidenav switches between overlay (`mode="over"`) and side (`mode="side"`).
4. Confirm zero horizontal scrollbars on mobile viewports ($375\text{px}$).
