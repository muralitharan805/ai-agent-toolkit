import { Injectable, inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { Router, NavigationEnd } from '@angular/router';
import { filter } from 'rxjs/operators';

/**
 * Valid GA4 primitive and object parameter values.
 */
export type GtagParamValue = string | number | boolean | null | undefined | readonly string[] | Record<string, unknown>;

/**
 * Window extension interface for GA4 gtag.js dataLayer runtime.
 */
declare global {
  interface Window {
    gtag?: (command: string, actionOrTarget: string, params?: Record<string, GtagParamValue>) => void;
    dataLayer?: unknown[];
  }
}

/**
 * Service orchestrating Google Analytics 4 (GA4) event and page view tracking
 * across Single Page Application client-side navigation transitions.
 */
@Injectable({ providedIn: 'root' })
export class AnalyticsService {
  private readonly router = inject(Router);
  private readonly platformId = inject(PLATFORM_ID);

  /**
   * Initializes GA4 page_view tracking on client-side router navigation events.
   *
   * @param measurementId - The GA4 Web Stream Measurement ID (e.g. 'G-XXXXXXXXXX')
   */
  init(measurementId: string): void {
    if (!isPlatformBrowser(this.platformId)) {
      return;
    }

    this.router.events
      .pipe(filter((event): event is NavigationEnd => event instanceof NavigationEnd))
      .subscribe((event: NavigationEnd) => {
        if (typeof window.gtag === 'function') {
          window.gtag('config', measurementId, {
            page_path: event.urlAfterRedirects,
          });
        }
      });
  }

  /**
   * Tracks a custom analytics event with sanitized, typed metadata.
   *
   * @param eventName - Identifier for the custom event (e.g. 'cta_clicked', 'export_generated')
   * @param params - Optional structured event properties (free of PII)
   */
  trackEvent(eventName: string, params: Record<string, GtagParamValue> = {}): void {
    if (isPlatformBrowser(this.platformId) && typeof window.gtag === 'function') {
      window.gtag('event', eventName, params);
    }
  }
}
