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

/**
 * Enterprise boilerplate template for a standalone Angular custom form control
 * implementing the ControlValueAccessor (CVA) interface.
 *
 * @description Supports Angular 19+ standalone architecture, OnPush change detection,
 * signal inputs, disabled state propagation, and full type safety.
 */
@Component({
  selector: 'app-custom-text-input',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  providers: [
    {
      provide: NG_VALUE_ACCESSOR,
      useExisting: forwardRef(() => CustomTextInputComponent),
      multi: true
    }
  ],
  template: `
    <div class="custom-control-wrapper" [class.is-disabled]="isDisabled()">
      @if (label()) {
        <label [attr.for]="controlId()" class="control-label">{{ label() }}</label>
      }
      <div class="input-container">
        <input
          [id]="controlId()"
          type="text"
          [value]="value()"
          [placeholder]="placeholder()"
          [disabled]="isDisabled()"
          (input)="handleInput($event)"
          (blur)="handleBlur()"
          class="native-input"
        />
      </div>
    </div>
  `,
  styles: [`
    .custom-control-wrapper {
      display: flex;
      flex-direction: column;
      gap: 0.375rem;
    }
    .control-label {
      font-size: 0.875rem;
      font-weight: 500;
      color: var(--text-primary, #1e293b);
    }
    .input-container {
      position: relative;
    }
    .native-input {
      width: 100%;
      padding: 0.625rem 0.875rem;
      border: 1px solid var(--border-color, #cbd5e1);
      border-radius: 0.375rem;
      font-size: 0.875rem;
      transition: border-color 0.2s, box-shadow 0.2s;
    }
    .native-input:focus {
      outline: none;
      border-color: var(--primary-color, #3b82f6);
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
    }
    .is-disabled {
      opacity: 0.6;
      pointer-events: none;
    }
  `]
})
export class CustomTextInputComponent implements ControlValueAccessor {
  private readonly cdr = inject(ChangeDetectorRef);

  /** Public signal inputs */
  readonly label = input<string>('');
  readonly placeholder = input<string>('');
  readonly controlId = input<string>(`custom-input-${Math.random().toString(36).substring(2, 9)}`);

  /** Reactive internal state signals */
  readonly value = signal<string>('');
  readonly isDisabled = signal<boolean>(false);

  /** CVA Callback functions */
  private onChange: (value: string) => void = () => {};
  private onTouched: () => void = () => {};

  /**
   * Writes a new value from the Angular form model into the component view.
   * @param incomingValue The incoming value from the form control.
   */
  writeValue(incomingValue: string | null | undefined): void {
    const sanitizedValue = incomingValue ?? '';
    this.value.set(sanitizedValue);
    this.cdr.markForCheck();
  }

  /**
   * Registers a callback function that should be called when the control's value changes in the UI.
   * @param fn The callback function provided by Angular Forms.
   */
  registerOnChange(fn: (value: string) => void): void {
    this.onChange = fn;
  }

  /**
   * Registers a callback function that should be called when the control receives a touch event.
   * @param fn The callback function provided by Angular Forms.
   */
  registerOnTouched(fn: () => void): void {
    this.onTouched = fn;
  }

  /**
   * Updates the disabled state of the component when toggled via the form control API.
   * @param isControlDisabled Whether the control is currently disabled.
   */
  setDisabledState(isControlDisabled: boolean): void {
    this.isDisabled.set(isControlDisabled);
    this.cdr.markForCheck();
  }

  /**
   * Handles native DOM input events and propagates changes to the form model.
   * @param event Native DOM Event.
   */
  protected handleInput(event: Event): void {
    const target = event.target as HTMLInputElement | null;
    const newValue = target?.value ?? '';
    this.value.set(newValue);
    this.onChange(newValue);
  }

  /**
   * Handles native DOM blur events and propagates touch status to the form model.
   */
  protected handleBlur(): void {
    this.onTouched();
  }
}
