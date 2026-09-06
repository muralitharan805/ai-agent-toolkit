import { Component, ChangeDetectionStrategy, inject, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';

/**
 * Standalone SSR-safe Privacy Policy component fulfilling Google AdSense Program Policies
 * and GDPR disclosure mandates regarding cookies, GA4 analytics, and DART cookie opt-outs.
 */
@Component({
  selector: 'app-privacy-policy',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  template: `
    <article class="legal-container">
      <header class="legal-header">
        <h1>Privacy Policy</h1>
        <p class="effective-date">Effective Date: August 16, 2026</p>
      </header>

      <section class="legal-section">
        <h2>1. Information We Collect</h2>
        <p>We respect your privacy. Minimal anonymized telemetry is collected via Google Analytics 4 (GA4) to analyze server-side rendering health and optimize client application performance.</p>
      </section>

      <section class="legal-section">
        <h2>2. Cookies & Google AdSense Advertising</h2>
        <p>This website uses Google AdSense to display advertisements. Google, as a third-party vendor, uses cookies to serve ads on our site.</p>
        <p>Google's use of advertising cookies enables it and its partners to serve ads based on user visits to this site and other locations across the Internet.</p>
        <p>Users may opt out of personalized advertising by visiting the <a href="https://www.google.com/settings/ads" target="_blank" rel="noopener noreferrer">Google Ads Settings</a> portal.</p>
      </section>

      <section class="legal-section">
        <h2>3. Server-Side Data Protection & Contact</h2>
        <p>No personally identifiable information (PII) is written to server logs or edge cache streams. If you have questions regarding data privacy, contact our engineering team via official repository channels.</p>
      </section>
    </article>
  `,
  styles: [`
    .legal-container {
      max-width: 800px;
      margin: 2rem auto;
      padding: 2rem;
      color: #e2e8f0;
      line-height: 1.7;
    }
    .legal-header {
      margin-bottom: 2rem;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      padding-bottom: 1rem;
    }
    .legal-header h1 {
      font-size: 2rem;
      font-weight: 700;
      color: #ffffff;
      margin: 0 0 0.5rem 0;
    }
    .effective-date {
      color: #94a3b8;
      font-size: 0.875rem;
      margin: 0;
    }
    .legal-section {
      margin-bottom: 2rem;
    }
    .legal-section h2 {
      font-size: 1.25rem;
      font-weight: 600;
      color: #94a3b8;
      margin: 0 0 0.75rem 0;
    }
    .legal-section p {
      color: #cbd5e1;
      font-size: 0.95rem;
      margin: 0 0 1rem 0;
    }
    .legal-section a {
      color: #60a5fa;
      text-decoration: underline;
      text-underline-offset: 3px;
    }
    .legal-section a:hover {
      color: #93c5fd;
    }
  `]
})
export class PrivacyPolicyComponent {
  private readonly platformId = inject(PLATFORM_ID);
  protected readonly isBrowser = isPlatformBrowser(this.platformId);
}
