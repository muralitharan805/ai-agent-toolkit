# Strictly Typed Reactive Forms & ControlValueAccessor (CVA) Architecture

## 1. Strictly Typed Reactive Forms Overview

Modern Angular provides comprehensive type safety for the Reactive Forms API. All form controls track the exact TypeScript types of their values throughout their lifecycle, eliminating runtime surprises and invalid payload structures.

### 1.1 Form Primitives & Generic Interfaces

Enterprise applications MUST define explicit interfaces representing the control structure:

```typescript
import { FormControl, FormGroup, FormArray, FormRecord } from '@angular/forms';

/**
 * Domain model interface representing the business object.
 */
export interface UserAddress {
  readonly street: string;
  readonly city: string;
  readonly postalCode: string;
  readonly isPrimary: boolean;
}

/**
 * Form model interface mapping each property to a strongly typed FormControl.
 */
export interface AddressFormModel {
  street: FormControl<string>;
  city: FormControl<string>;
  postalCode: FormControl<string>;
  isPrimary: FormControl<boolean>;
}

/**
 * User Profile Form model demonstrating nested groups and arrays.
 */
export interface UserProfileFormModel {
  fullName: FormControl<string>;
  email: FormControl<string>;
  primaryAddress: FormGroup<AddressFormModel>;
  additionalAddresses: FormArray<FormGroup<AddressFormModel>>;
  preferences: FormRecord<FormControl<boolean>>;
}
```

### 1.2 NonNullableFormBuilder & Default Reset Semantics

In standard `FormGroup`, invoking `.reset()` resets all controls to `null`. This forces types to become `T | null`. To guarantee non-nullable semantics, use `NonNullableFormBuilder` (available via `inject(FormBuilder).nonNullable`):

```typescript
import { Component, inject } from '@angular/core';
import { FormBuilder, Validators, FormGroup } from '@angular/forms';

@Component({ ... })
export class ProfileFormComponent {
  private readonly fb = inject(FormBuilder).nonNullable;

  readonly form: FormGroup<UserProfileFormModel> = this.fb.group({
    fullName: ['', [Validators.required, Validators.minLength(2)]],
    email: ['', [Validators.required, Validators.email]],
    primaryAddress: this.fb.group({
      street: ['', Validators.required],
      city: ['', Validators.required],
      postalCode: ['', [Validators.required, Validators.pattern(/^\d{5,6}$/)]],
      isPrimary: [true]
    }),
    additionalAddresses: this.fb.array<FormGroup<AddressFormModel>>([]),
    preferences: this.fb.record<FormControl<boolean>>({})
  });
}
```

When `this.form.reset()` is invoked, controls reset to their initial non-nullable string/boolean values rather than `null`.

---

## 2. ControlValueAccessor (CVA) Specification

The `ControlValueAccessor` interface acts as the bridge between the Angular Forms API and custom DOM elements or reusable input components.

### 2.1 CVA Architecture Contract

Any custom input component intended for use with `formControlName` or `[formControl]` MUST fulfill:
1. Provide `NG_VALUE_ACCESSOR` in the component `providers` array using `forwardRef`.
2. Implement the 4 interface methods: `writeValue`, `registerOnChange`, `registerOnTouched`, and `setDisabledState`.
3. Support OnPush change detection without dropping change events.
4. Support ARIA accessibility attributes (`aria-invalid`, `aria-describedby`, `aria-disabled`).

### 2.2 Complete Production-Grade CVA Implementation

Here is a resilient, type-safe Currency/Money Input component:

```typescript
import {
  Component,
  ChangeDetectionStrategy,
  forwardRef,
  input,
  signal,
  inject,
  ChangeDetectorRef
} from '@angular/core';
import { ControlValueAccessor, NG_VALUE_ACCESSOR } from '@angular/forms';

export interface CurrencyAmount {
  readonly amount: number;
  readonly currency: string;
}

@Component({
  selector: 'app-currency-input',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => CurrencyInputComponent),
      multi: true
    }
  ],
  template: `
    <div class="currency-field" [class.is-disabled]="isDisabled()">
      <span class="currency-symbol">{{ currencyCode() }}</span>
      <input
        type="number"
        step="0.01"
        [value]="amount()"
        [disabled]="isDisabled()"
        (input)="onAmountInput($event)"
        (blur)="onBlur()"
        class="amount-input"
        placeholder="0.00"
      />
    </div>
  `,
  styles: [`
    .currency-field {
      display: inline-flex;
      align-items: center;
      border: 1px solid #cbd5e1;
      border-radius: 0.375rem;
      padding: 0.25rem 0.5rem;
    }
    .currency-symbol {
      font-weight: 600;
      color: #64748b;
      margin-right: 0.375rem;
    }
    .amount-input {
      border: none;
      outline: none;
      width: 100%;
      font-size: 0.875rem;
    }
    .is-disabled {
      background-color: #f1f5f9;
      opacity: 0.6;
    }
  `]
})
export class CurrencyInputComponent implements ControlValueAccessor {
  private readonly cdr = inject(ChangeDetectorRef);

  readonly currencyCode = input<string>('USD');

  readonly amount = signal<number>(0);
  readonly isDisabled = signal<boolean>(false);

  private onChange: (value: CurrencyAmount) => void = () => {};
  private onTouched: () => void = () => {};

  writeValue(incomingValue: CurrencyAmount | null | undefined): void {
    if (incomingValue && typeof incomingValue.amount === 'number') {
      this.amount.set(incomingValue.amount);
    } else {
      this.amount.set(0);
    }
    this.cdr.markForCheck();
  }

  registerOnChange(fn: (value: CurrencyAmount) => void): void {
    this.onChange = fn;
  }

  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  setDisabledState(isControlDisabled: boolean): void {
    this.isDisabled.set(isControlDisabled);
    this.cdr.markForCheck();
  }

  protected onAmountInput(event: Event): void {
    const target = event.target as HTMLInputElement;
    const parsed = parseFloat(target.value) || 0;
    this.amount.set(parsed);
    this.onChange({
      amount: parsed,
      currency: this.currencyCode()
    });
  }

  protected onBlur(): void {
    this.onTouched();
  }
}
```

### 2.3 Key Considerations for CVA in Zoneless Angular
- In zoneless mode (`provideExperimentalZonelessChangeDetection()`), DOM events inside the component will trigger change detection, but programmatic updates via `writeValue()` or `setDisabledState()` MUST call `cdr.markForCheck()` or update a `signal()` to trigger dirty checking.
- Do NOT invoke `this.onChange()` inside `writeValue()`. `writeValue()` should strictly update internal view state without notifying the parent form model, avoiding infinite update loops.
