---
trigger: model_decision
description: "Enforces strict enterprise standards for Angular Reactive Forms (v19+) including mandatory Typed Forms, prohibition of untyped forms, centralized validation error presentation, ControlValueAccessor implementation, takeUntilDestroyed leak prevention, and structured submission lifecycles."
---
# Angular Enterprise Reactive Forms Rule

## Description
This rule enforces enterprise-grade architectural standards for Angular Reactive Forms (v19+). It mandates strictly typed reactive forms using `NonNullableFormBuilder` or explicit generic interfaces, centralized error presentation, standard `ControlValueAccessor` (CVA) interfaces for custom form controls, deterministic submission lifecycles, and memory leak prevention. It strictly forbids legacy untyped forms, inline template error boilerplate, un-unsubscribed form streams, and the usage of template-driven `[(ngModel)]` in complex domain workflows.

## Constraints

### 1. Mandatory Strictly Typed Reactive Forms
- All form instances MUST be declared using strictly typed reactive forms (`FormGroup<T>`, `FormControl<T>`, `FormArray<T>`, `FormRecord<T>`).
- Form initialization MUST prioritize `inject(FormBuilder).nonNullable` or `NonNullableFormBuilder` to guarantee non-nullable default value semantics on form reset.
- The use of legacy untyped form classes (`UntypedFormGroup`, `UntypedFormControl`, `UntypedFormArray`, `UntypedFormBuilder`) or explicit `any` generic parameters is STRICTLY FORBIDDEN.
- Form data models MUST be defined as dedicated TypeScript interfaces or type aliases before instantiating the form.

### 2. Prohibition of Inline Error Boilerplate in Templates
- Developers MUST NOT write repetitive, copy-pasted error checking logic in component templates (e.g. `@if (form.controls.email.errors && form.controls.email.touched)`).
- Error messages MUST be presented using a centralized error presenter component (e.g. `<app-form-error [control]="form.controls.email" />`) or a pure form error pipe.
- All form error messages MUST be resolved against a standardized error dictionary supporting domain-specific validation keys (`required`, `email`, `minlength`, `maxlength`, `pattern`, `custom`).

### 3. Reusable Custom Form Controls & ControlValueAccessor (CVA)
- Any custom UI input component intended for form integration (e.g. custom datepickers, multi-select tags, masked phone inputs, address blocks) MUST implement the Angular `ControlValueAccessor` interface.
- Custom form controls MUST provide `NG_VALUE_ACCESSOR` using `forwardRef` and configure `changeDetection: ChangeDetectionStrategy.OnPush`.
- The `writeValue(value: T)` method MUST gracefully handle null or undefined payloads without throwing runtime exceptions.
- The `setDisabledState(isDisabled: boolean)` method MUST reflect disabled state in the DOM and reactive state attributes (e.g. `aria-disabled`).

### 4. Memory Leak & Stream Teardown Protocol
- Subscriptions to form streams (`valueChanges`, `statusChanges`) MUST be protected against memory leaks using `takeUntilDestroyed(this.destroyRef)` or modern Angular Signal interop via `toSignal(form.valueChanges)`.
- Bare, unmanaged `.subscribe()` calls on form observables without explicit lifecycle teardown are STRICTLY FORBIDDEN.

### 5. Deterministic Submission Lifecycle & Data Extraction
- Form submission handlers MUST execute `form.markAllAsTouched()` before checking validation state to visually notify users of all invalid fields.
- Submissions MUST enforce an early guard clause: `if (this.form.invalid) { return; }`.
- When extracting form data for backend API payloads, developers MUST use `this.form.getRawValue()` rather than `this.form.value` to ensure disabled form controls are not stripped from the payload.
- Submit buttons MUST be disabled or display a spinner while async submission or asynchronous validation is pending.

### 6. Asynchronous Validation Debouncing
- Custom asynchronous validators (`AsyncValidatorFn`) communicating with backend services MUST incorporate debouncing (`timer(300)`) and switch-mapping (`switchMap`) to cancel pending HTTP requests and prevent server flooding.
- Asynchronous validators MUST NOT trigger on every keystroke without debouncing.

## Examples

- **Correct implementation:**
```typescript
// registration-form.component.ts
import { Component, ChangeDetectionStrategy, inject, DestroyRef } from '@angular/core';
import { FormBuilder, Validators, ReactiveFormsModule, FormControl, FormGroup } from '@angular/forms';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormErrorComponent } from '@shared/ui/form-error.component';
import { PhoneInputComponent } from '@shared/ui/phone-input.component';
import { UserService } from '@core/services/user.service';

export interface RegistrationFormModel {
  fullName: FormControl<string>;
  email: FormControl<string>;
  phone: FormControl<string>;
  acceptTerms: FormControl<boolean>;
}

@Component({
  selector: 'app-registration-form',
  standalone: true,
  imports: [ReactiveFormsModule, FormErrorComponent, PhoneInputComponent],
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <form [formGroup]="form" (ngSubmit)="onSubmit()" class="form-grid">
      <div class="field-group">
        <label for="fullName">Full Name</label>
        <input id="fullName" type="text" formControlName="fullName" />
        <app-form-error [control]="form.controls.fullName" />
      </div>

      <div class="field-group">
        <label for="email">Email Address</label>
        <input id="email" type="email" formControlName="email" />
        <app-form-error [control]="form.controls.email" />
      </div>

      <button type="submit" [disabled]="isSubmitting">Submit</button>
    </form>
  `
})
export class RegistrationFormComponent {
  private readonly fb = inject(FormBuilder).nonNullable;
  private readonly userService = inject(UserService);
  private readonly destroyRef = inject(DestroyRef);

  protected isSubmitting = false;

  readonly form: FormGroup<RegistrationFormModel> = this.fb.group({
    fullName: ['', [Validators.required, Validators.minLength(3)]],
    email: ['', [Validators.required, Validators.email]],
    phone: ['', [Validators.required]],
    acceptTerms: [false, [Validators.requiredTrue]]
  });

  constructor() {
    this.form.valueChanges
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe(() => { /* Safe reactive stream */ });
  }

  onSubmit(): void {
    this.form.markAllAsTouched();
    if (this.form.invalid || this.isSubmitting) return;

    this.isSubmitting = true;
    this.userService.register(this.form.getRawValue())
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe({
        next: () => { this.isSubmitting = false; this.form.reset(); },
        error: () => { this.isSubmitting = false; }
      });
  }
}
```

- **Incorrect implementation (FORBIDDEN):**
```typescript
// Anti-pattern: Untyped forms, unmanaged subscriptions, and template error spaghetti
import { Component } from '@angular/core';
import { FormControl } from '@angular/forms';

@Component({
  selector: 'app-bad-form',
  template: `
    <!-- FORBIDDEN: Verbose copy-pasted error checking logic in template -->
    <input [formControl]="email" />
    <span *ngIf="email.errors && email.touched">Email is required!</span>
  `
})
export class BadFormComponent {
  // FORBIDDEN: Untyped form control without non-nullable configuration
  email: any = new FormControl('');

  ngOnInit() {
    // FORBIDDEN: Memory leak hazard! Bare subscribe without takeUntilDestroyed
    this.email.valueChanges.subscribe((val: any) => console.log(val));
  }

  submit() {
    // FORBIDDEN: Fails to mark fields as touched, uses raw .value which drops disabled controls
    const data = { email: this.email.value };
  }
}
```
