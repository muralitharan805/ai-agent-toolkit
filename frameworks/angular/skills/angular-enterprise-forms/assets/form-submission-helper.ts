import { AbstractControl, FormGroup } from '@angular/forms';

/**
 * Recursively marks all controls, sub-groups, and arrays in a form tree as touched.
 *
 * @param control The root AbstractControl or FormGroup instance.
 */
export function markAllFormControlsAsTouched(control: AbstractControl): void {
  control.markAsTouched({ onlySelf: true });

  if (control instanceof FormGroup) {
    const controls = control.controls;
    for (const key of Object.keys(controls)) {
      markAllFormControlsAsTouched(controls[key]);
    }
  } else if ('controls' in control && Array.isArray((control as unknown as { controls: AbstractControl[] }).controls)) {
    const formArray = control as unknown as { controls: AbstractControl[] };
    for (const subControl of formArray.controls) {
      markAllFormControlsAsTouched(subControl);
    }
  }
}

/**
 * Searches the DOM for the first invalid input element within a form container and smoothly scrolls it into view.
 *
 * @param formContainerElement The root native HTMLFormElement or container element.
 * @param focusElement Whether to automatically focus the invalid element after scrolling.
 */
export function scrollToFirstInvalidControl(
  formContainerElement: HTMLElement,
  focusElement: boolean = true
): void {
  // Query for common Angular invalid form control CSS selectors
  const invalidElement = formContainerElement.querySelector<HTMLElement>(
    '.ng-invalid:not(form):not(div):not([formGroupName]), [aria-invalid="true"]'
  );

  if (!invalidElement) {
    return;
  }

  invalidElement.scrollIntoView({
    behavior: 'smooth',
    block: 'center'
  });

  if (focusElement && typeof invalidElement.focus === 'function') {
    invalidElement.focus({ preventScroll: true });
  }
}

/**
 * Extracts a complete, strongly-typed data payload from a Reactive FormGroup using getRawValue().
 * Guarantees that disabled fields are included in the serialized output.
 *
 * @param form Strongly typed Angular FormGroup.
 * @returns Complete typed value object.
 */
export function extractFormRawPayload<T>(form: FormGroup): T {
  return form.getRawValue() as T;
}
