---
name: angular-mobile-responsive
description: Best practices, architecture, Angular CDK BreakpointObserver Signal service (ScreenService), Angular Material responsive component utilization (mat-sidenav, mat-grid-list, mat-table to mat-card transformation, mat-bottom-sheet), container queries, and touch ergonomics for Angular applications.
---

# Angular Material Responsive Layout & Mobile Ergonomics Skill

## Goal
Guide developers and AI coding agents in designing ultra-responsive, mobile-first Angular applications by prioritizing **Angular Material (`@angular/material`)** components, Angular CDK Layout (`BreakpointObserver`), Signal-driven viewport state management, dynamic layout control flow, and touch ergonomics.

---

## Core Responsive Architecture & Breakpoints

### 1. Standard Breakpoint Specifications
Angular CDK provides standard breakpoint queries (`@angular/cdk/layout`). Map them to standard viewport sizes:

| Breakpoint Name | Query / Range | Primary Target Devices |
| :--- | :--- | :--- |
| `Handset` (Mobile) | `max-width: 599.98px` | Smartphones (Portrait / Small Screen) |
| `Tablet` | `600px - 950.98px` | Tablets & Large Foldables |
| `Web` (Desktop) | `>= 960px` | Laptops, Desktops, & Ultra-wide Displays |

---

## Angular CDK Signal-Driven Responsive Service (`ScreenService`)

Encapsulate `@angular/cdk/layout` `BreakpointObserver` inside a global, singleton Angular service utilizing Signals (`signal()`, `computed()`):

```typescript
// src/app/core/services/screen.service.ts
import { Injectable, inject, signal, computed, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';

@Injectable({ providedIn: 'root' })
export class ScreenService {
  private readonly breakpointObserver = inject(BreakpointObserver);
  private readonly platformId = inject(PLATFORM_ID);

  // Reactive Viewport Signals
  readonly isMobile = signal<boolean>(false);
  readonly isTablet = signal<boolean>(false);
  readonly isDesktop = signal<boolean>(true);

  // Dynamic Grid Column Count (e.g. for mat-grid-list)
  readonly gridCols = computed(() => {
    if (this.isMobile()) return 1;
    if (this.isTablet()) return 2;
    return 4;
  });

  constructor() {
    if (isPlatformBrowser(this.platformId)) {
      this.breakpointObserver
        .observe([Breakpoints.Handset, Breakpoints.Tablet, Breakpoints.Web])
        .subscribe((result) => {
          const isHandset = result.breakpoints[Breakpoints.Handset] ?? false;
          const isTab = result.breakpoints[Breakpoints.Tablet] ?? false;

          this.isMobile.set(isHandset);
          this.isTablet.set(isTab);
          this.isDesktop.set(!isHandset && !isTab);
        });
    }
  }
}
```

---

## Angular Material Responsive Component Utilization Patterns

Maximize the use of built-in Angular Material components to handle responsive transformations seamlessly:

### 1. Responsive Navigation Shell (`<mat-sidenav-container>`)
Utilize Angular Material Sidenav for layout navigation, dynamically switching `mode` based on screen signals:

```html
<mat-sidenav-container class="app-sidenav-container">
  <!-- Sidenav: Mobile = "over" (overlay), Desktop = "side" (persistent) -->
  <mat-sidenav 
    #sidenav 
    [mode]="screen.isMobile() ? 'over' : 'side'" 
    [opened]="screen.isDesktop()"
    class="app-sidenav">
    <mat-nav-list>
      <a mat-list-item routerLink="/dashboard">
        <mat-icon matListItemIcon>dashboard</mat-icon>
        <span matListItemTitle>Dashboard</span>
      </a>
    </mat-nav-list>
  </mat-sidenav>

  <mat-sidenav-content>
    <mat-toolbar color="primary">
      @if (screen.isMobile()) {
        <button mat-icon-button (click)="sidenav.toggle()" aria-label="Toggle navigation">
          <mat-icon>menu</mat-icon>
        </button>
      }
      <span>App Title</span>
    </mat-toolbar>

    <main class="main-content">
      <router-outlet></router-outlet>
    </main>

    <!-- Mobile Bottom Navigation Bar (Shown on Mobile Viewports Only) -->
    @if (screen.isMobile()) {
      <nav class="mobile-bottom-nav">
        <a routerLink="/dashboard" routerLinkActive="active">
          <mat-icon>dashboard</mat-icon>
          <span>Home</span>
        </a>
      </nav>
    }
  </mat-sidenav-content>
</mat-sidenav-container>
```

---

### 2. Responsive Data Views (`mat-table` ➔ `mat-card` / `mat-accordion`)
For data listings, render full `<table mat-table>` on desktop and transform to stacked `<mat-card>` or `<mat-accordion>` on mobile:

```html
@if (screen.isMobile()) {
  <!-- Mobile: Stacked Material Cards View -->
  <div class="mobile-card-list">
    @for (item of dataList(); track item.id) {
      <mat-card class="mobile-item-card">
        <mat-card-header>
          <mat-card-title>{{ item.name }}</mat-card-title>
          <mat-card-subtitle>{{ item.category }}</mat-card-subtitle>
        </mat-card-header>
        <mat-card-content>
          <p><strong>Amount:</strong> {{ item.amount | currency }}</p>
        </mat-card-content>
      </mat-card>
    }
  </div>
} @else {
  <!-- Desktop: Full Angular Material Data Table -->
  <table mat-table [dataSource]="dataList()" class="mat-elevation-z2">
    <ng-container matColumnDef="name">
      <th mat-header-cell *matHeaderCellDef> Name </th>
      <td mat-cell *matCellDef="let element"> {{ element.name }} </td>
    </ng-container>
    <!-- Column Definitions -->
    <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
    <tr mat-row *matRowDef="let row; columns: displayedColumns;"></tr>
  </table>
}
```

---

### 3. Responsive Overlays (`mat-bottom-sheet` vs `mat-dialog`)
- **Mobile (`isMobile() = true`)**: Open `<mat-bottom-sheet>` for action menus, context options, or filter panels for optimal thumb-reach ergonomics.
- **Desktop (`isDesktop() = true`)**: Open standard `<mat-dialog>` or `<mat-menu>`.

---

## Touch Ergonomics & Safe Area SCSS Mixins

Ensure minimum $44 \times 44\text{px}$ touch targets and handle modern mobile notch / gesture bar insets:

```scss
// src/styles/_responsive.scss
@mixin mobile-safe-areas {
  padding-top: env(safe-area-inset-top, 0px);
  padding-bottom: env(safe-area-inset-bottom, 0px);
  padding-left: env(safe-area-inset-left, 0px);
  padding-right: env(safe-area-inset-right, 0px);
}

// Minimum Touch Target Constraint
button, a.mat-mdc-button-base {
  min-height: 44px;
  min-width: 44px;
}
```
