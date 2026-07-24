---
name: angular-material-styling
description: "Guidelines and architecture for prioritizing Angular Material UI components (Tables, Inputs, Dropdowns, Buttons), centralizing Google Fonts SCSS typography, and applying M3 design tokens across Angular applications."
---
# Goal
Enforce Angular Material (`@angular/material`) as the mandatory primary UI component library for all standard user interface controls (Tables, Buttons, Inputs, Dropdowns, Dialogs, Cards), integrate Google Fonts SCSS typography (`Inter`, `Roboto`, `Outfit`), and implement strict fallback guidelines when custom components are required.

# Instructions

1. **Material First Component Selection**:
   Always use standard Angular Material standalone modules for core UI controls:
   - **Tables**: `MatTableModule`, `MatPaginatorModule`, `MatSortModule`
   - **Buttons & Icons**: `MatButtonModule`, `MatIconButton`, `MatIconModule`
   - **Inputs & Form Fields**: `MatFormFieldModule`, `MatInputModule`
   - **Dropdowns & Selects**: `MatSelectModule`, `MatOptionModule`, `MatAutocompleteModule`
   - **Dialogs & Overlays**: `MatDialogModule`, `MatSnackBarModule`, `MatMenuModule`, `MatTooltipModule`
   - **Containers & Layout**: `MatCardModule`, `MatToolbarModule`, `MatSidenavModule`

2. **Google Fonts & Typography System**:
   - Embed modern Google Fonts (e.g., `<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Outfit:wght@500;600;700&display=swap" rel="stylesheet">`) in `index.html`.
   - Define a central `src/styles/_typography.scss` configuring the `typography` field in Angular Material 3 (`mat.define-theme`).
   - Use Google Fonts variables `--app-font-heading: 'Outfit', sans-serif;` and `--app-font-body: 'Inter', sans-serif;` globally.

3. **SCSS Theme & M3 Design Tokens**:
   - Inherit all component surface colors, borders, and typography from Angular Material 3 CSS tokens (`var(--mat-sys-primary)`, `var(--mat-sys-surface-container)`, `var(--mat-sys-on-surface)`).
   - Define all custom palettes and light/dark theme modes in `src/styles/_theme.scss`.

4. **Component Fallback Guidelines**:
   - Fallback to third-party libraries or custom HTML/SCSS controls ONLY if Angular Material does NOT provide the required component (e.g., complex chart, rich text editor, multi-select tree table).
   - Custom fallback components MUST consume global M3 theme variables (`var(--mat-sys-*)`) to ensure exact visual alignment.

# Examples

## Standalone Angular Component using Material UI
```typescript
import { Component, ChangeDetectionStrategy, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormControl, ReactiveFormsModule } from '@angular/forms';
import { MatTableModule } from '@angular/material/table';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatCardModule } from '@angular/material/card';

interface Product {
  id: string;
  name: string;
  category: string;
  price: number;
}

@Component({
  selector: 'app-product-management',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatTableModule,
    MatPaginatorModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatIconModule,
    MatCardModule
  ],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <mat-card class="management-card">
      <mat-card-header>
        <mat-card-title>Product Catalog</mat-card-title>
        <mat-card-subtitle>Manage store inventory and pricing</mat-card-subtitle>
      </mat-card-header>

      <mat-card-content class="card-body">
        <div class="filter-bar">
          <mat-form-field appearance="outline" class="search-input">
            <mat-label>Search Product</mat-label>
            <input matInput [formControl]="searchControl" placeholder="Type product name...">
            <mat-icon matSuffix>search</mat-icon>
          </mat-form-field>

          <mat-form-field appearance="outline" class="category-select">
            <mat-label>Category</mat-label>
            <mat-select [formControl]="categoryControl">
              <mat-option value="all">All Categories</mat-option>
              <mat-option value="electronics">Electronics</mat-option>
              <mat-option value="apparel">Apparel</mat-option>
            </mat-select>
          </mat-form-field>

          <button mat-flat-button color="primary" class="add-btn">
            <mat-icon>add</mat-icon> Add Product
          </button>
        </div>

        <table mat-table [dataSource]="products()" class="product-table mat-elevation-z1">
          <ng-container matColumnDef="name">
            <th mat-header-cell *matHeaderCellDef> Product Name </th>
            <td mat-cell *matCellDef="let item"> {{ item.name }} </td>
          </ng-container>

          <ng-container matColumnDef="category">
            <th mat-header-cell *matHeaderCellDef> Category </th>
            <td mat-cell *matCellDef="let item"> {{ item.category }} </td>
          </ng-container>

          <ng-container matColumnDef="price">
            <th mat-header-cell *matHeaderCellDef> Price </th>
            <td mat-cell *matCellDef="let item"> {{ item.price | currency }} </td>
          </ng-container>

          <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
          <tr mat-row *matRowDef="let row; columns: displayedColumns;"></tr>
        </table>
      </mat-card-content>
    </mat-card>
  `,
  styleUrl: './product-management.component.scss'
})
export class ProductManagementComponent {
  readonly searchControl = new FormControl('');
  readonly categoryControl = new FormControl('all');
  readonly displayedColumns = ['name', 'category', 'price'];

  readonly products = signal<Product[]>([
    { id: '1', name: 'Wireless Headphones', category: 'electronics', price: 149.99 },
    { id: '2', name: 'Ergonomic Chair', category: 'apparel', price: 299.00 }
  ]);
}
```

## SCSS Typography & Token Styling
```scss
// product-management.component.scss
.management-card {
  background-color: var(--mat-sys-surface-container);
  border-radius: var(--mat-sys-corner-large, 16px);
  padding: 1rem;

  mat-card-title {
    font-family: var(--app-font-heading, 'Outfit', sans-serif);
    color: var(--mat-sys-primary);
  }

  .filter-bar {
    display: flex;
    gap: 1rem;
    align-items: center;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;

    .search-input {
      flex: 1;
      min-width: 240px;
    }
  }

  .product-table {
    width: 100%;
    background-color: var(--mat-sys-surface);
    color: var(--mat-sys-on-surface);
    font-family: var(--app-font-body, 'Inter', sans-serif);
  }
}
```

# Constraints
- Do NOT use standard HTML `<input>`, `<select>`, `<button>`, or `<table>` when corresponding Angular Material components exist.
- Do NOT hardcode arbitrary static font-family strings (`font-family: Arial`) or CSS hex colors (`#ffffff`, `#000000`).
- Do NOT use `::ng-deep` without explicit scoping inside host containers and using Material CSS tokens.
