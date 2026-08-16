---
trigger: always_on
---

# Angular Material UI Rules

When working with Angular Material or `@angular/cdk`, you MUST strictly adhere to the following rules:

## 1. Material 3 (M3) Theming Standards
- **No Legacy Theming:** NEVER use legacy Material 2 theming APIs like `mat-light-theme`, `mat-dark-theme`, or `mat-palette`.
- **Use Material 3 (M3):** Declare all themes using the modern M3 system (`mat.define-theme`) and access colors, typography, and density via CSS custom properties or Sass mixins.
- **Theming Customizations:** Use custom theme configurations through Sass mixins in global styles (e.g., `styles.scss`).

## 2. Standalone Component Imports
- **No Global/Shared Material Modules:** Do NOT create a single massive `MaterialModule` that imports and exports all Material components.
- **Direct Imports:** Import only the specific Angular Material modules required (e.g., `MatButtonModule`, `MatCardModule`, `MatDialogModule`) directly in the `imports` array of the standalone component where they are used.

## 3. Form Validation & Control
- **Reactive Forms:** Always use Angular Reactive Forms (`formControl`, `formGroup`, `FormBuilder`) with `mat-form-field` and Material inputs.
- **No Template-driven Forms:** Do NOT use `ngModel` or template-driven forms unless explicitly requested by the user.

## 4. Accessibility (a11y) & UX
- **ARIA Attributes:** Ensure all interactive Material elements (especially icon-only buttons, custom inputs, dialog headers) have proper `aria-label`, `aria-describedby`, or `aria-labelledby` attributes.
- **Focus Management:** Utilize CDK utilities (like `cdkTrapFocus`) for custom modals and overlays to maintain accessibility conformance.
- **Error Messages:** Always use `mat-error` inside `mat-form-field` for validation feedback.

## 5. Styling & Overrides
- **No Ad-Hoc or Inline CSS Overrides:** Never use inline CSS attributes (`style="font-size: 18px;"`) or plain CSS class overrides (e.g., overriding `.mat-mdc-button` directly with custom fonts or colors) to style Material components.
- **Declare at Theme Level:** Any changes to typography (font-size, font-weight, family) or color palettes MUST be declared at the Angular Material theme level using Sass mixins/design tokens (`mat.define-theme`, custom typography configs, CSS custom variables) or custom theme mapping.
- **Scoped styling / CSS variables:** If local tweaks are absolutely necessary, prefer styling using M3 CSS custom properties (design tokens) or scoped component-level classes rather than overriding internal Material DOM classes globally.
