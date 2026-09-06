import { Component, ChangeDetectionStrategy } from '@angular/core';

/**
 * Standalone Privacy Policy component fulfilling Google AdSense Program Policies
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
        <p>We respect your privacy. We collect minimal, anonymized telemetry via Google Analytics 4 (GA4) to analyze site performance, diagnose navigation errors, and enhance user experience.</p>
      </section>

      <section class="legal-section">
        <h2>2. Cookies & Google AdSense Advertising</h2>
        <p>This website uses Google AdSense to serve advertisements. Google, as a third-party vendor, uses cookies to serve ads on our site.</p>
        <p>Google's use of advertising cookies enables it and its partners to serve ads to users based on their visits to our site and other destinations across the Internet.</p>
        <p>Users may opt out of personalized advertising by visiting the <a href="https://www.google.com/settings/ads" target="_blank" rel="noopener noreferrer">Google Ads Settings</a> page.</p>
      </section>

      <section class="legal-section">
        <h2>3. Third-Party Analytics & Tracking</h2>
        <p>Analytics events are collected without storing sensitive personally identifiable information (PII) such as passwords, payment cards, or authentication tokens.</p>
      </section>

      <section class="legal-section">
        <h2>4. Data Protection & Contact</h2>
        <p>If you have any questions or concerns regarding this Privacy Policy, you may contact our engineering team via our official project support channels.</p>
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
export class PrivacyPolicyComponent {}
