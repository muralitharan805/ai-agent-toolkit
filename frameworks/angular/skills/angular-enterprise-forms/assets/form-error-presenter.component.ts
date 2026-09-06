import {
  Component,
  ChangeDetectionStrategy,
  input,
  computed
} from '@angular/core';
import { AbstractControl } from '@angular/forms';

/**
 * Standard enterprise error message lookup dictionary.
 */
const DEFAULT_ERROR_MESSAGES: Readonly<Record<string, (errorDetails: unknown) => string>> = {
  required: () => 'This field is required.',
  email: () => 'Please enter a valid email address.',
  minlength: (details) => {
    const info = details as { requiredLength?: number; actualLength?: number };
    return `Minimum length is ${info.requiredLength ?? 'unknown'} characters.`;
  },
  maxlength: (details) => {
    const info = details as { requiredLength?: number; actualLength?: number };
    return `Maximum length is ${info.requiredLength ?? 'unknown'} characters.`;
  },
  pattern: () => 'Input does not match the required format.',
  min: (details) => {
    const info = details as { min?: number; actual?: number };
    return `Value must be at least ${info.min ?? 'unknown'}.`;
  },
  max: (details) => {
    const info = details as { max?: number; actual?: number };
    return `Value must not exceed ${info.max ?? 'unknown'}.`;
  }
};

/**
 * Reusable, accessible standalone error message presenter component.
 *
 * @description Eliminates verbose inline template checks and guarantees
 * unified error formatting and accessibility across the application.
 */
@Component({
  selector: 'app-form-error',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    @if (errorMessage(); as message) {
      <p class="form-error-message" role="alert" aria-live="polite">
        <svg
          class="error-icon"
          viewBox="0 0 20 20"
          fill="currentColor"
          aria-hidden="true"
        >
          <path
            fill-rule="evenodd"
            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-8-5a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5A.75.75 0 0110 5zm0 10a1 1 0 100-2 1 1 0 000 2z"
            clip-rule="evenodd"
          />
        </svg>
        <span>{{ message }}</span>
      </p>
    }
  `,
  styles: [`
    .form-error-message {
      display: flex;
      align-items: center;
      gap: 0.375rem;
      margin: 0.25rem 0 0;
      font-size: 0.75rem;
      color: var(--color-error, #dc2626);
      line-height: 1.25;
    }
    .error-icon {
      width: 0.875rem;
      height: 0.875rem;
      flex-shrink: 0;
    }
  `]
})
export class FormErrorComponent {
  /** The target form control instance */
  readonly control = input.required<AbstractControl | null>();

  /** Optional custom error message overrides */
  readonly customMessages = input<Record<string, string>>({});

  /**
   * Evaluates the active validation error and returns the resolved human-readable message.
   */
  readonly errorMessage = computed<string | null>(() => {
    const ctrl = this.control();
    if (!ctrl || !ctrl.errors || (!ctrl.touched && !ctrl.dirty)) {
      return null;
    }

    const errorKeys = Object.keys(ctrl.errors);
    if (errorKeys.length === 0) {
      return null;
    }

    const firstKey = errorKeys[0];
    const overrides = this.customMessages();

    if (overrides[firstKey]) {
      return overrides[firstKey];
    }

    const defaultResolver = DEFAULT_ERROR_MESSAGES[firstKey];
    if (defaultResolver) {
      return defaultResolver(ctrl.errors[firstKey]);
    }

    // Support custom validator error string payloads
    const rawError = ctrl.errors[firstKey];
    if (typeof rawError === 'string') {
      return rawError;
    }

    return 'Field input is invalid.';
  });
}
