# Enterprise Form Validation & Centralized Error Architecture

## 1. Overview
In enterprise Angular applications, form validation logic must be pure, testable, and isolated from UI components. Error display must be centralized to avoid duplicating verbose `@if (form.controls.field.errors && form.controls.field.touched)` blocks across dozens of templates.

---

## 2. Synchronous Validation Patterns

### 2.1 Pure Custom Validator Functions
Custom validators MUST return a `ValidationErrors` object if invalid, or `null` if valid:

```typescript
import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

/**
 * Validates that a string does not contain leading or trailing whitespace.
 */
export function noWhitespaceValidator(): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    if (!control.value) {
      return null; // Let 'required' validator handle empty values
    }
    const isWhitespace = (control.value || '').trim().length === 0;
    const hasLeadingOrTrailing = control.value.trim() !== control.value;
    return isWhitespace || hasLeadingOrTrailing ? { whitespace: true } : null;
  };
}

/**
 * Validates tax identification numbers according to format.
 */
export function taxIdValidator(region: 'IN' | 'US'): ValidatorFn {
  const PATTERNS: Record<'IN' | 'US', RegExp> = {
    IN: /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/, // PAN format
    US: /^\d{3}-\d{2}-\d{4}$/          // SSN format
  };

  return (control: AbstractControl): ValidationErrors | null => {
    if (!control.value) return null;
    const valid = PATTERNS[region].test(control.value);
    return valid ? null : { invalidTaxId: { requiredFormat: region, actual: control.value } };
  };
}
```

### 2.2 Cross-Field Group Validation
Cross-field validations (such as password confirmation or start/end date logic) MUST be attached to the `FormGroup`, not individual controls:

```typescript
import { AbstractControl, ValidationErrors, ValidatorFn } from '@angular/forms';

/**
 * Validates that two fields match (e.g. password and confirmPassword).
 */
export function matchFieldsValidator(sourceField: string, targetField: string): ValidatorFn {
  return (control: AbstractControl): ValidationErrors | null => {
    const sourceCtrl = control.get(sourceField);
    const targetCtrl = control.get(targetField);

    if (!sourceCtrl || !targetCtrl) {
      return null;
    }

    if (targetCtrl.errors && !targetCtrl.errors['fieldsMismatch']) {
      return null; // Preserve other validation errors
    }

    if (sourceCtrl.value !== targetCtrl.value) {
      targetCtrl.setErrors({ fieldsMismatch: true });
      return { fieldsMismatch: true };
    } else {
      targetCtrl.setErrors(null);
      return null;
    }
  };
}
```

---

## 3. Asynchronous Validation with Debounce & Cancellation

Directly querying an API on every keystroke causes race conditions and floods backend services. Async validators MUST debounce input and cancel stale HTTP requests using `timer` and `switchMap`:

```typescript
import { inject, Injectable } from '@angular/core';
import { AbstractControl, AsyncValidatorFn, ValidationErrors } from '@angular/forms';
import { Observable, of, timer } from 'rxjs';
import { map, switchMap, catchError } from 'rxjs/operators';
import { UserService } from '@core/services/user.service';

@Injectable({ providedIn: 'root' })
export class UniqueEmailValidator {
  private readonly userService = inject(UserService);

  /**
   * Returns an AsyncValidatorFn that checks email uniqueness with 300ms debounce.
   */
  validate(excludeUserId?: string): AsyncValidatorFn {
    return (control: AbstractControl): Observable<ValidationErrors | null> => {
      const email = control.value;
      if (!email || control.pristine) {
        return of(null);
      }

      return timer(300).pipe(
        switchMap(() => this.userService.checkEmailAvailability(email, excludeUserId)),
        map((isAvailable) => (isAvailable ? null : { emailTaken: { email } })),
        catchError(() => of(null)) // Degrade gracefully on network failure
      );
    };
  }
}
```

Attach to control using the third argument:
```typescript
email: ['', {
  validators: [Validators.required, Validators.email],
  asyncValidators: [this.emailValidator.validate()]
}]
```

---

## 4. Centralized Error Message Dictionary

Instead of hardcoding error strings in every HTML file, define a centralized resolver:

```typescript
export interface ValidationErrorDetails {
  readonly requiredLength?: number;
  readonly actualLength?: number;
  readonly min?: number;
  readonly max?: number;
  readonly [key: string]: unknown;
}

export const FORM_ERROR_MESSAGES: Record<string, (details: ValidationErrorDetails) => string> = {
  required: () => 'This field is required.',
  email: () => 'Please enter a valid email address.',
  minlength: (d) => `Minimum length is ${d.requiredLength} characters (current: ${d.actualLength}).`,
  maxlength: (d) => `Maximum length is ${d.requiredLength} characters (current: ${d.actualLength}).`,
  pattern: () => 'Input does not match the required pattern.',
  fieldsMismatch: () => 'The fields do not match.',
  emailTaken: (d) => `The email '${d['email']}' is already in use.`
};

export function resolveFormErrorMessage(
  errors: Record<string, ValidationErrorDetails> | null | undefined,
  customOverrides?: Record<string, string>
): string | null {
  if (!errors) return null;
  const keys = Object.keys(errors);
  if (keys.length === 0) return null;

  const firstKey = keys[0];
  if (customOverrides && customOverrides[firstKey]) {
    return customOverrides[firstKey];
  }

  const resolver = FORM_ERROR_MESSAGES[firstKey];
  return resolver ? resolver(errors[firstKey]) : 'Field input is invalid.';
}
```
