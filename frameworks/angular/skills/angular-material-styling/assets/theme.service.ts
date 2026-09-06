import { Injectable, signal, effect, inject, DOCUMENT } from '@angular/core';

/**
 * Reactive Theme Service.
 * Controls application-wide light/dark theme state using Angular Signals,
 * enforces Dark Theme by default with OS preference fallback,
 * and synchronizes the root document element class with localStorage persistence.
 */
@Injectable({ providedIn: 'root' })
export class ThemeService {
  private readonly document = inject(DOCUMENT);
  private static readonly STORAGE_KEY = 'app-theme-preference';

  /** Signal holding true if Dark Mode is active, false if Light Mode. */
  readonly isDarkMode = signal<boolean>(this.getInitialThemePreference());

  constructor() {
    effect(() => {
      const dark = this.isDarkMode();
      const root = this.document.documentElement;
      root.classList.toggle('dark-theme', dark);
      root.classList.toggle('light-theme', !dark);
      try {
        localStorage.setItem(ThemeService.STORAGE_KEY, dark ? 'dark' : 'light');
      } catch {
        // Handle localStorage restrictions in private/sandboxed contexts
      }
    });
  }

  /**
   * Toggles the application theme between Dark and Light mode.
   */
  toggleTheme(): void {
    this.isDarkMode.update((previous: boolean) => !previous);
  }

  /**
   * Evaluates saved user preference first, falls back to OS system preference,
   * defaulting to true (Dark Theme).
   */
  private getInitialThemePreference(): boolean {
    try {
      const saved = localStorage.getItem(ThemeService.STORAGE_KEY);
      if (saved) {
        return saved === 'dark';
      }
    } catch {
      // Ignore storage access errors
    }

    if (typeof window !== 'undefined' && window.matchMedia) {
      if (window.matchMedia('(prefers-color-scheme: light)').matches) {
        return false;
      }
      if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return true;
      }
    }

    return true; // Default to Dark Theme
  }
}
