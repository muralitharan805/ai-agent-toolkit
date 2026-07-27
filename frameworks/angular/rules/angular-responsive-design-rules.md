---
trigger: always_on
description: "Mandates Angular Material component utilization (mat-sidenav, mat-card, mat-bottom-sheet) for responsive layouts, minimum 44px touch targets, mobile safe area insets, and Signal-driven control flow rendering."
---

# Angular Material Responsive Layout Rules

## Description
Enforces mandatory Angular Material component utilization for responsive layout transformations, minimum touch target ergonomics ($44 \times 44\text{px}$), mobile safe area inset handling, and Signal-based dynamic template control flow across all Angular applications.

## Constraints

### 1. Mandatory Angular Material Component Utilization for Responsiveness
- **Navigation Shell**: Layout navigation MUST utilize `<mat-sidenav-container>` and `<mat-sidenav>`.
  - Mobile: `mode="over"` (overlay with backdrop).
  - Desktop: `mode="side"` (persistent sidebar).
- **Responsive Overlays**: Mobile action menus and contextual options MUST prefer `<mat-bottom-sheet>` over small desktop dropdowns for thumb ergonomics.
- **Responsive Lists**: Large data tables MUST transform from `<table mat-table>` on desktop to stacked `<mat-card>` or `<mat-accordion>` views on mobile screen sizes (`< 600px`).

### 2. Minimum Touch Target Rule ($44 \times 44\text{px}$)
- Interactive elements (buttons, icons, menu triggers, list items) MUST satisfy a minimum touch target area of $44 \times 44\text{px}$ on touch devices.
- Tiny icon buttons without padding or touch target area are STRICTLY FORBIDDEN on mobile viewports.

### 3. Mobile Safe Area Inset Handling
- Headers, fixed action bars, and bottom navigation bars MUST include CSS `env(safe-area-inset-top)` and `env(safe-area-inset-bottom)` to accommodate mobile notches and device gesture bars.

### 4. Dynamic Control Flow Rendering
- Template switching between mobile-optimized layouts and desktop layouts MUST use native Angular control flow blocks (`@if (screen.isMobile()) { ... } @else { ... }`) to prevent rendering heavy, unseen desktop DOM elements on mobile viewports.
