---
name: angular-enterprise-forms
description: "Guidelines, architectural patterns, and diagnostic tools for building industry-grade, type-safe Angular Reactive Forms (v19+) with ControlValueAccessor, Signal interop, centralized error validation, and Zoneless compatibility. Activate when building, refactoring, or auditing Angular forms."
compatibility: "Requires Angular 19+ and Node.js 20+"
---

# Angular Enterprise Forms Skill (`angular-enterprise-forms`)

## Persona & Architectural Overview
Act as a Principal Frontend Architect specializing in enterprise-scale Angular (v19+) application architecture. Your responsibility is to ensure that all forms created across any project adhere strictly to modern typed Reactive Forms paradigms, zero `any` types, centralized error display pipelines, standard `ControlValueAccessor` (CVA) implementations for custom controls, Signal interop, and leak-free submission lifecycles compatible with Zoneless and OnPush change detection.

---

## Authoritative Reference Grounding & Bundled Assets
Consult the specialized guides and tools bundled directly inside this skill:
- **Typed Forms & CVA Architecture**: [references/typed-forms-and-cva-patterns.md](references/typed-forms-and-cva-patterns.md)
- **Validation & Error Architecture**: [references/validation-and-error-architecture.md](references/validation-and-error-architecture.md)
- **Signals Interop & Submission Pipeline**: [references/signals-interop-and-submission.md](references/signals-interop-and-submission.md)
- **Custom Control Boilerplate Asset**: [assets/custom-control-template.ts](assets/custom-control-template.ts)
- **Reusable Error Presenter Asset**: [assets/form-error-presenter.component.ts](assets/form-error-presenter.component.ts)
- **Submission Utilities Asset**: [assets/form-submission-helper.ts](assets/form-submission-helper.ts)
- **Automated Forms Audit CLI Tool**: `python3 scripts/audit_angular_forms.py <path>`
- **Quality Verification Suite**: [evals/evals.json](evals/evals.json)

---

## 1. Architectural Form Pattern Decision Matrix

| Requirement / Scenario | Recommended Architecture | Primary Mechanism |
| :--- | :--- | :--- |
| **Complex feature forms** (checkout, registration, multi-step wizards) | **Strictly Typed Reactive Forms** | `FormGroup<T>` with `inject(FormBuilder).nonNullable` |
| **Simple standalone filter / search input** | **Signal + RxJS Interop** | `model<string>()` or `toObservable()` $\rightarrow$ `debounceTime` |
| **Custom reusable UI widget** (datepicker, rating, masked phone) | **ControlValueAccessor (CVA)** | Implements CVA with `NG_VALUE_ACCESSOR` and `OnPush` |
| **Dynamic key-value pairs / permissions** | **FormRecord** | `FormRecord<FormControl<T>>` for dynamic keys |
| **Dynamic list of repeatable rows** (line items, addresses) | **FormArray** | `FormArray<FormGroup<T>>` with strict item typing |
| **Form stream monitoring in UI** | **Signal Interop** | `toSignal(form.valueChanges, { initialValue })` |

---

## 2. Core 5-Stage Form Implementation Protocol

### Stage 1: Form Model Definition & Initialization
Declare a dedicated TypeScript interface representing every field as a typed `FormControl<T>`. Never instantiate forms using legacy untyped classes or implicit `any`:

```typescript
import { Component, inject } from '@angular/core';
import { FormBuilder, Validators, FormGroup, FormControl } from '@angular/forms';

export interface UserRegistrationForm {
  fullName: FormControl<string>;
  email: FormControl<string>;
  age: FormControl<number>;
  newsletter: FormControl<boolean>;
}

@Component({ ... })
export class RegistrationComponent {
  private readonly fb = inject(FormBuilder).nonNullable;

  readonly form: FormGroup<UserRegistrationForm> = this.fb.group({
    fullName: ['', [Validators.required, Validators.minLength(3)]],
    email: ['', [Validators.required, Validators.email]],
    age: [18, [Validators.required, Validators.min(18)]],
    newsletter: [false]
  });
}
```

### Stage 2: Synchronous, Asynchronous & Cross-Field Validation
Isolate validators into pure functions. Asynchronous validators querying remote APIs MUST debounce using `timer(300)` and `switchMap`:

```typescript
// Async Validator with debouncing
export function uniqueUsernameValidator(userService: UserService): AsyncValidatorFn {
  return (control: AbstractControl): Observable<ValidationErrors | null> => {
    if (!control.value || control.pristine) return of(null);
    return timer(300).pipe(
      switchMap(() => userService.checkUsername(control.value)),
      map(isAvailable => (isAvailable ? null : { usernameTaken: true })),
      catchError(() => of(null))
    );
  };
}
```

### Stage 3: Custom Form Controls via `ControlValueAccessor`
When authoring reusable inputs (e.g., datepicker, phone picker), implement `ControlValueAccessor`. Ensure `writeValue()` does NOT trigger `onChange()`, and call `cdr.markForCheck()` for Zoneless/OnPush updates:

```typescript
@Component({
  selector: 'app-phone-input',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [
    { provide: NG_VALUE_ACCESSOR, useExisting: forwardRef(() => PhoneInputComponent), multi: true }
  ],
  template: `...`
})
export class PhoneInputComponent implements ControlValueAccessor { ... }
```
*(Reference: [assets/custom-control-template.ts](assets/custom-control-template.ts))*

### Stage 4: Centralized Error Presentation
Never duplicate `@if (form.controls.field.errors && form.controls.field.touched)` in templates. Use the centralized `<app-form-error>` component:

```html
<div class="field-group">
  <label for="email">Email Address</label>
  <input id="email" type="email" formControlName="email" />
  <app-form-error [control]="form.controls.email" />
</div>
```
*(Reference: [assets/form-error-presenter.component.ts](assets/form-error-presenter.component.ts))*

### Stage 5: Signal Interop, Submission Lifecycle & Cleanup
Always use `markAllAsTouched()` to highlight invalid controls, guard against invalid submission, extract data via `getRawValue()` (so disabled controls are retained), and bind streams with `takeUntilDestroyed()`:

```typescript
onSubmit(): void {
  this.form.markAllAsTouched();
  if (this.form.invalid || this.isSubmitting()) return;

  this.isSubmitting.set(true);
  const payload = this.form.getRawValue();

  this.api.submit(payload)
    .pipe(takeUntilDestroyed(this.destroyRef))
    .subscribe({
      next: () => { this.isSubmitting.set(false); this.form.reset(); },
      error: () => { this.isSubmitting.set(false); }
    });
}
```

---

## 3. Automated Forms Audit Tool
Scan an entire Angular workspace or feature folder for untyped forms, template error spaghetti, and stream memory leaks:

```bash
python3 frameworks/angular/skills/angular-enterprise-forms/scripts/audit_angular_forms.py src/app
```

Add `--json` for machine-readable JSON pipeline outputs or `--strict` to fail builds on any detected violation.

---

## Gotchas & Anti-Patterns
- **`form.value` vs `form.getRawValue()`**: `form.value` strips all disabled controls from the output object. When submitting data to backend APIs, ALWAYS use `form.getRawValue()` so disabled control values are preserved.
- **CVA Infinite Update Loop**: Calling `this.onChange()` inside `writeValue()` creates an infinite ping-pong event loop between the parent form and child component. `writeValue()` must ONLY update internal component state.
- **Bare `.subscribe()` Memory Leaks**: Subscribing to `form.valueChanges` without `takeUntilDestroyed()` or `toSignal()` creates severe memory leaks because the form tree survives component destruction if referenced by parent scopes.
- **Untyped `FormGroup` Regression**: Using `new FormGroup({})` without generic parameters or using `UntypedFormGroup` silences TypeScript checks and leaks `any` across services.
- **Zoneless CVA Desynchronization**: In Zoneless Angular (`provideExperimentalZonelessChangeDetection()`), custom CVA components must explicitly invoke `cdr.markForCheck()` or mutate an internal `signal()` in `writeValue()` and `setDisabledState()`.
